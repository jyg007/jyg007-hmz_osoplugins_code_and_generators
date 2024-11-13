# Offline Signing Orchestrator Harmonize Plugins

## oso-harmonize-plugins image

### Prereqs
- Supporting infrastructure deployed containing syslog/registry/etc across LPAR1-LPAR3

### Copy oso-harmonize-plugins image to private registry
1. Verify the image signature
    ```
    wget https://public.dhe.ibm.com/systems/hyper-protect/OSO_GPG_Key.pub
    gpg --import OSO_GPG_Key.pub
    export FINGERPRINT=$(gpg --fingerprint --with-colons | grep fpr | tr -d 'fpr:')

    skopeo standalone-verify images/oso-harmonize-plugins/manifest.json us.icr.io/dap-osc-staging/oso-harmonize-plugins:v1.0.0 $FINGERPRINT images/oso-harmonize-plugins/signature-1
    ```
1. Load Docker images

    `skopeo copy dir:./images/oso-harmonize-plugins docker://registry.control23.dap.local/oso/oso-harmonize-plugins:v1.0.0 --dest-creds $REGISTRY_USER:$REGISTRY_PASSWORD --remove-signatures`
1. Retrieve the digest of the loaded docker image:

    `skopeo inspect docker://registry.control23.dap.local/oso/oso-harmonize-plugins:v1.0.0 --creds $REGISTRY_USER:$REGISTRY_PASSWORD | jq '.Name + "@" + .Digest'`

## Frontend Plugin
The oso harmonize frontend plugin is used to import/export operations from within Harmonize Core accessible from LPAR1 (hot).

### Prereqs
- Supporting infrastructure deployed containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined
- For the frontend plugin to retrieve operations in a consumable format (JSON), a ticket should be created against the Harmonize DevOps team to set an empty passphrase
- OpenTofu and required terraform providers (hpcr/null) which can be obtained via the OSO release archive

### Functional OSO user
A functional user specific for OSO should be created within the Harmonize UI. This user will be used to import/export operations from within Harmonize.

1. Generate a private key used for the functional user
    1. Key generation using secp256k1 eliptic curve

    `openssl ecparam -genkey -name secp256k1 -noout -out privateKey.pem`

    2. Key generation using secp256r1 eliptic curve

    `openssl ecparam -genkey -name secp256r1 -noout -out privateKey.pem`

    3. Key generation using ED25519 eliptic curve

    `openssl genpkey -algorithm Ed25519 -out privateKey.pem`

1. Generate a public key from the previously generated private key

    `openssl ec -in privateKey.pem -pubout -outform DER | openssl base64 -A -out publicKey.pem`
1. Within the Harmonize UI, create the functional user with the user public key from the content of the public key `publicKey.pem`.
1. Obtain the base64 value used for the `SK` terraform variable within the contract

    `cat privateKey.pem | base64 -w0`

### Generate encrypted workload
The encrypted workload will be used within OSO when deploying the frontend (LPAR1) components during the `init` process. Within the `frontend_plugin` directory:

1. Copy the terraform template

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` and assign values to the terrarform variables
    - `HMZ_SERVER` - Harmonize frontend endpoint
    - `VAULTID` - Vault ID used for cold vault operations (if new vault, generate a new uuid)
    - `SK` - Base64 private key for OSO functional user account (see above)
    - `FRONTEND_PLUGIN_IMAGE` - Frontend plugin image with sha256 (see above)
    - `SEED` - Passphrase used to optionally encrypt the data being transferred between OSO and Harmonize (matches backend)
    - `TOKEN_EXP` - Expiration time configured in Harmonize for the bearer token returned upon authentication
1. Within the `contracts` directory, generate the encrypted workload:

    `./create-frontend.sh`

## Grep11

### Prereqs
- Supporting infrastructure deployed containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined
- Crypto appliance has been configured and accessible on HiperSocket34 network on LPAR3

### Copy grep11-c16 image to registry
Obtain the grep11-c16 image and copy it to the private registry, obtaining the sha256 of the image (used below).

### Generate grep11 keys and certificates
The grep11 server and client keys/certificates can be generated from within the `grep11/certs` directory.
1. Update the `prefix` with the correct value within the `server.cnf` file
1. Generate the keys and certificates: `./gen.sh`

### Generate encrypted workload
The encrypted workload will be used within OSO when deploying along with the backend services during a signing iteration process on LPAR3. Within the `grep11` directory:
1. Copy the terraform template

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` and assign values to the terraform variables
    - `IMAGE` - GREP11-C16 image with sha256 (see above)
    - `GREP11_CA_CERT` - Grep11 CA certificate (see above)
    - `GREP11_SERVER_KEY` - Grep11 server private key (see above)
    - `GREP11_SERVER_CERT` - Grep11 server certificate (see above)
    - `DOMAIN` - Crypto appliance domain
    - `C16_CA_CERT` - Crypto appliance CA certificate
    - `C16_CLIENT_CERT` - Crypto appliance client certificate
    - `C16_CLIENT_KEY` - Crypto appliance client key
