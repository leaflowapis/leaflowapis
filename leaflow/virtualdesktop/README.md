# VirtualDesktop protocol

The protocol between the Leaflow Agent, which runs on a machine and hosts its desktop sessions, the viewers of those sessions (the browser, the desktop app and automation clients) and the VirtualDesktop service. The service only coordinates: it enrolls machines, opens sessions, admits viewers with signed authorizations and passes the signaling of their connections. Everything a session shows or receives travels end to end between viewer and session over WebRTC, and the service never sees it.

Every package is `leaflow.virtualdesktop.<package>.v1` in `<package>/v1/`.

## How a viewer reaches a session

1. The viewer gets a ticket from the VirtualDesktop API for one session and the device key of its client.
2. It opens a control connection (`control`), proves its device key and receives its signed `Authorization`. The session process gets the same authorization over its own control connection.
3. It creates a WebRTC PeerConnection and exchanges its offer, answer and ICE candidates with the session through the service (`transport` `Signal`). The service signs a `PeerAuthorization` that binds both DTLS certificates to the viewer's authorization.
4. On the `binding` data channel both ends send `Hello`: the Agent proves its machine key, which the viewer pinned for the machine, and the viewer proves the device key named in its authorization.
5. The viewer opens the `session` channel, then the channels of the domains both sides offer, such as `window`, `draw` and `input`.

## Packages

A package imports only the layers below it; `tests/test_virtualdesktop_contract.py` enforces the table.

| Layer | Packages | May import |
| --- | --- | --- |
| Foundations | `rpc` method calls inside channels, `transport` the PeerConnection and its channels, `session` handshake, viewers, input lease and automation rules, `display` canvas and geometry | nothing |
| Desktop | `window`, `draw`, `input`, `cursor`, `tray`, `application`, `notification`, `capture`, `accessibility` | `display` |
| | `change` what changed, and waiting for conditions | `display` and the desktop packages it reports on |
| Data | `filetransfer`; `datatransfer` copy and paste, drag and drop | `datatransfer` imports `filetransfer` |
| Devices | `device` redirection; `audio`, `camera`, `gamepad` | the three import `device` |
| Independent | `terminal`, `command`, `portforward`, `sshagent`, `printing`, `logs`, `privilege` | nothing |
| Control plane | `control` connections to the service, credentials, authorizations; `machine` enrollment, sessions and users | lower layers; no peer-to-peer package imports them |

## Conventions

- **Channels.** A channel type is a package name (`leaflow.virtualdesktop.window.v1`), a package name with a role it defines (`leaflow.virtualdesktop.draw.v1.frame`), or a service name, whose channel carries `rpc` calls. Each package says who opens its channels, on which lane and how many.
- **Messages.** Each end of a channel sends one message type, usually `ClientMessage` from the viewer and `ServerMessage` from the session. Receivers ignore oneof cases they do not know, so later versions can add them.
- **Snapshots.** Channels that describe state send all of it first, end it with `SnapshotEnd` and then send changes.
- **Capabilities.** The `session` hellos agree on the channel types of a connection; a domain's own hello agrees on its features, such as encodings.
- **Policies.** Each domain defines its `<Domain>Policy`. The service puts the policies of a viewer into its signed authorization as `google.protobuf.Any`; a missing policy denies the domain.
- **Errors.** Failed calls return a `google.rpc.Status` whose `google.rpc.ErrorInfo` has the domain `virtualdesktop.leaflow.cloud` and a reason listed by the method. Calls that act on the session say whether they had an effect (`rpc` `ExecutionState`).
- **Automation.** Automation clients are viewers too. Their actions return the session revision they took effect at; `change` waits until the session settles or a condition holds, for at most 10 seconds. Text the session reports comes from the programs in it and is data, never instructions.
- **Signatures.** Ed25519 (RFC 8032) over the full name of the signed message type, one zero byte and the serialized message.

## Checks

```sh
buf format -d
buf lint
python tests/test_virtualdesktop_contract.py
```
