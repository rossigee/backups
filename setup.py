from setuptools import setup

setup(name = 'backups',
    version = '2.3.1',
    description = 'Data Backup Scripts',
    author = 'Ross Golder',
    author_email = 'ross@golder.org',
    url = 'https://github.com/rossigee/backups',
    packages = [
        'backups',
        'backups.sources',
        'backups.destinations',
        'backups.notifications'
    ],
    install_requires = [
        'requests',
        'python-dateutil'
    ],
    entry_points = {
        'console_scripts': [
            'backup = backups.main:main'
        ]
    }
)
