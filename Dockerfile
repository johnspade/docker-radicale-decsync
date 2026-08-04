FROM bitnami/minideb:bullseye

ARG COMMIT_ID
ENV COMMIT_ID=${COMMIT_ID}

ARG VERSION
ENV VERSION=${VERSION:-3.7.7}

ARG BUILD_UID
ENV BUILD_UID=${BUILD_UID:-2999}

ARG BUILD_GID
ENV BUILD_GID=${BUILD_GID:-2999}

ARG TAKE_FILE_OWNERSHIP
ENV TAKE_FILE_OWNERSHIP=${TAKE_FILE_OWNERSHIP:-true}

LABEL maintainer="Thomas Queste <tom@tomsquest.com>" \
      org.label-schema.name="Radicale Docker Image" \
      org.label-schema.description="Enhanced Docker image for Radicale, the CalDAV/CardDAV server, with DecSync plugin" \
      org.label-schema.url="https://github.com/Kozea/Radicale" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$COMMIT_ID \
      org.label-schema.vcs-url="https://github.com/johnspade/docker-radicale-decsync" \
      org.label-schema.schema-version="1.0"

RUN install_packages \
        curl \
        git \
        openssh-client \
        gosu \
        wget \
        python3-minimal \
        python3-venv \
        python3-pip \
        passwd \
    && install_packages \
        gcc \
        python3-dev \
        libffi-dev \
        libc-dev-bin \
    && python3 -m venv /venv \
    && /venv/bin/pip install --no-cache-dir radicale==$VERSION passlib[bcrypt] \
    && /venv/bin/pip install --no-cache-dir git+https://github.com/DiagonalArg/Radicale-DecSync.git@b4518d72c5da6ff57d9a3946a54b54c9da61ca13 \
    && apt-get remove --purge -y gcc python3-dev libffi-dev libc-dev-bin \
    && apt-get -y autoremove \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists \
    && addgroup --gid $BUILD_GID radicale \
    && adduser --uid $BUILD_UID --disabled-password --disabled-login --shell /bin/false --no-create-home --ingroup radicale radicale \
    && mkdir -p /config /data /data/decsync \
    && chmod -R 770 /data \
    && chown -R radicale:radicale /data

HEALTHCHECK --interval=30s --retries=3 CMD curl --fail http://localhost:5232 || exit 1
VOLUME /config /data
EXPOSE 5232

COPY config /config/config
COPY update_config_from_env.py /usr/local/bin
COPY docker-entrypoint.sh /usr/local/bin

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["/venv/bin/radicale", "--config", "/config/config"]
