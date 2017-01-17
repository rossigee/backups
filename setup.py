from setuptools import setup

setup(name = 'backups',
    version = '1.2.0',
    description = 'Data Backup Scripts',
    author = 'Ross Golder',
    author_email = 'ross@golder.org',
    url = 'http://www.golder.org/',
    packages = ['backups'],
    entry_points = {
        'console_scripts': [
            'backup = backups.main:main'
        ]
    }
)

