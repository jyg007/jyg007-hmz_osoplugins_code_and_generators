#!/bin/bash

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

#terraform init
#terraform destroy -auto-approve

. ./terraform.tfvars

sed -e 's#${tpl.imagegrep11}#'$IMAGEGREP11"#" -e 's#${tpl.imagenginx}#'$IMAGENGINX"#" grep11-c16.yml.tftpl > docker-compose.yml

sed -e 's/<<-EOT/$(cat <<-EOT /' -e 's/^EOT/EOT\n)/' ./terraform.tfvars > ./o.$$ 
for i in IMAGE SYSLOG REGISTRY MACHINE2 MACHINE2_DESCRIPTION MACHINE2_HKD_B24 HSMDOMAIN2 MACHINE1 MACHINE1_DESCRIPTION MACHINE1_HKD_B24 HSMDOMAIN1 SECRET_B24 MKVP 
do
  sed -i "s/^$i/export $i/" ./o.$$
done

. ./o.$$
rm ./o.$$

sed -e "s/HSMDOMAIN/$HSMDOMAIN1/" grep11server.tpl > srv/grep11server1.yaml
sed -e "s/HSMDOMAIN/$HSMDOMAIN2/" grep11server.tpl > srv/grep11server2.yaml

ENV=env-crypto.yml
envsubst < env.tpl > $ENV

