. ./terraform_grep11.tfvars

for i in HSMDOMAIN2 HSMDOMAIN1 
do
  sed -i "s/^$i/export $i/" ./o.$$
done

sed -e "s/HSMDOMAIN/$HSMDOMAIN1/" -e "s/EP11SERVERPORT/10876/" grep11server.tpl > srv/grep11server1.yaml
sed -e "s/HSMDOMAIN/$HSMDOMAIN2/" -e "s/EP11SERVERPORT/11876/" grep11server.tpl > srv/grep11server2.yaml

GREP11DIR=grep11_addon

cp terraform_grep11.tfvars $GREP11DIR/terraform.tfvars

for i in cfg nginx srv 
do 
	cp -r $i docker-compose/
done


