#!/usr/bin/env python
# encoding: utf-8
"""
Copyright (c) 2014 tiptap. All rights reserved.

"""
import beanstalkt
import statsd
import tornado.ioloop
import tt_utils

import logging
log = logging.getLogger(__name__)


class TTWorkQueue(beanstalkt.Client):
    """
    Adds initialize and get_status methods to the beanstalkt client
    """
    def initialize(self, tubeName, on_status_change=None, on_reconnect=None):
        self._init_status(on_status_change)
        self.connect(callback=self._connect_callback)
        self.use(tubeName, callback=self._use_callback)
        self.watch(tubeName, callback=self._watch_callback)
        self.ignore("default")
        if on_reconnect:
            self.set_reconnect_callback(on_reconnect)

    def get_status(self):
        return self.useSet and self.watchSet and self.connected

    def _use_callback(self, resp):
        if isinstance(resp, Exception):
            log.warning("queue error: %s" % str(resp))
        else:
            self.useSet = True

        self._update_status()

    def _watch_callback(self, resp):
        if isinstance(resp, Exception):
            log.warning("queue error: %s" % str(resp))
        else:
            self.watchSet = True

        self._update_status()

    def _connect_callback(self):
        self.connected = True
        self._update_status()

    def _init_status(self, on_status_change):
        self.on_status_change = on_status_change
        self.useSet = False
        self.watchSet = False
        self.connected = False
        self.ready = False

    def _update_status(self):
        ready = self.get_status()
        if self.ready != ready:
            self.ready = ready
            if self.on_status_change:
                self.on_status_change(self.ready)


class BaseHandler(object):
    """
    base class for a consumer/producer of a TTWorkQueue.

    """
    STATSD = statsd.StatsClient('localhost', 8125)

    def __init__(self, queueName):
        self.queueName = queueName

        ports = tt_utils.load_config("/opt/tiptap/configs/ports.yml")
        host = "localhost"
        port = ports['servicePorts']['beanstalkd']

        self.queue = TTWorkQueue(host=host, port=port)
        self.queue.initialize(
            self.queueName,
            on_reconnect=self._on_reconnect
        )

        self.consuming = False

    def _on_reconnect(self, *args):
        log.info("reconnected to \'%s\' beanstalkd tube" % self.queueName)
        if self.consuming:
            self.queue.reserve(callback=self._process_queue_job)

    def _consume(self):
        self.consuming = True
        self.queue.reserve(callback=self._process_queue_job)

    def _reconsume(self, reconsumeTime):
        tornado.ioloop.IOLoop.instance().add_timeout(
            reconsumeTime,
            self._consume
        )

    def put(self, jsonJob, **kwargs):
        self.queue.put(jsonJob, callback=self._put_callback, **kwargs)

    def _put_callback(self, resp):
        if isinstance(resp, Exception):
            log.warning("queue error: %s" % str(resp))


PROCESSING = False


class PollHandler(BaseHandler):
    """
    handler that polls queue instead of blocking on reserve.

    _process_queue_job method must handle a beanstalkt.TimedOut
    exception by reconsuming after some interval

    there can be multiple handlers in a single python process but
    there should only be on reserved job / process at any time, so
    this handler uses a global 'processing' flag

    """
    STATSD = statsd.StatsClient('localhost', 8125)

    def _on_reconnect(self, *args):
        log.info("reconnected to \'%s\' beanstalkd tube" % self.queueName)
        if self.consuming and not PROCESSING:
            self.queue.reserve(timeout=0, callback=self._process_queue_job)

    def _consume(self):
        self.consuming = True
        if not PROCESSING:
            self.queue.reserve(timeout=0, callback=self._process_queue_job)

    def _processing(self):
        global PROCESSING

        PROCESSING = True

    def _not_processing(self):
        global PROCESSING

        PROCESSING = False
