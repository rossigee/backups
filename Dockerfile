FROM alpine:latest

# Install main O/S applications required
RUN apk add --no-cache \
    curl git sudo vim \
    python3 py3-pip \
    py3-cryptography \
    openssh-client \
    mariadb-client \
    postgresql-client postgresql \
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

COPY dist/backups-2.3.0.tar.gz /tmp
RUN pip3 install /tmp/backups-2.3.0.tar.gz
