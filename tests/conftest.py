"""Shared pytest fixtures for shop-controller tests."""

import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_mqtt_client():
    """Return a MagicMock that mocks paho.mqtt.client.Client."""
    client = MagicMock()
    client.publish = MagicMock()
    client.subscribe = MagicMock()
    client.will_set = MagicMock()
    client.tls_set = MagicMock()
    client.username_pw_set = MagicMock()
    client.connect = MagicMock()
    client.loop_forever = MagicMock()
    client.on_connect = None
    client.on_message = None
    return client


@pytest.fixture
def env_vars(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("MQTT_BROKER", "test.broker")
    monkeypatch.setenv("MQTT_PORT", "8883")
    monkeypatch.setenv("MQTT_USER", "testuser")
    monkeypatch.setenv("MQTT_PASS", "testpass")
