import logging
import unittest
from unittest.mock import Mock

from api.navidrome_client import NavidromeClient
from core.context import AppContext


class AppContextConnectionTests(unittest.TestCase):
    def test_connection_callback_receives_the_validated_client(self):
        context = AppContext(settings=Mock(), logger=logging.getLogger(__name__))
        callback = Mock()
        client = Mock(spec=NavidromeClient)

        context.set_connection_services_callback(callback)
        context.replace_connection_services_callback(client)

        callback.assert_called_once_with(client)

    def test_connection_callback_must_be_configured(self):
        context = AppContext(settings=Mock(), logger=logging.getLogger(__name__))

        with self.assertRaisesRegex(RuntimeError, "handler is not configured"):
            context.replace_connection_services_callback(Mock(spec=NavidromeClient))


if __name__ == "__main__":
    unittest.main()
