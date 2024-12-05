# Offline Signing Orchestrator Ripple Custody Plugins

## Verify the Offline Signing Orchestrator Plugin image

### Prerequisites
- The supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3.

### Copy the Offline Signing Orchestrator Plugin to a private registry
1. Verify the image signature by running the command:
    ```
    wget https://public.dhe.ibm.com/systems/hyper-protect/OSO_GPG_Key.pub
    gpg --import OSO_GPG_Key.pub
    export FINGERPRINT=$(gpg --fingerprint --with-colons | grep fpr | tr -d 'fpr:')

    skopeo standalone-verify images/oso-harmonize-plugins/manifest.json us.icr.io/dap-osc-staging/oso-harmonize-plugins:v1.0.0 $FINGERPRINT images/oso-harmonize-plugins/signature-1
    ```
1. Load the docker images.

    `skopeo copy dir:./images/oso-harmonize-plugins docker://registry.control23.dap.local/oso/oso-harmonize-plugins:v1.0.0 --dest-creds $REGISTRY_USER:$REGISTRY_PASSWORD --remove-signatures`

1. Retrieve and note the digest of the loaded docker image.  The digest will be needed when setting the FRONTEND_PLUGIN_IMAGE and BACKEND_PLUGIN_IMAGE variables within the terraform.tfvars files as described in later sections of this document.

    `skopeo inspect docker://registry.control23.dap.local/oso/oso-harmonize-plugins:v1.0.0 --creds $REGISTRY_USER:$REGISTRY_PASSWORD | jq '.Name + "@" + .Digest'`

## Frontend Plugin
The Offline Signing Orchestrator frontend plugin performs import or export operations to or from the Ripple Custody core which is accessible from LPAR1 (hot).

### Prerequisites
- The supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined.
- To retrieve operations in JSON format, you must have an empty passphrase.
- Download OpenTofu and the required terraform providers (hpcr and local) from the Offline Signing Orchestrator release archive.
- OSO plugin image and SHA256 hash as described in previous section.

### Create a functional OSO user
Using the Ripple Custody UI, create a functional user specifically for OSO. The user will be used to perform import or export operations to and from Ripple Custody.

1. Generate a private key for the functional user by executing one of the following commands based on the eliptic curve algorithem required.
    1. Generate a key using secp256k1 eliptic curve.

    `openssl ecparam -genkey -name secp256k1 -noout -out privateKey.pem`

    2. Generate a key using secp256r1 eliptic curve.

    `openssl ecparam -genkey -name secp256r1 -noout -out privateKey.pem`

    3. Generate a key using ED25519 eliptic curve.

    `openssl genpkey -algorithm Ed25519 -out privateKey.pem`

1. Generate a public key from the previously generated private key.

    `openssl ec -in privateKey.pem -pubout -outform DER | openssl base64 -A -out publicKey.pem`

1. In the Ripple Custody UI, create a functional user with the user public key. Use the `publicKey.pem` for the public key content.
1. Obtain the base64 value used for the `SK` terraform variable within the contract.

    `cat privateKey.pem | base64 -w0`

### Generate encrypted workload
OSO uses the encrypted workload to deploy the frontend (LPAR1) components during the `init` process.  Change to the `frontend_plugin` directory, and complete the following steps:

