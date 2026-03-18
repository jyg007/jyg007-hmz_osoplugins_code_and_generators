# Digital Asset Platform Cold Storage Metaco Harmonize Plugins

This repo maintains the document and code to define Metaco Harmonize plugins for the IBM Offline Signing Orchestrator 1.3.2, 1.4+ and 1.5
It supports multivault capability while the backend.tfpl requires updates.

## Building

```
make generate
make build
```

### Contract Generators

frontend-plugin and backend-plugin contract generators can be found in contract directory.
grep11 server certificates (and client) must be generated before (use `gen.sh` script).
