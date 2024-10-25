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

# entrypoint for nginx
touch /tmp/certs.pem

echo 'starting envsubst'
envsubst '\$PORT' < /app-root/nginx/nginx.conf.template > /app-root/nginx/nginx.conf
echo 'Starting nginx'
nginx -c /app-root/nginx/nginx.conf -g 'daemon off;' &
# Wait for the Nginx process to finish
NGINX_PID=$!
wait $NGINX_PID

# Exit with the same exit code as the Nginx process
exit $?
