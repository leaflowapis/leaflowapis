# Leaflow API Contracts

This repository contains the public API contracts for the Leaflow platform. Contracts are organized by service and API version under [`leaflow/`](leaflow/):

```text
leaflow/<service>/<version>/openapi.yaml
leaflow/<service>/<sub-package>/<version>/openapi.yaml
```

Each `openapi.yaml` is a complete API entry point. Larger contracts, such as Billing, use resource files alongside the entry point and compose them with standard `$ref` references.

The [Fleet protocol](leaflow/fleet/), spoken by the Leaflow Fleet Agent, participants and the Fleet service, and its desktop feature, the [VirtualDesktop protocol](leaflow/fleet/virtualdesktop/), are defined in Protocol Buffers and checked with `buf`.

## SDKs

SDKs generated from these contracts are maintained in separate repositories:

| Language | Installation | Repository |
| --- | --- | --- |
| Go | `go get github.com/leaflowapis/leaflow-go/<service>[/<sub-package>]` | [leaflow-go](https://github.com/leaflowapis/leaflow-go) |
| TypeScript | `npm install @leaflow/sdk` | [leaflow-ts](https://github.com/leaflowapis/leaflow-ts) |
