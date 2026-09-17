import unittest
from unittest.mock import patch

from telegram_bot.telegram_engine import TelegramEngine


class FakeAPI:
    def __init__(self):
        self.messages = []

    def send_message(self, text):
        self.messages.append(text)
        return True

    def send_photo_with_caption(self, image_path, caption):
        raise AssertionError("image output is outside phase 2")


class NoImageEngine:
    def generate(self, event_type, trade):
        raise RuntimeError("image unavailable")


class TelegramPhase2Tests(unittest.TestCase):
    def test_send_signal_accepts_extra_text_and_reuses_injected_api(self):
        api = FakeAPI()
        engine = TelegramEngine(api=api, images=NoImageEngine())

        with patch("telegram_bot.telegram_engine.build_message", return_value="base signal"):
            engine.send_signal({"symbol": "SPY"}, extra_text="reason one")

        self.assertEqual(api.messages, ["base signal\n\nreason one"])
        self.assertIs(engine.api, api)


if __name__ == "__main__":
    unittest.main()
