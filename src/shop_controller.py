"""Shop door controller service: MQTT command forwarding + HA cover discovery.

Subscribes to MQTT door command topics and forwards PRESS commands to the
liftmaster-remote ESP32 via MQTT. No local GPIO — all doors are remote.
Publishes HA MQTT cover discovery configs and handles availability via LWT/birth messages.

Designed to run as a systemd service on a Raspberry Pi 4B.
"""

import json
import logging
import os
import socket
import sys
import time

import paho.mqtt.client as mqtt


# ---------------------------------------------------------------------------
# Configuration — loaded from environment by load_config(), called from main()
# ---------------------------------------------------------------------------

BROKER = ""
PORT = 8883
USER = ""
PASS = ""

# Constants (not configurable)
AVAIL_TOPIC = "shop-controller/status"

# Door definitions: (door_id, friendly_name, z2m_state_topic, remote_cmd_topic)
DOORS = [
    ("shop_door_1", "Shop Door 1", "zigbee-shop/shop_door_1", "liftmaster/button/shop_door_1/command"),
    ("shop_door_2", "Shop Door 2", "zigbee-shop/shop_door_2", "liftmaster/button/shop_door_2/command"),
    ("shop_door_3", "Shop Door 3", "zigbee-shop/shop_door_3", "liftmaster/button/shop_door_3/command"),
    ("shop_door_4", "Shop Door 4", "zigbee-shop/shop_door_4", "liftmaster/button/shop_door_4/command"),
    ("barn_door",   "Barn Door",   "zigbee-shop/barn_door",   "liftmaster/button/barn_door/command"),
]

# Command topics this service subscribes to (built from DOORS)
CMD_TOPICS = {f"shop-controller/button/{d[0]}/command": d for d in DOORS}

# Old discovery topics to clear on connect (prevents name stacking after renames)
_STALE_DISCOVERY = []

log = logging.getLogger(__name__)


def load_config():
    """Read configuration from environment variables."""
    global BROKER, PORT, USER, PASS

    BROKER = os.environ.get("MQTT_BROKER", "")
    PORT = int(os.environ.get("MQTT_PORT", "8883"))
    USER = os.environ.get("MQTT_USER", "")
    PASS = os.environ.get("MQTT_PASS", "")


# ---------------------------------------------------------------------------
# HA MQTT discovery
# ---------------------------------------------------------------------------

def publish_discovery(client):
    """Publish Home Assistant MQTT discovery configs for shop door covers."""
    device = {
        "ids": ["shop-controller"],
        "name": "Shop Controller",
        "mf": "Raspberry Pi",
        "mdl": "4B",
    }

    for door_id, door_name, state_topic, _remote_cmd in DOORS:
        config = {
            "unique_id": f"shop-controller-cover-{door_id}",
            "name": door_name,
            "device_class": "garage",
            "state_topic": state_topic,
            "value_template": "{{ 'closed' if value_json.contact else 'open' }}",
            "state_open": "open",
            "state_closed": "closed",
            "command_topic": f"shop-controller/button/{door_id}/command",
            "payload_open": "PRESS",
            "payload_close": "PRESS",
            "payload_stop": "PRESS",
            "optimistic": False,
            "availability_topic": AVAIL_TOPIC,
            "payload_available": "online",
            "payload_not_available": "offline",
            "icon": "mdi:barn" if door_id == "barn_door" else "mdi:garage",
            "device": device,
        }
        client.publish(
            f"homeassistant/cover/shop-controller/{door_id}/config",
            json.dumps(config),
            retain=True,
        )

    log.info("Published HA cover discovery configs for %d doors", len(DOORS))


# ---------------------------------------------------------------------------
# MQTT callbacks
# ---------------------------------------------------------------------------

def on_connect(client, userdata, connect_flags, reason_code, properties):
    """Handle MQTT connection — publish birth, subscribe, and send discovery."""
    if reason_code.is_failure:
        log.error("MQTT connection failed: %s", reason_code)
        return

    log.info("Connected to MQTT broker (rc=%s)", reason_code)

    # Birth message
    client.publish(AVAIL_TOPIC, "online", qos=1, retain=True)

    # Subscribe to all door command topics
    client.subscribe([(topic, 1) for topic in CMD_TOPICS])

    # Clear stale discovery topics from previous renames
    for topic in _STALE_DISCOVERY:
        client.publish(topic, payload=b"", qos=1, retain=True)
    if _STALE_DISCOVERY:
        log.info("Cleared %d stale discovery topics", len(_STALE_DISCOVERY))

    # Publish HA discovery configs
    publish_discovery(client)


def on_message(client, userdata, message):
    """Handle incoming MQTT messages — forward door commands to liftmaster-remote."""
    door = CMD_TOPICS.get(message.topic)
    if door is None:
        log.warning("Unknown topic: %s", message.topic)
        return

    door_id, door_name, _state_topic, remote_cmd = door
    log.info("%s: forwarding PRESS to %s", door_name, remote_cmd)
    client.publish(remote_cmd, "PRESS", qos=1)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Initialize and run the shop controller MQTT service."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    load_config()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"shop-controller-{socket.gethostname()}",
    )
    client.tls_set(ca_certs="/etc/ssl/certs/ca-certificates.crt")
    client.username_pw_set(USER, PASS)
    client.will_set(AVAIL_TOPIC, payload="offline", qos=1, retain=True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT)

    log.info("Starting MQTT loop — listening for door commands")
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    main()
