if grep -q "ep11" backend.yml.tftpl; then
    echo "already patched — exiting."
    exit 1
fi
GREP11DIR=grep11_addon

cp terraform_grep11.tfvars $GREP11DIR/terraform.tfvars

pushd $GREP11DIR
./create_contract_shell.sh
popd
for i in cfg nginx srv 
do 
	cp -r $GREP11DIR/$i docker-compose/
done

cp backend.yml.tftpl backend.yml.tftpl.orig
cat $GREP11DIR/docker-compose.yml >> backend.yml.tftpl
mv $GREP11DIR/env-crypto.yml ..


