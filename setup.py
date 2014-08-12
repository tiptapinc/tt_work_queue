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
    install_requires=['tornado', 'beanstalkt', 'PyYAML'],
    package_dir={'tt_work_queue': 'src'},
    packages=['tt_work_queue']
)
