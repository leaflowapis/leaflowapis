# Leaflow API Contracts

This repository contains the public API contracts for the Leaflow platform. Contracts are organized by service and API version under [`leaflow/`](leaflow/):

```text
leaflow/<service>/<version>/openapi.yaml
```

Browse the directory for the available contracts and versions.

## SDKs

SDKs generated from these contracts are maintained in separate repositories:

| Language | Installation | Repository |
| --- | --- | --- |
| Go | `go get github.com/leaflowapis/leaflow-go/<service>` | [leaflow-go](https://github.com/leaflowapis/leaflow-go) |
| TypeScript | `npm install @leaflow/sdk` | [leaflow-ts](https://github.com/leaflowapis/leaflow-ts) |

## Apifox synchronization

After changes are merged into `main`, GitHub Actions imports each service's `openapi.yaml` into its corresponding Apifox project. The workflow creates missing projects and can also be run manually from the Actions page.

Configure the following in the GitHub repository or organization:

- Secret `APIFOX_ACCESS_TOKEN`: Create an API access token in Apifox account settings with permission to edit the target projects.
- Variable `APIFOX_TEAM_ID`: The Apifox team ID under which projects are created.

Project names come from the contract's `info.title`. The workflow looks up a project by its full name, reuses an existing match, or creates a new project. It stops if multiple projects have the same name to avoid importing into the wrong project. Keep `info.title` stable after project creation; if it changes, rename the Apifox project as well.

The workflow bundles each contract and its `$ref` dependencies on the GitHub runner, then imports the result through the Apifox API. It creates new endpoints and replaces matching endpoints and data models, but does not delete endpoints found only in Apifox. Treat `APIFOX_ACCESS_TOKEN` as a privileged credential and restrict access to Actions and repository secrets. New contracts under `leaflow/<service>/<version>/openapi.yaml` require no additional project ID configuration.
