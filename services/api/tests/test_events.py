from unittest.mock import MagicMock, patch

import pytest
from api.events.access import reset_singletons
from api.events.bus_registry import BusRegistry
from api.events.consumers.rabbitmq import RabbitMQConsumer
from api.events.publisher import emit_message_created, publish_event


class TestEvents:
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        BusRegistry.set(backend="rabbitmq", config={"url": "amqp://guest:guest@localhost:5672/"})
        yield
        BusRegistry.clear()
        reset_singletons()

    @patch("api.events.access.MessageBusFactory.build_producer")
    def test_publish_event(self, mock_build_producer):
        mock_producer = MagicMock()
        mock_build_producer.return_value = mock_producer

        result = publish_event("test.event", {"data": "hit"})

        assert result is True
        mock_producer.publish.assert_called_once()
        args, kwargs = mock_producer.publish.call_args
        assert kwargs["topic"] == "test.event"
        assert kwargs["message"]["payload"]["data"] == "hit"

    @patch("api.events.access.MessageBusFactory.build_producer")
    def test_emit_message_created(self, mock_build_producer):
        mock_producer = MagicMock()
        mock_build_producer.return_value = mock_producer

        emit_message_created(1, 10, "patient", "Hello")

        mock_producer.publish.assert_called_once()
        args, kwargs = mock_producer.publish.call_args
        assert kwargs["topic"] == "message.created"
        assert kwargs["message"]["payload"]["message_id"] == 1

    @patch("pika.BlockingConnection")
    @patch("pika.URLParameters")
    def test_rabbitmq_consumer_connect(self, mock_params, mock_pika):
        consumer = RabbitMQConsumer()
        consumer.configure({"url": "amqp://test"})
        consumer.connect()

        assert consumer._connected is True
        mock_pika.assert_called_once()

    def test_consumer_handler_registration(self):
        consumer = RabbitMQConsumer()
        mock_handler = MagicMock()
        consumer.subscribe("test.topic", mock_handler)

        handlers = consumer.get_handlers("test.topic")
        assert mock_handler in handlers
