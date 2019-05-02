FROM alpine:latest

# Install main O/S applications required
RUN apk add --no-cache \
    curl git rsync vim sudo \
    python3 py3-pip \
    mariadb-client \
    postgresql-client postgresql \
    gnupg \
    zip unzip \
    supervisor

# Install Jobber app binary for scheduling
RUN curl -sLO https://github.com/dshearer/jobber/releases/download/v1.3.2/jobber-1.3.2-r0_alpine3.6and3.7.apk && \
    apk add --allow-untrusted jobber-1.3.2-r0_alpine3.6and3.7.apk; \
    rm -f jobber-1.3.2-r0_alpine3.6and3.7.apk

# Install main python packages required
RUN pip3 install \
    git+https://github.com/rossigee/backups \
    awscli \
    boto3 \
    prometheus_client

# Set up our custom notification handler
#ADD /notify-webhook.sh /notify-webhook.sh
#RUN chmod 755 /notify-webhook.sh

# Run the scheduler
CMD ["/usr/libexec/jobbermaster"]
