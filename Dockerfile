#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

FROM registry.access.redhat.com/ubi9/ubi-minimal:9.8 AS live

ENV HOME=/app-root
#RUN --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum.repos.d/centos.repo,target=/etc/yum.repos.d/centos.repo \
#    --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial,target=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial \
#    --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum/vars/stream,target=/etc/yum/vars/stream \
RUN    rpm --install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    microdnf update -y  && microdnf --assumeyes module enable nginx:1.26 && \
    microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        --enablerepo=ubi-9-codeready-builder-rpms \
        --enablerepo=epel \
        install \
            python3.13 \
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

FROM registry.access.redhat.com/ubi9/ubi-minimal:9.8 AS compile

ENV HOME=/app-root \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

#RUN --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum.repos.d/centos.repo,target=/etc/yum.repos.d/centos.repo \
 #   --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial,target=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial \
  #  --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum/vars/stream,target=/etc/yum/vars/stream \
RUN rpm --install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm &&\
    microdnf update -y  && microdnf --assumeyes module enable nginx:1.26 && \
    microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --setopt=keepcache=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        --enablerepo=ubi-9-codeready-builder-rpms \
        --enablerepo=epel \
        install \
            openssl-devel \
            gcc cargo rustc \
            python3.13-pip python3.13-devel \
    && microdnf clean all \
    && rm -rf /var/cache/dnf /var/cache/yum

RUN  mkdir -p "${HOME}"
ARG PIP_INDEX_URL=https://pypi.org/simple \
    PIP_CACHE_DIR=/pipcache

COPY /requirements*.txt /tmp
RUN --mount=type=secret,id=netrc,target=${HOME}/.netrc,mode=0600 \
    --mount=type=cache,id=pipcache,target=${PIP_CACHE_DIR} \
    pip3.13 install --upgrade --require-hashes \
        --requirement <(gawk 'BEGIN { RS = "[^\\\\]\n" } /pip==/ { print }' /tmp/requirements.constraints.txt) \
    && pip3.13 install --requirement /tmp/requirements.build.txt \
    && python3.13 -m venv --without-pip /opt/venv \
    && pip3.13 --python /opt/venv install --requirement /tmp/requirements.txt
RUN pip3.13 --python /opt/venv install --upgrade --no-cache-dir jaraco.context==6.1.0 \
	urllib3>=2.0.6 \
        six>=1.17.0 \
        requests>=2.31.0

COPY /src/oso_harmonize_plugins /src/oso_harmonize_plugins
COPY /src/setup.py /src
RUN pip3.13 wheel --wheel-dir /build --no-index --no-build-isolation /src \
    && pip3.13 --python /opt/venv install --no-index --find-links /build oso_harmonize_plugins

FROM live AS release

COPY --from=compile --chown=1001:0 /opt/venv /opt/venv
COPY --from=compile --chown=1001:0 ${HOME} ${HOME}
COPY --chown=1001:0 /src/app-root /oso-root

RUN rm -rf /app-root/.cargo


RUN rpm -e --nodeps acl curl-minimal glib2 libcurl-minimal libarchive gnupg2 gpgme libdnf librepo microdnf  libmount util-linux util-linux-core libblkid libfdisk libsmartcols libnghttp2 libsolv
RUN rpm -e --justdb --nodeps pcre2 openssl-libs nginx-core 
RUN rpm -e --nodeps  dbus-broker dbus systemd krb5-libs cyrus-sasl-lib openldap bzip2-libs gawk gzip ncurses-base p11-kit p11-kit-trust pcre2-syntax sqlite-libs rpm rpm-libs  openssl libxml2 nginx-filesystem nginx pam libuuid libgomp systemd-rpm-macros systemd-libs systemd-pam sed  libgcrypt xz-libs libstdc++ openssl-fips-provider openssl-fips-provider-so

USER 1001
ENV PATH="/opt/venv/bin:$PATH"
CMD [ "/oso-root/common/entrypoints/entrypoint.sh" ]