1. Copy the terraform template.

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` file and assign values to the following terraform variables:
    - `HMZ_SERVER` - Ripple Custody frontend endpoint
    - `VAULTID` - Vault ID used for cold vault operations. If you are using a new vault, then generate a new uuid.
    - `SK` - Base64 private key for OSO functional user account
    - `FRONTEND_PLUGIN_IMAGE` - Frontend plugin image with sha256
    - `SEED` - Passphrase used to optionally encrypt the data being transferred between OSO and Ripple Custody. The passphrase must match with the backend.
    - `TOKEN_EXP` - Expiration time configured in Ripple Custody for the bearer token returned upon authentication
1. To generate the encrypted workload, change to the `contracts` directory and run:

    `./create-frontend.sh`

## Generate encrypted workload for GREP11 container

### Prerequisites
- The supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined.
- A configured Crypto appliance accessible from HiperSocket34 network on LPAR3.

### Copy grep11-c16 image to registry
Download the grep11-c16 image, copy it to the private registry, and obtain the sha256 of the image.  See the [IBM Hyper Protect Virtual Servers Documentation](https://www.ibm.com/docs/en/hpvs/2.1.x?topic=dcenasee-downloading-crypto-express-network-api-secure-execution-enclaves-major-release) for steps to locate and download the image.


### Generate encrypted workload
The encrypted workload will be used within OSO when deploying along with the backend services during a signing iteration process on LPAR3. Change to the `grep11` directory and perform the following steps:
1. Copy the terraform template.

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` file and assign values to the following terraform variables:
    - `PREFIX` - Prefix used for OSO deployment
    - `IMAGE` - GREP11-C16 image with sha256 (see above)
    - `DOMAIN` - Crypto appliance domain
    - `C16_CA_CERT` - Crypto appliance CA certificate
    - `C16_CLIENT_CERT` - Crypto appliance client certificate
    - `C16_CLIENT_KEY` - Crypto appliance client key
1. To perform a stand-alone deployment of GREP11 on LPAR3 without OSO, edit the terraform.tfvars file and assign values to the following terraform variables:
    - `REGISTRY_URL` - Private registry endpoint (ex. registry.control23.dap.local)
    - `REGISTRY_USERNAME` - Private registry username (ex. registryuser)
    - `REGISTRY_PASSWORD` - Private registry password
    - `REGISTRY_CA` - Private registry CA certificate
    - `SYSLOG_HOSTNAME` - Syslog hostname accessible via LPAR2/LPAR3 (ex. logging.control23.dap.local)
    - `SYSLOG_PORT` - Syslog port number (ex. 6514)
    - `SYSLOG_SERVER_CERT` - Syslog server certificate
    - `SYSLOG_CLIENT_CERT` - Syslog client certificate
    - `SYSLOG_CLIENT_KEY` - Syslog client key
1. To generate the encrypted workload, change to the `contracts` directory and run:

    `./create-grep11.sh prefix`

1. The GREP11 server and client keys/certificates are generated within the `grep11/certs` directory.  Use the GREP11 CA certificate, client certificate, and client key when setting the terraform variables for the Backend deployment as described in the next section.  Every time the `create-grep11.sh` runs, new certificates are generated.

## Backend

### Prerequisites
- Supporting infrastructure deployed containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined.
- GREP11 certificates generated by following the steps in the previous section.
- OSO plugin image and SHA256 hash as described in previous section.

### Copy cold bridge, cold vault and kmsconnect images to registry
Obtain the cold bridge, cold vault, and kmsconnect images from Ripple and copy them to the private registry. Obtain the sha256 hashes for each of the images.

