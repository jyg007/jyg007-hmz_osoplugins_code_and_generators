#!/bin/bash
#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#
#

cp -r /oso-root/"${COMPONENT}"/*    /app-root

if [ "${DEBUG}" == "true" ]; then
	echo "${SSH_PUBKEY}" >"${HOME}/.ssh/authorized_keys"
        sed -ie 's/#Port 22/Port '"$SSH_PORT"'/g' /etc/ssh/sshd_config
else
	export DEBUG="false"
fi

umask 0007
/app-root/entrypoints/entrypoint.sh
