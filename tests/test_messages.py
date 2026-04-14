"""Unit tests for MQTT message handling — command forwarding."""

import sys
import time
from unittest.mock import MagicMock, patch

import pytest


def _load_controller(env_vars):
    """Import shop_controller after env vars are set."""
    sys.modules.pop("src.shop_controller", None)
    from src import shop_controller
    shop_controller.load_config()
    return shop_controller


class TestOnMessage:
    """Tests for on_message callback — all doors forward to liftmaster-remote."""

    def test_shop_door_1_forwards_to_liftmaster(self, env_vars):
        """shop_door_1 command forwards PRESS to liftmaster."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "shop-controller/button/shop_door_1/command"

        sc.on_message(client, None, msg)

        client.publish.assert_called_once_with(
            "liftmaster/button/shop_door_1/command", "PRESS", qos=1
        )

    def test_shop_door_2_forwards_to_liftmaster(self, env_vars):
        """shop_door_2 command forwards PRESS to liftmaster."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "shop-controller/button/shop_door_2/command"

        sc.on_message(client, None, msg)

        client.publish.assert_called_once_with(
            "liftmaster/button/shop_door_2/command", "PRESS", qos=1
        )

    def test_shop_door_3_forwards_to_liftmaster(self, env_vars):
        """shop_door_3 command forwards PRESS to liftmaster."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "shop-controller/button/shop_door_3/command"

        sc.on_message(client, None, msg)

        client.publish.assert_called_once_with(
            "liftmaster/button/shop_door_3/command", "PRESS", qos=1
        )

    def test_shop_door_4_forwards_to_liftmaster(self, env_vars):
        """shop_door_4 command forwards PRESS to liftmaster."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "shop-controller/button/shop_door_4/command"

        sc.on_message(client, None, msg)

        client.publish.assert_called_once_with(
            "liftmaster/button/shop_door_4/command", "PRESS", qos=1
        )

    def test_barn_door_forwards_to_liftmaster(self, env_vars):
        """barn_door command forwards PRESS to liftmaster."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "shop-controller/button/barn_door/command"

        sc.on_message(client, None, msg)

        client.publish.assert_called_once_with(
            "liftmaster/button/barn_door/command", "PRESS", qos=1
        )

    def test_unknown_topic_does_not_forward(self, env_vars):
        """Unknown topic does not publish anything."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        msg = MagicMock()
        msg.topic = "shop-controller/button/unknown_door/command"

        sc.on_message(client, None, msg)

        client.publish.assert_not_called()
