import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot


def _make_update() -> MagicMock:
    message = MagicMock()
    message.reply_text = AsyncMock()
    update = MagicMock()
    update.message = message
    return update


@pytest.mark.parametrize(
    ("handler", "expected_reply"),
    [
        (bot.start, "Welcome to Part-Time Intelligence!"),
        (
            bot.help,
            "Available commands:\n"
            "/start — Start the bot\n"
            "/help — Show help\n"
            "/music — Generate music",
        ),
        (bot.music, "Send me a positive prompt for the music."),
    ],
)
def test_command_replies(handler, expected_reply) -> None:
    update = _make_update()

    asyncio.run(handler(update, MagicMock()))

    update.message.reply_text.assert_awaited_once_with(expected_reply)


def test_main_registers_all_command_handlers(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-test-token")
    monkeypatch.setattr(bot, "load_dotenv", lambda *args, **kwargs: None)

    fake_application = MagicMock()
    fake_builder = MagicMock()
    fake_builder.token.return_value = fake_builder
    fake_builder.build.return_value = fake_application
    fake_application_class = MagicMock()
    fake_application_class.builder.return_value = fake_builder
    monkeypatch.setattr(bot, "Application", fake_application_class)

    bot.main()

    fake_builder.token.assert_called_once_with("fake-test-token")
    registered = {
        tuple(call.args[0].commands): call.args[0].callback
        for call in fake_application.add_handler.call_args_list
    }
    assert registered == {
        ("start",): bot.start,
        ("help",): bot.help,
        ("music",): bot.music,
    }
