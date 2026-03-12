#!/bin/bash

#!/usr/bin/bash

#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2023
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#


# CA
openssl genrsa -out grep11ca-key.pem 4096
openssl req -config ca.cnf -key grep11ca-key.pem -new -out grep11ca-req.csr
openssl x509 -signkey grep11ca-key.pem -extfile ca.cnf -extensions v3_ca -in grep11ca-req.csr -req -days 7300 -out grep11ca.pem

# Server
#openssl req -config server.cnf -newkey rsa:4096 -nodes -keyout grep11server-key.pem -new -extensions grep11server -out grep11server.csr
#openssl x509 -req -in grep11server.csr -days 7300 -CA grep11ca.pem -CAkey grep11ca-key.pem -CAcreateserial -extensions grep11server -out grep11server.pem
openssl genrsa -out grep11server-key.pem 4096
openssl req -config server.cnf -key grep11server-key.pem -new -out grep11server-req.csr
openssl x509 -in grep11server-req.csr -req -days 7300 -CA grep11ca.pem -CAkey grep11ca-key.pem -CAcreateserial -extfile server.cnf -extensions grep11server -out grep11server.pem


# Client
openssl req -config client.cnf -newkey rsa:4096 -nodes -keyout grep11client-key.pem -new -out grep11client.csr
openssl x509 -req -in grep11client.csr -days 7300 -CA grep11ca.pem -CAkey grep11ca-key.pem -CAcreateserial -out grep11client.pem

cp grep11ca.pem grep11server.pem grep11server-key.pem ../srv/
