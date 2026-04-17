# Folding@home v8 for Home Assistant

`foldingathome_v8` is a HACS custom integration for monitoring and controlling a
local Folding@home v8 client from Home Assistant.

This integration connects directly to the FAH v8 websocket endpoint at:

`ws://<host>:<port>/api/websocket`

The default port is `7396`.

## Features

- UI-based setup through a Home Assistant config flow
- Machine-level status entities
- Button entities for `fold`, `pause`, and `finish`
- Dynamic sensors for active work units in the default resource group

## What v1 Supports

- Direct local websocket access only
- The default resource group only
- Work-unit monitoring for currently active units

## What v1 Does Not Support

- TLS or authenticated remote access
- Folding@home cloud account management
- Advanced config mutation
- Multi-group controls
- Visualization or log streaming

## Security Notes

This integration assumes the Folding@home websocket is only exposed on a trusted
LAN. The FAH v8 direct websocket is unencrypted and should not be published to
the internet without a carefully designed secure proxy.

## Docker Notes

Your Folding@home container must expose port `7396` from the container to the
network Home Assistant can reach.

Example:

```yaml
services:
  fah:
    image: ghcr.io/foldingathome/fah-gpu:latest
    ports:
      - "7396:7396"
```

You may also need to configure the FAH client/container so it binds the control
interface beyond `127.0.0.1`.

## Installation

1. Add this repository to HACS as a custom repository of type `Integration`.
2. Install `Folding@home v8`.
3. Restart Home Assistant.
4. Add the `Folding@home v8` integration from `Settings -> Devices & services`.
5. Enter the host and port for your FAH v8 client.

## Entities

Stable entities:

- `binary_sensor.connected`
- `sensor.client_state`
- `sensor.active_work_units`
- `sensor.total_ppd`
- `sensor.client_version` (diagnostic, disabled by default)

Control entities:

- `button.fold`
- `button.pause`
- `button.finish`

Dynamic entities:

- one progress sensor per active work unit in the default group

