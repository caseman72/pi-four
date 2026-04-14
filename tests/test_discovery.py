"""Unit tests for HA cover discovery JSON."""

import json
import sys
from unittest.mock import MagicMock

import pytest


def _load_controller(env_vars):
    """Import shop_controller after env vars are set."""
    sys.modules.pop("src.shop_controller", None)
    from src import shop_controller
    shop_controller.load_config()
    return shop_controller


def _get_discovery_publishes(sc, client):
    """Call publish_discovery and return a dict of topic -> parsed JSON."""
    sc.publish_discovery(client)
    results = {}
    for c in client.publish.call_args_list:
        args, kwargs = c
        topic = args[0]
        payload = args[1] if len(args) > 1 else kwargs.get("payload")
        if isinstance(payload, str):
            results[topic] = json.loads(payload)
    return results


DOOR_IDS = ["shop_door_1", "shop_door_2", "shop_door_3", "shop_door_4", "barn_door"]


class TestPublishDiscovery:
    """Tests for publish_discovery() — cover discovery configs."""

    def test_publishes_discovery_for_all_5_doors(self, env_vars):
        """Publishes discovery config for each of the 5 doors."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        for door_id in DOOR_IDS:
            topic = f"homeassistant/cover/shop-controller/{door_id}/config"
            assert topic in publishes, f"Missing discovery for {door_id}"

    def test_discovery_retain_true(self, env_vars):
        """All discovery publishes use retain=True."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        sc.publish_discovery(client)

        for c in client.publish.call_args_list:
            _, kwargs = c
            assert kwargs.get("retain") is True

    def test_discovery_cover_has_required_fields(self, env_vars):
        """Cover discovery JSON contains all required fields."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        door = publishes["homeassistant/cover/shop-controller/shop_door_1/config"]
        required_fields = [
            "unique_id", "name", "device_class", "state_topic",
            "value_template", "state_open", "state_closed",
            "command_topic", "payload_open", "payload_close",
            "payload_stop", "optimistic", "availability_topic",
            "payload_available", "payload_not_available", "icon", "device",
        ]
        for field in required_fields:
            assert field in door, f"Missing field: {field}"

    def test_discovery_unique_ids(self, env_vars):
        """Each door has a unique_id prefixed with 'shop-controller-cover-'."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        for door_id in DOOR_IDS:
            door = publishes[f"homeassistant/cover/shop-controller/{door_id}/config"]
            assert door["unique_id"] == f"shop-controller-cover-{door_id}"

    def test_discovery_device_class_garage(self, env_vars):
        """All doors have device_class 'garage'."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        for door_id in DOOR_IDS:
            door = publishes[f"homeassistant/cover/shop-controller/{door_id}/config"]
            assert door["device_class"] == "garage"

    def test_discovery_state_topics(self, env_vars):
        """State topics point to zigbee-shop/{door_id}."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        for door_id in DOOR_IDS:
            door = publishes[f"homeassistant/cover/shop-controller/{door_id}/config"]
            assert door["state_topic"] == f"zigbee-shop/{door_id}"

    def test_discovery_command_topics(self, env_vars):
        """Command topics use shop-controller/button/{door_id}/command."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        for door_id in DOOR_IDS:
            door = publishes[f"homeassistant/cover/shop-controller/{door_id}/config"]
            assert door["command_topic"] == f"shop-controller/button/{door_id}/command"

    def test_discovery_payloads_all_press(self, env_vars):
        """payload_open, payload_close, payload_stop are all 'PRESS'."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        door = publishes["homeassistant/cover/shop-controller/shop_door_2/config"]
        assert door["payload_open"] == "PRESS"
        assert door["payload_close"] == "PRESS"
        assert door["payload_stop"] == "PRESS"

    def test_discovery_not_optimistic(self, env_vars):
        """optimistic is False."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        door = publishes["homeassistant/cover/shop-controller/shop_door_1/config"]
        assert door["optimistic"] is False

    def test_discovery_availability(self, env_vars):
        """availability_topic and payloads match expected values."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        door = publishes["homeassistant/cover/shop-controller/shop_door_1/config"]
        assert door["availability_topic"] == "shop-controller/status"
        assert door["payload_available"] == "online"
        assert door["payload_not_available"] == "offline"

    def test_discovery_device_object(self, env_vars):
        """Device object matches expected structure."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        door = publishes["homeassistant/cover/shop-controller/shop_door_1/config"]
        device = door["device"]
        assert device["ids"] == ["shop-controller"]
        assert device["name"] == "Shop Controller"
        assert device["mf"] == "Raspberry Pi"
        assert device["mdl"] == "4B"

    def test_discovery_barn_door_icon(self, env_vars):
        """Barn door uses mdi:barn icon, shop doors use mdi:garage."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        barn = publishes["homeassistant/cover/shop-controller/barn_door/config"]
        assert barn["icon"] == "mdi:barn"

        shop = publishes["homeassistant/cover/shop-controller/shop_door_1/config"]
        assert shop["icon"] == "mdi:garage"

    def test_discovery_value_template(self, env_vars):
        """value_template parses Z2M contact JSON."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        publishes = _get_discovery_publishes(sc, client)

        door = publishes["homeassistant/cover/shop-controller/shop_door_1/config"]
        assert "value_json.contact" in door["value_template"]
