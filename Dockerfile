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
RUN pip3 install \
    boto3 \
    awscli \
    adal \
    azure-mgmt-compute \
    prometheus_client \
    elasticsearch==7.7.0

COPY . /tmp/backups
RUN cd /tmp/backups && \
  python3 setup.py sdist && \
  pip3 install dist/backups-2.3.4.tar.gz
