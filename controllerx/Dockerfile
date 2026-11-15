# hadolint ignore=DL3006
FROM ghcr.io/hassio-addons/appdaemon:0.19.3

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# App version, "<ControllerX version>[-<app-only release>]"
ARG BUILD_VERSION
ARG BUILD_ARCH
# Checksum of controllerx.zip for the ControllerX version above
ARG CONTROLLERX_SHA256="a9c9cc828fa107ae0f483e8efc1803f22e30abb18709cbc26c7f565d4d10c705"

# Bundle ControllerX and drop the community app's initial configuration
# (hello world app and dashboard), the init-controllerx service creates ours.
RUN \
    : "${BUILD_VERSION:?BUILD_VERSION build argument is required}" \
    && controllerx_version="${BUILD_VERSION%%-*}" \
    && curl -fsSL -o /tmp/controllerx.zip \
        "https://github.com/xaviml/controllerx/releases/download/v${controllerx_version}/controllerx.zip" \
    && echo "${CONTROLLERX_SHA256}  /tmp/controllerx.zip" | sha256sum -c - \
    && python -m zipfile -e /tmp/controllerx.zip /opt/controllerx \
    && rm -fr \
        /root/appdaemon \
        /tmp/*

# Copy root filesystem
COPY rootfs /

# Labels
LABEL \
    io.hass.name="ControllerX" \
    io.hass.description="Controller-based automations running on AppDaemon with ControllerX preinstalled" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    io.hass.url="https://github.com/xaviml/controllerx-app" \
    maintainer="Xavier Moreno <xaviml.93@gmail.com>" \
    org.opencontainers.image.title="ControllerX" \
    org.opencontainers.image.description="Controller-based automations running on AppDaemon with ControllerX preinstalled" \
    org.opencontainers.image.authors="Xavier Moreno <xaviml.93@gmail.com>" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/xaviml/controllerx-app" \
    org.opencontainers.image.source="https://github.com/xaviml/controllerx-app" \
    org.opencontainers.image.documentation="https://github.com/xaviml/controllerx-app/blob/main/controllerx/DOCS.md" \
    org.opencontainers.image.version=${BUILD_VERSION}
