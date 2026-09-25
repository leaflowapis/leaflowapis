# Leaflow API Contracts

This repository contains the public API contracts for the Leaflow platform. Contracts are organized by service and API version under [`leaflow/`](leaflow/):

```text
leaflow/<service>/<version>/openapi.yaml
leaflow/<service>/<sub-package>/<version>/openapi.yaml
```

Sub-packages group related APIs within a service. Browse the directory for the available contracts and versions.

## SDKs

SDKs generated from these contracts are maintained in separate repositories:

| Language | Installation | Repository |
| --- | --- | --- |
| Go | `go get github.com/leaflowapis/leaflow-go/<service>[/<sub-package>]` | [leaflow-go](https://github.com/leaflowapis/leaflow-go) |
| TypeScript | `npm install @leaflow/sdk` | [leaflow-ts](https://github.com/leaflowapis/leaflow-ts) |