### Generate encrypted workload
The encrypted workload will be used within OSO when deploying along with the GREP11 services during a signing iteration process on LPAR3. Change to the `backend` directory and perform the following steps:
1. Copy the terraform template

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` file and assign values to the following terraform variables:
    - `PREFIX` - Prefix used for OSO deployment
    - `BACKEND_PLUGIN_IMAGE` - Backend plugin image with sha256 (see above)
    - `SEED` - Passphrase used to optionally encrypt the data being transferred between OSO and Ripple Custody (matches frontend)
    - `COLD_BRIDGE_IMAGE` - Cold bridge image with sha256 (see above)
    - `COLD_VAULT_IMAGE` - Cold vault image with sha256 (see above)
    - `KMSCONNECT_IMAGE` - KMS connect image with sha256 (see above)
    - `VAULT_ID` - Vault ID used for cold vault operations
    - `NOTARY_MESSAGING_PUBLIC_KEY` - Notary messaging public key after genesis
    - `WORKLOAD_VOL_SEED` - Workload volume encryption seed
    - `GREP11_CA` - GREP11 CA certificate
    - `GREP11_CLIENT_KEY` - GREP11 client key
    - `GREP11_CLIENT_CERT` - GREP11 client certificate
1. To perform a stand-alone deployment of the backend on LPAR3 without OSO, edit the terraform.tfvars file and assign values to the following terraform variables:
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
1. To generate the encrypted workload, change to the `contracts` directory and run:

    `./create-backend.sh`

## Cold Vault Registration Process
Before deploying workloads with OSO, you must register the cold vault manually. The process requires the stand-alone deployments of both the GREP11 and backend services.

### Prerequisites
- Supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined.
- Create backend and GREP11 encrypted contracts for stand-alone mode.

1. On LPAR2, configure the HiperSockets for the airgap mode.
    ```
    sudo chzdev -a <HiperSocket12> online=0
    sudo chzdev -a <HiperSocket23> online=1
    ```
1. Copy the `output` directory to LPAR3.
1. Login to LPAR3. If required, create a temporary OSA network.

### GREP11

1. On LPAR3, change the current working directory to `output/grep11`.
1. Copy the cloudinit to the libvirt images directory.

    `sudo cp cloud-init /var/lib/libvirt/images/grep11-cloudinit`
1. Create a GREP11 overlay image.

    `sudo qemu-img create -f qcow2 /var/lib/libvirt/images/grep11-overlay.qcow2 10G`
1. Edit the domain.xml and ensure the hpcr image reference location is correct.
1. Create the GREP11 hpvs instance.

    `sudo virsh create ./domain.xml`
1. Verify through the syslog logging that the GREP11 service is initialized successfully.

### Backend

1. On LPAR3, change the current working directory to `output/backend`.
1. Copy the cloudinit to the libvirt images directory.

    `sudo cp cloud-init /var/lib/libvirt/images/vault-cloudinit`
1. Create a backend overlay image.

    `sudo qemu-img create -f qcow2 /var/lib/libvirt/images/vault-overlay.qcow2 10G`
1. Create an empty data volume for the vault if one does not already exist.

    `sudo qemu-img create -f qcow2 /var/lib/libvirt/images/vault-data.qcow2 10G`
1. Edit the domain.xml and ensure the hpcr image reference location is correct.
1. Create the backend hpvs instance.

    `sudo virsh create ./domain.xml`
1. Verify through the syslog logging that the backend services are initialized successfully.

### Vault Creation

1. During start of the vault backend service on LPAR3, review the syslog logging and obtain the new `Vault Core pubKeySig (der base64)`.
1. Within the Ripple Custody UI, create a new vault with the public key signature and the vault id specified within the contracts.
1. The vault should show the activation status as `Pending`.

### Vault Registration

1. Obtain the HiperSocket23 network address for the backend service.

    `nslookup backend.control23.dap.local 192.168.5.9`
1. Retrieve the pending operations from the cold vault.

    `curl http://<backend-ip>:8080/v1/feed/download?clean=True`
1. Import the JSON output from the curl command into the cold vault pending operations through the Ripple Custody UI as a `.dat` file.
1. Once successfully imported, the vault activation status shows `Completed`.
1. Accounts can now be created for the new cold vault.

### Cleanup

1. Shutdown grep11-c16 and backend HPVS instances.
    ```
    virsh destroy grep11-c16
    virsh destroy backend
    ```
1. On LPAR2, configure the HiperSockets for non-airgap mode.
    ```
    sudo chzdev -a <HiperSocket12> online=1
    sudo chzdev -a <HiperSocket23> online=0
    ```
1. Ensure the backend workload used within OSO includes the `STANDALONE` variable. The variable must be set to false.

## OSO Ripple Custody Encrypted Workloads
Within the orchestration process, OSO requires plugin workload definitions to be encrypted. When configuring OSO, the encrypted plugin workloads are specified in the FRONTEND_WORKLOADS and BACKEND_WORKLOADS OSO variables within the OSO `terraform.tfvars` file. After generating the encrypted plugin workloads using the `create_frontend.sh`, `create_backend.sh`, and `create_grep11.sh` scripts, obtain the values for the FRONTEND_WORKLOADS and BACKEND_WORKLOADS OSO variables by running the following command from the `contracts` directory:

`./get_workloads.sh`