1. To perform a stand-alone deployment of GREP11 on LPAR3 without OSO, edit the terraform.tfvars and assign values to the terraform variables
    - `REGISTRY_URL` - Private registry endpoint (ex. registry.control23.dap.local)
    - `REGISTRY_USERNAME` - Private registry username (ex. registryuser)
    - `REGISTRY_PASSWORD` - Private registry password
    - `REGISTRY_CA` - Private registry CA certificate
    - `SYSLOG_HOSTNAME` - Syslog hostname accessible via LPAR2/LPAR3 (ex. logging.control23.dap.local)
    - `SYSLOG_PORT` - Syslog port number (ex. 6514)
    - `SYSLOG_SERVER_CERT` - Syslog server certificate
    - `SYSLOG_CLIENT_CERT` - Syslog client certificate
    - `SYSLOG_CLIENT_KEY` - Syslog client key
1. Within the `contracts` directory, generate the encryptd workload:

    `./create-grep11.sh <prefix>`

## Backend

### Prereqs
- Supporting infrastructure deployed containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined
- Grep11 certificates generated (see above)

### Copy cold bridge, cold vault and kmsconnect images to registry
Obtain the cold bridge, cold vault, and kmsconnect images and copy them to the private registry, obtaining the sha256 of the image (used below).

