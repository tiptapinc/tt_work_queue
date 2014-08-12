#!/usr/bin/env python
# encoding: utf-8
"""
Copyright (c) 2014 tiptap. All rights reserved.

"""
import beanstalkt

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
