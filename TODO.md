# Pi-Four Shop Door Controller — TODO

## Phase 1 — Flash Pi 4B
- [x] Flash Raspberry Pi OS Lite (64-bit) onto **new** SD card
- [x] Keep old SD card as backup
- [x] Boot, set hostname `pi-four`
- [x] Enable SSH, copy `~/.ssh/authorized_keys`
- [x] Configure network (Ethernet ~and/or WiFi `farmland`~)
- [x] Add static route in DD-WRT for `pi-four` (hostname → IP)
- [x] Verify `ssh pi-four` works from Mac

## Phase 2 — Code (clone pi-three → adapt)
- [ ] Init git repo in `pi-four/`
- [ ] Create `src/shop_controller.py` — adapted from pi-three `relay_controller.py`
  - No GPIO — all 5 doors forward MQTT commands to liftmaster-remote
  - Doors: `shop_door_1..4`, `barn_door`
  - State topics: `zigbee-shop/{door_id}`
  - Command forwarding: `liftmaster/button/{door_id}/command` → `PRESS`
  - Cover discovery: `homeassistant/cover/shop-controller/{door_id}/config`
  - Stale discovery cleanup on connect
- [ ] Create `src/deploy.sh` — target `pi-four:/opt/shop-controller`
- [ ] Create `src/shop-controller.service` (systemd)
- [ ] Create `src/zigbee2mqtt-configuration.yaml` — `base_topic: zigbee-shop`, channel 20
- [ ] Create `src/zigbee2mqtt.service`
- [ ] Create `src/config.env.example` (no GPIO vars)
- [ ] Create `tests/` — 5 remote doors, no GPIO tests
- [ ] All tests passing
- [ ] Create `README.md`

## Phase 3 — Deploy
- [ ] Run `deploy.sh` → push to pi-four
- [ ] Install Z2M + Sonoff Zigbee dongle on pi-four
- [ ] Verify both services running

## Phase 4 — Pair Tilt Sensors
- [ ] Enable `permit_join` on Z2M (`zigbee-shop/bridge/request/permit_join`)
- [ ] Reset each sensor (pull battery, reinsert) — they were on the old ESP32-C6 coordinator
- [ ] Pair all 5 sensors, rename by IEEE address:
  - `0xffffb40e0601cc87` → `shop_door_1`
  - `0xffffb40e0601d4f7` → `shop_door_2`
  - `0xffffb40e06061cf2` → `shop_door_3`
  - `0xffffb40e06062fe8` → `shop_door_4`
  - `0xffffb40e0601d759` → `barn_door`
- [ ] Disable `permit_join`

## Phase 5 — HA Integration
- [ ] Verify 5 cover entities in HA under "Shop Controller"
- [ ] Test: press open/close → liftmaster relay fires
- [ ] Test: tilt sensor state reflects in cover entity
- [ ] Assign devices to HA Areas (Shop, Barn)

## Notes
- **No shop_door_1 on liftmaster yet** — user will add a DO; same PRESS pattern
- Pi-three Z2M channel: 25 → pi-four use channel 20
- Liftmaster button topics: `liftmaster/button/{name}/command` (PRESS)
- Same HiveMQ Cloud broker, same credentials