### Generate encrypted workload
The encrypted workload will be used within OSO when deploying along with the grep11 services during a signing iteration process on LPAR3. Within the `backend` directory:
1. Copy the terraform template

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` and assign values to the terraform variables
    - `BACKEND_PLUGIN_IMAGE` - Backend plugin image with sha256 (see above)
    - `SEED` - Passphrase used to optionally encrypt the data being transferred between OSO and Harmonize (matches frontend)
    - `COLD_BRIDGE_IMAGE` - Cold bridge image with sha256 (see above)
    - `COLD_VAULT_IMAGE` - Cold vault image with sha256 (see above)
    - `KMSCONNECT_IMAGE` - KMS connect image with sha256 (see above)
    - `VAULT_ID` - Vault ID used for cold vault operations
    - `NOTARY_MESSAGING_PUBLIC_KEY` - Notary messaging public key after genesis
    - `WORKLOAD_VOL_SEED` - Workload volume encryption seed
    - `GREP11_ENDPOINT` - GREP11 backend service endpoint (ex. <prefix>-cs-backend-grep11.control23.dap.local:9876)
    - `GREP11_CA` - GREP11 CA certificate
    - `GREP11_CLIENT_KEY` - GREP11 client key
    - `GREP11_CLIENT_CERT` - GREP11 client certificate
1. To perform a stand-alone deployment of GREP11 on LPAR3 without OSO, edit the terraform.tfvars and assign values to the terraform variables
    - `STANDALONE` - Only enabled when deploying the backend service as stand alone (without OSO) during vault registration
    - `ENV_VOL_SEED` - Environment volume encryption seed (should match with what is set from within OSO terraform.tfvars)
    - `REGISTRY_URL` - Private registry endpoint (ex. registry.control23.dap.local)
    - `REGISTRY_USERNAME` - Private registry username (ex. registryuser)
    - `REGISTRY_PASSWORD` - Private registry password
    - `REGISTRY_CA` - Private registry CA certificate
    - `SYSLOG_HOSTNAME` - Syslog hostname accessible via LPAR2/LPAR3 (ex. logging.control23.dap.local)
    - `SYSLOG_PORT` - Syslog port number (ex. 6514)
    - `SYSLOG_SERVER_CERT` - Syslog server certificate
    - `SYSLOG_CLIENT_CERT` - Syslog client certificate
    - `SYSLOG_CLIENT_KEY` - Syslog client key
1. Within the `contracts` directory, generate the encryptd workload:

    `./create-backend.sh`

## Registry Cold Vault Process
The cold vault will need to be registered as part of a manual process prior to deploying the workloads with OSO. The process requires the stand-alone deployments of both the GREP11 and Backend Services.

### Prereqs
- Supporting infrastructure deployed containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined
- Backend and grep11 encrypted contracts have been created for stand-alone mode (see above)

1. On LPAR2, configure the HiperSockets for the airgap mode
    ```
    sudo chzdev -a <HiperSocket12> online=0
    sudo chzdev -a <HiperSocket23> online=1
    ```
1. Copy the `output` directory to LPAR3
1. Login to LPAR3 (create temporary OSA network if required)

### Grep11

1. On LPAR3, change the current working direcotry to `output/grep11`
1. Copy the cloudinit to the libvirt images directory:

    `sudo cp cloud-init /var/lib/libvirt/images/grep11-cloudinit`
1. Create a grep11 overlay image:

    `sudo qemu-img create -f qcow2 /var/lib/libvirt/images/grep11-overlay.qcow2 10G`
1. Edit the domain.xml and ensure the hpcr image reference location is correct
1. Create the grep11 hpvs instance:

    `sudo virsh create ./domain.xml`
1. Verify through the syslog logging that the GREP11 service comes up successfully

### Backend

1. On LPAR3, change the current working directory to `output/backend`
1. Copy the cloudinit to the libvirt images directory:

    `sudo cp cloud-init /var/lib/libvirt/images/vault-cloudinit`
1. Create a backend overlay image:

    `sudo qemu-img create -f qcow2 /var/lib/libvirt/images/vault-overlay.qcow2 10G`
1. Create an empty data volume for the vault (if not already create):

    `sudo qemu-img create -f qcow2 /var/lib/libvirt/images/vault-data.qcow2 10G`
1. Edit the domain.xml and ensure the hpcr image reference location is correct
1. Create the backend hpvs instance:

    `sudo virsh create ./domain.xml`
1. Verify through the syslog logging that the backend services comes up successfully

### Vault Creation

1. During start of the vault backend service on LPAR3, review the syslog logging and obtain the new `Vault Core pubKeySig (der base64)`
1. Within the Harmonize UI, create a new vault with the public key signature and the vault id specified within the contracts
1. The vault should show it's activation status as `Pending`

### Vault Registration

1. Obtain the HiperSocket23 network address for the backend service

    `nslookup backend.control23.dap.local 192.168.5.9`
1. Retrieve the pending operations from the cold vault:

    `curl http://<backend-ip>:8080/v1/feed/download?clean=True`
1. Import the JSON output from the curl command into the cold vault pending operations through the Harmonize UI as a `.dat` file
1. Once successfully imported, the vault activation status shows `Completed`
1. Accounts can now be created for the new cold vault

### Cleanup

1. Shutdown grep11-c16 and backend HPVS instances
    ```
    virsh destroy grep11-c16
    virsh destroy backend
    ```
1. On LPAR2, configure the HiperSockets for non-airgap mode
    ```
    sudo chzdev -a <HiperSocket12> online=1
    sudo chzdev -a <HiperSocket23> online=0
    ```
1. Ensure the backend workload used within OSO includes the `STANDALONE` variable set to false

## OSO Harmonize Encrypted Workloads
OSO requires plugin encrypted workloads as part of it's orchestration process, such as the `FRONTEND_WORKLOADS` and `BACKEND_WORKLOADS`. After generating the encrypted workloads via the `create_frontend.sh` `create_backend.sh` `create_grep11.sh`, the workloads can be displayed via the following commmand and used directly within OSO's `terraform.tfvars` file:

`./get_workloads.sh`

Congratulations, OSO is ready to orchestrate the cold signing process with Ripple/Metaco Harmonize!
