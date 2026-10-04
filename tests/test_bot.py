import asyncio
import io
import logging
import re
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot
from logger import BotLogger

BOT_LOGGER_NAME = "telegram_media_bot"


def _make_update() -> MagicMock:
    message = MagicMock()
    message.reply_text = AsyncMock()
    update = MagicMock()
    update.message = message
    return update


class _RecordCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def _collect_bot_logs():
    collector = _RecordCollector()
    bot_logger = logging.getLogger(BOT_LOGGER_NAME)
    bot_logger.addHandler(collector)
    try:
        yield collector
    finally:
        bot_logger.removeHandler(collector)


def _logged_messages(collector: _RecordCollector):
    return [(record.levelname, record.getMessage()) for record in collector.records]


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


@pytest.mark.parametrize(
    ("handler", "command"),
    [
        (bot.start, "/start"),
        (bot.help, "/help"),
        (bot.music, "/music"),
    ],
)
def test_command_handlers_log_receipt_and_response(handler, command) -> None:
    with _collect_bot_logs() as collector:
        update = _make_update()
        asyncio.run(handler(update, MagicMock()))

    messages = _logged_messages(collector)
    assert ("INFO", f"Command received: {command}") in messages
    assert ("INFO", f"Response sent: {command}") in messages


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

    with _collect_bot_logs() as collector:
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
    fake_application.add_error_handler.assert_called_once_with(bot.on_error)

    messages = _logged_messages(collector)
    assert ("INFO", "Bot backend started") in messages
    assert all("fake-test-token" not in message for _, message in messages)


def test_error_handler_logs_unexpected_exception() -> None:
    context = MagicMock()
    try:
        raise RuntimeError("kaboom")
    except RuntimeError as exc:
        context.error = exc

    with _collect_bot_logs() as collector:
        asyncio.run(bot.on_error(MagicMock(), context))

    messages = _logged_messages(collector)
    assert ("ERROR", "Unexpected error while handling update: kaboom") in messages
    error_record = collector.records[-1]
    assert error_record.exc_info is not None
    assert isinstance(error_record.exc_info[1], RuntimeError)


def test_bot_logger_format_includes_timestamp_and_level() -> None:
    buffer = io.StringIO()
    test_logger = BotLogger("format-test-logger", stream=buffer)

    test_logger.info("hello world")

    assert re.search(
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[INFO\] hello world$",
        buffer.getvalue(),
        re.MULTILINE,
    )


@pytest.mark.parametrize(
    ("method", "level"),
    [("info", "INFO"), ("warning", "WARNING"), ("error", "ERROR")],
)
def test_bot_logger_levels(method, level) -> None:
    buffer = io.StringIO()
    test_logger = BotLogger(f"level-test-{method}", stream=buffer)

    getattr(test_logger, method)("payload")

    assert f"[{level}] payload" in buffer.getvalue()


def test_bot_logger_exception_includes_traceback() -> None:
    buffer = io.StringIO()
    test_logger = BotLogger("exception-test-logger", stream=buffer)

    try:
        raise ValueError("boom")
    except ValueError:
        test_logger.exception("operation failed")

    output = buffer.getvalue()
    assert "[ERROR] operation failed" in output
    assert "ValueError: boom" in output
    assert "Traceback" in output


def test_bot_logger_mutes_noisy_library_loggers() -> None:
    BotLogger("muted-test-logger")

    for name in ("httpx", "httpcore", "telegram"):
        assert logging.getLogger(name).level >= logging.WARNING
