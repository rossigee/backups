FROM alpine:latest

# Install main O/S applications required
RUN apk add --no-cache \
    curl git sudo vim \
    python3 py3-pip \
    openssh-client \
    mariadb-client \
    postgresql-client postgresql \
    gnupg \
    zip unzip

# Install main python packages required
RUN pip3 install \
    git+https://github.com/rossigee/backups@master \
    awscli \
    boto3 \
    prometheus_client

