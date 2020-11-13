from setuptools import setup

setup(
    name='tt_work_queue',
    description='TipTap work queue library.',
    long_description=(
        '%s\n\n%s' % (
            open('README.md').read(),
            open('CHANGELOG.md').read()
        )
    ),
    version=open('VERSION').read().strip(),
    author='TipTap',
    install_requires=[
        'tornado',
        'PyYAML',
        'beanstalkt==0.6.0'
    ],
    packages=['tt_work_queue']
)
