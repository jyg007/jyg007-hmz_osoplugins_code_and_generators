. ./terraform_grep11.tfvars

sed -e "s/HSMDOMAIN/$HSMDOMAIN1/" -e "s/EP11SERVERPORT/10876/" grep11server.tpl > srv/grep11server1.yaml
sed -e "s/HSMDOMAIN/$HSMDOMAIN2/" -e "s/EP11SERVERPORT/11876/" grep11server.tpl > srv/grep11server2.yaml

if [[ ! -f srv/grep11ca.pem ]] 
then
	echo "Missing grep11 server certificates"
	echo "Run gen.sh to create grep11 certs and make sure grep11 client ones are properly set"
	read -n 1
	exit 3
fi

[[ -d srv ]] || mkdir srv

for i in cfg nginx srv 
do 
	cp -r $i docker-compose/
done

