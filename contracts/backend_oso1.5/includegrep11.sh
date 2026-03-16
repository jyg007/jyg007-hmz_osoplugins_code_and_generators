GREP11DIR=grep11_addon

cp terraform_grep11.tfvars $GREP11DIR/terraform.tfvars

pushd $GREP11DIR
./create_contract_shell.sh
popd
for i in cfg nginx srv 
do 
	cp -r $GREP11DIR/$i docker-compose/
done

mv $GREP11DIR/env-crypto.yml ..


