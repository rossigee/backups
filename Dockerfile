FROM alpine:latest

# Install main O/S applications required
RUN apk add --no-cache \
    curl git sudo vim \
    python3 py3-pip \
    py3-cryptography \
    openssh-client \
    mariadb-client \
    postgresql-client postgresql \
    samba-client \
    gnupg \
    zip unzip

# Install main python packages required
RUN pip3 install --break-system-packages \
    boto3 \
    awscli \
    azure-identity \
    azure-mgmt-compute \
    prometheus_client \
    elasticsearch \
    b2sdk \
    minio \
    dropbox \
    google-api-python-client \
    google-auth

COPY . /tmp/backups
RUN pip3 install --break-system-packages build && \
  cd /tmp/backups && \
  python3 -m build && \
  pip3 install --break-system-packages dist/backups-*.tar.gz
