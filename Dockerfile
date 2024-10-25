#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

FROM registry.access.redhat.com/ubi9/ubi-minimal:latest AS live

ENV HOME=/app-root
RUN microdnf --assumeyes module enable nginx:1.24 \
    && microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        install \
            python3.12 \
            gettext nginx findutils \
    && microdnf clean all

RUN install --directory --mode 0700 --owner 1001 --group 0 \
        "${HOME}" \
        "${HOME}/.ssh" \
    && chown -R 1001:0 /var/run \
    && chmod -R ug+rwX /var/run \
    && chown -R 1001:0 /var/lib/nginx \
    && chmod -R ug+rwX /var/lib/nginx \
    && chown -R 1001:0 /var/log/nginx \
    && chmod -R ug+rwX /var/log/nginx \
    && chown -R 1001:0 /usr/local/etc \
    && chmod -R ug+rwX /usr/local/etc \
    ;

FROM registry.access.redhat.com/ubi9/ubi-minimal:latest AS compile

ENV HOME=/app-root
RUN microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --setopt=keepcache=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        install \
            openssl-devel \
            gcc cargo rustc \
            python3.12-pip python3.12-devel \
    && mkdir -p "${HOME}"
ARG PIP_INDEX_URL=https://pypi.org/simple \
    PIP_CACHE_DIR=/pipcache

COPY /requirements*.txt /tmp
RUN --mount=type=secret,id=netrc,target=${HOME}/.netrc,mode=0600 \
    --mount=type=cache,id=pipcache,target=${PIP_CACHE_DIR} \
    pip3.12 install --upgrade --require-hashes \
        --requirement <(gawk 'BEGIN { RS = "[^\\\\]\n" } /pip==/ { print }' /tmp/requirements.constraints.txt) \
    && pip3.12 install --requirement /tmp/requirements.build.txt \
    && python3.12 -m venv --without-pip /opt/venv \
    && pip3.12 --python /opt/venv install --requirement /tmp/requirements.txt

COPY /src/oso_harmonize_plugins /src/oso_harmonize_plugins
COPY /src/setup.py /src
RUN pip3.12 wheel --wheel-dir /build --no-index --no-build-isolation /src \
    && pip3.12 --python /opt/venv install --no-index --find-links /build oso_harmonize_plugins

FROM live AS release

COPY --from=compile --chown=1001:0 /opt/venv /opt/venv
COPY --from=compile --chown=1001:0 ${HOME} ${HOME}
COPY --chown=1001:0 /src/app-root /oso-root

USER 1001
ENV PATH="/opt/venv/bin:$PATH"
CMD [ "/oso-root/common/entrypoints/entrypoint.sh" ]
