from setuptools import setup

setup(name = 'backups',
    version = '2.7.0',
    description = 'Backup orchestration tool for databases, folders and cloud snapshots',
    long_description = (
        'A Python backup orchestration tool that cycles through sources '
        '(databases, folders, cloud snapshots), compresses and optionally '
        'encrypts each backup, uploads to one or more destinations (S3, GCS, '
        'B2, Dropbox, local, and more), and reports results via notifications '
        '(email, Slack, Discord, Telegram, Prometheus, and more). '
        'Supports OpenTelemetry OTLP tracing for observability.'
    ),
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
        'python-dateutil',
        'paramiko',
    ],
    extras_require = {
        'tracing': [
            'opentelemetry-api',
            'opentelemetry-sdk',
            'opentelemetry-exporter-otlp-proto-grpc',
            'grpcio>=1.80.0',
        ]
    },
    entry_points = {
        'console_scripts': [
            'backup = backups.main:main'
        ]
    }
)
