# Folding@home v8 for Home Assistant

`foldingathome_v8` is a HACS custom integration for monitoring and controlling a
Folding@home v8 instance from Home Assistant.

This integration connects directly to the FAH v8 websocket endpoint at:

`ws://<host>:<port>/api/websocket`

The default port is `7396`.

## Features

- UI-based setup through a Home Assistant config flow
- Machine-level monitoring sensors and binary sensors
- Button controls for `fold`, `pause`, and `finish`
- Aggregate progress reporting across active work units

## Limitations

- TLS or authenticated remote access
- Folding@home cloud account management
- Advanced config mutation
- Multi-group controls
- Visualization or log streaming

## Security Notes

This integration assumes the Folding@home websocket is only exposed on a trusted
LAN. The FAH v8 direct websocket is unencrypted and should not be published to
the internet without a carefully designed secure proxy.

## Connectivity Notes

Home Assistant must be able to reach the FAH v8 websocket on port `7396`. If
your Folding@home instance is running behind a container, VM, or firewall,
ensure that the port is exposed and reachable from Home Assistant.

## Installation

1. Add this repository to HACS as a custom repository of type `Integration`.
2. Install `Folding@home v8`.
3. Restart Home Assistant.
4. Add the `Folding@home v8` integration from `Settings -> Devices & services`.
5. Enter the host and port for your FAH v8 client.
