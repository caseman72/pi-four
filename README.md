# Pi-Four Shop Door Controller

MQTT-based shop/barn door controller for Home Assistant. Runs on a Raspberry Pi 4B, forwarding door commands to a liftmaster-remote ESP32 via MQTT. Tilt sensors provide door state via Zigbee2MQTT.

## Architecture

```
HA Cover Entity → MQTT → pi-four (shop-controller) → MQTT → liftmaster-remote → relay pulse
                                                       ↑
Z2M (zigbee-shop) ← Sonoff dongle ← Zigbee tilt sensors (state)
```

No local GPIO — all 5 doors are remote-controlled via liftmaster-remote.

## Doors

| Door | Z2M State Topic | Liftmaster Command |
|------|----------------|--------------------|
| Shop Door 1 | `zigbee-shop/shop_door_1` | `liftmaster/button/shop_door_1/command` |
| Shop Door 2 | `zigbee-shop/shop_door_2` | `liftmaster/button/shop_door_2/command` |
| Shop Door 3 | `zigbee-shop/shop_door_3` | `liftmaster/button/shop_door_3/command` |
| Shop Door 4 | `zigbee-shop/shop_door_4` | `liftmaster/button/shop_door_4/command` |
| Barn Door   | `zigbee-shop/barn_door`   | `liftmaster/button/barn_door/command`   |

## Deploy

```bash
bash src/deploy.sh
```

Deploys to `pi-four:/opt/shop-controller` and configures Zigbee2MQTT.

### First-time setup

1. Flash Raspberry Pi OS Lite (64-bit), hostname `pi-four`
2. Create secrets on the Pi:
   ```bash
   ssh pi-four
   sudo mkdir -p /opt/shop-controller
   sudo chown caseman:caseman /opt/shop-controller
   cat > /opt/shop-controller/secrets.env << EOF
   MQTT_USER=your_username
   MQTT_PASS=your_password
   EOF
   chmod 600 /opt/shop-controller/secrets.env
   ```
3. Run `bash src/deploy.sh`
4. Edit Z2M config with broker password and dongle serial

## Zigbee2MQTT

Base topic: `zigbee-shop` (channel 20, separate from pi-three on channel 25).

Pair sensors:
```bash
mosquitto_pub -t 'zigbee-shop/bridge/request/permit_join' -m '{"time": 120}'
```

Rename by IEEE address after pairing:
- `0xffffb40e0601cc87` → `shop_door_1`
- `0xffffb40e0601d4f7` → `shop_door_2`
- `0xffffb40e06061cf2` → `shop_door_3`
- `0xffffb40e06062fe8` → `shop_door_4`
- `0xffffb40e0601d759` → `barn_door`

## MQTT Topics

| Topic | Direction | Payload |
|-------|-----------|---------|
| `shop-controller/status` | Pi → Broker | `online` / `offline` |
| `shop-controller/button/{door_id}/command` | Broker → Pi | `PRESS` |
| `liftmaster/button/{door_id}/command` | Pi → Broker | `PRESS` (forwarded) |
| `zigbee-shop/{door_id}` | Z2M → Broker | `{"contact": true/false, ...}` |
| `homeassistant/cover/shop-controller/*/config` | Pi → Broker | HA cover discovery JSON |

## Tests

```bash
python3 -m pytest tests/ -v
```

## Hardware

- Raspberry Pi 4B Rev 1.4 (headless, Ethernet)
- SONOFF Zigbee 3.0 USB Dongle Plus (Ember adapter)
- 5x Third Reality Zigbee tilt sensors
- Liftmaster-remote ESP32 (relay control, separate device)
