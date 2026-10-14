import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from goreecloud_observability.runtime import Handler, parse_json_payload


class StrictRuntimeJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def post(self, payload):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request("POST", "/v1/signals", body=payload, headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def test_valid_nested_json_is_accepted_by_parser(self):
        self.assertEqual({"subject": {"action": "read"}}, parse_json_payload(b'{"subject":{"action":"read"}}'))

    def test_top_level_duplicate_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            parse_json_payload(b'{"authority":"one","authority":"other"}')

    def test_nested_duplicate_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            parse_json_payload(b'{"context":{"role":"viewer","role":"admin"}}')

    def test_non_finite_numbers_rejected(self):
        for value in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "non-finite"):
                    parse_json_payload(b'{"metric":' + value + b'}')

    def test_duplicate_input_is_rejected_over_http(self):
        status, response = self.post(b'{"request":{},"request":{}}')
        self.assertEqual(400, status)
        self.assertEqual("invalid_signal", response.get("error"))

    def test_non_finite_input_is_rejected_over_http(self):
        status, response = self.post(b'{"data":NaN}')
        self.assertEqual(400, status)
        self.assertEqual("invalid_signal", response.get("error"))


if __name__ == "__main__":
    unittest.main()
