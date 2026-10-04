import logging
import sys

_NOISY_LOGGERS = ("httpx", "httpcore", "telegram")


class BotLogger:
    """A small reusable wrapper around the standard logging module.

    Deliberately free of Telegram-specific logic so it can be reused by
    other backends (e.g. the music-generation backend).
    """

    FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        stream=None,
    ) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.propagate = False
        if not self._logger.handlers:
            handler = logging.StreamHandler(
                stream if stream is not None else sys.stdout
            )
            handler.setFormatter(
                logging.Formatter(self.FORMAT, datefmt=self.DATE_FORMAT)
            )
            self._logger.addHandler(handler)
        for noisy in _NOISY_LOGGERS:
            logging.getLogger(noisy).setLevel(logging.WARNING)

    def info(self, message: str, *args) -> None:
        self._logger.info(message, *args)

    def warning(self, message: str, *args) -> None:
        self._logger.warning(message, *args)

    def error(self, message: str, *args) -> None:
        self._logger.error(message, *args)

    def exception(self, message: str, *args, **kwargs) -> None:
        self._logger.exception(message, *args, **kwargs)
