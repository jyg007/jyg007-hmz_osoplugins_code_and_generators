# Digital Asset Platform Cold Storage Metaco Harmonize Plugins

This repo maintains the document and code to define Metaco Harmonize plugins for the IBM Offline Signing Orchestrator.

## Building
### Build environment variables
| Environment Variable  | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| REGISTRY_URL          | URL of your container registry (e.g., us.icr.io). |
| REGISTRY_NAMESPACE    | Container registry namespace |

### Frontend Sidecar
```
export REGISTRY_URL=us.icr.io
export REGISTRY_NAMESPACE=<REGISTRY_NAMESPACE>
make frontend_sidecar
```

### Backend Sidecar
```
export REGISTRY_URL=us.icr.io
export REGISTRY_NAMESPACE=<REGISTRY_NAMESPACE>
make backend_sidecar
```

### Sidecar Contracts
1. Change the working directory to `contracts`
1. For both backend_sidecar and frontend_sidecar directories, copy the `terraform.tfvars.template` file to `terraform.tfvars` and fill out the required variables
1. Generate the contracts: `./create_contracts.sh` under the `contracts` directory
1. Use the generated encrypted workload as part of the Offline Signing Orchestrator conductor plugin workloads
