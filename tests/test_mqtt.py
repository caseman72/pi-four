"""Unit tests for MQTT connect/subscribe/LWT."""

import sys
from unittest.mock import MagicMock, patch, call

import pytest
import paho.mqtt.client as mqtt


def _load_controller(env_vars):
    """Import shop_controller after env vars are set."""
    sys.modules.pop("src.shop_controller", None)
    from src import shop_controller
    shop_controller.load_config()
    return shop_controller


class TestMQTTClient:
    """Tests for MQTT client setup in main()."""

    def test_client_uses_version2_api(self, env_vars):
        """Client constructor called with mqtt.CallbackAPIVersion.VERSION2."""
        sc = _load_controller(env_vars)

        with patch("paho.mqtt.client.Client") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            try:
                sc.main()
            except Exception:
                pass

            MockClient.assert_called_once()
            args, kwargs = MockClient.call_args
            assert args[0] == mqtt.CallbackAPIVersion.VERSION2

    def test_client_sets_tls(self, env_vars):
        """client.tls_set called with ca_certs pointing to system CA bundle."""
        sc = _load_controller(env_vars)

        with patch("paho.mqtt.client.Client") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            try:
                sc.main()
            except Exception:
                pass

            mock_instance.tls_set.assert_called_once()

    def test_client_sets_lwt(self, env_vars):
        """will_set called with topic='shop-controller/status', payload='offline'."""
        sc = _load_controller(env_vars)

        with patch("paho.mqtt.client.Client") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            try:
                sc.main()
            except Exception:
                pass

            mock_instance.will_set.assert_called_once_with(
                "shop-controller/status", payload="offline", qos=1, retain=True
            )

    def test_client_uses_loop_forever(self, env_vars):
        """main() calls client.loop_forever(retry_first_connection=True)."""
        sc = _load_controller(env_vars)

        with patch("paho.mqtt.client.Client") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            sc.main()

            mock_instance.loop_forever.assert_called_once_with(
                retry_first_connection=True
            )


class TestOnConnect:
    """Tests for on_connect callback."""

    def test_on_connect_publishes_birth(self, env_vars):
        """on_connect publishes 'online' to 'shop-controller/status'."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        reason_code = MagicMock()
        reason_code.is_failure = False

        sc.on_connect(client, None, MagicMock(), reason_code, None)

        birth_calls = [c for c in client.publish.call_args_list
                      if c[0][0] == "shop-controller/status" and c[0][1] == "online"]
        assert len(birth_calls) >= 1

    def test_on_connect_subscribes_5_door_topics(self, env_vars):
        """on_connect subscribes to exactly 5 door command topics with QoS 1."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        reason_code = MagicMock()
        reason_code.is_failure = False

        sc.on_connect(client, None, MagicMock(), reason_code, None)

        client.subscribe.assert_called_once()
        sub_args = client.subscribe.call_args[0][0]
        assert len(sub_args) == 5, f"Expected 5 subscriptions, got {len(sub_args)}"
        topics = [t[0] for t in sub_args]
        assert "shop-controller/button/shop_door_1/command" in topics
        assert "shop-controller/button/shop_door_2/command" in topics
        assert "shop-controller/button/shop_door_3/command" in topics
        assert "shop-controller/button/shop_door_4/command" in topics
        assert "shop-controller/button/barn_door/command" in topics
        for t, qos in sub_args:
            assert qos == 1

    def test_on_connect_calls_publish_discovery(self, env_vars):
        """on_connect calls publish_discovery."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        reason_code = MagicMock()
        reason_code.is_failure = False

        with patch.object(sc, "publish_discovery") as mock_disc:
            sc.on_connect(client, None, MagicMock(), reason_code, None)
            mock_disc.assert_called_once_with(client)

    def test_on_connect_does_not_subscribe_z2m_topics(self, env_vars):
        """on_connect subscribe list does NOT contain any zigbee topic."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        reason_code = MagicMock()
        reason_code.is_failure = False

        sc.on_connect(client, None, MagicMock(), reason_code, None)

        client.subscribe.assert_called_once()
        sub_args = client.subscribe.call_args[0][0]
        topics = [t[0] for t in sub_args]
        for topic in topics:
            assert "zigbee" not in topic, f"Unexpected Z2M subscription: {topic}"

    def test_on_connect_skips_on_failure(self, env_vars):
        """If reason_code.is_failure is True, on_connect does not publish or subscribe."""
        sc = _load_controller(env_vars)
        client = MagicMock()
        reason_code = MagicMock()
        reason_code.is_failure = True

        sc.on_connect(client, None, MagicMock(), reason_code, None)

        client.publish.assert_not_called()
        client.subscribe.assert_not_called()
