#!/bin/bash

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

sed -i -e 's/^module/#module/g' /etc/rsyslog.conf

envsubst '\$SYSLOG_HOSTNAME \$SYSLOG_PORT' < /app-root/logging/rsyslog.conf.template > /etc/rsyslog.d/100-component.conf
rm -f /etc/rsyslog.d/50-default.conf

rsyslogd -n
