# Leaflow API Contracts

OpenAPI contracts for the Leaflow platform, organized by service and API version under `leaflow/`.

```text
leaflow/<service>/<version>/openapi.yaml
leaflow/<service>/<sub-package>/<version>/openapi.yaml
```

Each `openapi.yaml` is an entry point. Larger contracts reference sibling files with `$ref`.

The [Fleet protocol](leaflow/fleet/) and its [VirtualDesktop protocol](leaflow/fleet/virtualdesktop/) are defined in Protocol Buffers and checked with `buf`.

## SDKs

| Language | Installation | Repository |
| --- | --- | --- |
| Go | `go get github.com/leaflowapis/leaflow-go/<service>[/<sub-package>]` | [leaflow-go](https://github.com/leaflowapis/leaflow-go) |
| TypeScript | `npm install @leaflow/sdk` | [leaflow-ts](https://github.com/leaflowapis/leaflow-ts) |
| Rust | `cargo add leaflow-<service> --git https://github.com/leaflowapis/leaflow-rs` | [leaflow-rs](https://github.com/leaflowapis/leaflow-rs) |
