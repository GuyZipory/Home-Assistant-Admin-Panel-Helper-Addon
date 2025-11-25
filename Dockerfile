ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && pip3 install --no-cache-dir --break-system-packages \
    flask==3.0.0 \
    requests==2.31.0 \
    pyjwt==2.8.0

# Copy application files
WORKDIR /app
COPY app.py /app/
COPY requirements.txt /app/

# Copy S6 service scripts
COPY rootfs /

# Set executable permissions
RUN chmod a+x /app/app.py \
    && chmod a+x /etc/services.d/supervisor-gateway/run \
    && chmod a+x /etc/services.d/supervisor-gateway/finish
