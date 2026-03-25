"""
SmartBudget — централізований модуль логування.

Налаштовує Python logging для всього застосунку:
- Рівень логування задається через змінну оточення LOG_LEVEL
- Два обробники: консоль (stdout) та файл з ротацією
- Структурований формат: час | рівень | модуль | повідомлення
- Унікальні ідентифікатори помилок (error_id) для швидкого пошуку

Usage:
    from logger import get_logger, log_error
    logger = get_logger(__name__)
    logger.info("Something happened")
    log_error(logger, exc, context={"user": 1})
"""

import logging
import os
import traceback
import uuid
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

LOG_DIR = os.environ.get("LOG_DIR", "logs")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", 5 * 1024 * 1024))
LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "5"))

_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _ensure_log_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(_FMT, datefmt=_DATE_FMT)


def setup_logging() -> None:
    """
    Ініціалізувати глобальну систему логування.

    Викликається один раз під час старту застосунку (app.py).
    Рівень логування береться зі змінної оточення LOG_LEVEL
    (DEBUG / INFO / WARNING / ERROR / CRITICAL). За замовчуванням INFO.

    Обробники:
        - StreamHandler  → stdout (завжди увімкнений)
        - RotatingFileHandler → logs/smartbudget.log (5 MB × 5 файлів)
        - TimedRotatingFileHandler → logs/errors.log (щодня, 30 днів)
    """
    _ensure_log_dir()

    numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
    formatter = _build_formatter()

    root = logging.getLogger()
    root.setLevel(numeric_level)

    if root.handlers:
        return

    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    main_handler = RotatingFileHandler(
        filename=os.path.join(LOG_DIR, "smartbudget.log"),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    main_handler.setLevel(numeric_level)
    main_handler.setFormatter(formatter)
    root.addHandler(main_handler)

    error_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "errors.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root.addHandler(error_handler)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    root.info(
        "Logging initialised | level=%s | dir=%s | handlers=console,file,errors",
        LOG_LEVEL, LOG_DIR,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Повернути іменований логер.

    Args:
        name: зазвичай передають __name__ модуля.

    Returns:
        logging.Logger: налаштований логер.
    """
    return logging.getLogger(name)

def log_error(
    logger: logging.Logger,
    exc: Exception,
    context: dict | None = None,
    message: str = "Unexpected error",
) -> str:
    """
    Залогувати виняток з унікальним ідентифікатором та контекстом.

    Генерує error_id (UUID4) для кожної помилки — він потрапляє як
    у лог, так і повертається викликачу, щоб його можна було показати
    користувачеві або передати в службу підтримки.

    Args:
        logger: логер модуля, де виникла помилка.
        exc:    перехоплений виняток.
        context: довільний словник з додатковою інформацією
                 (наприклад, {"user_id": 1, "route": "/expenses"}).
        message: коротке людино-читане пояснення події.

    Returns:
        str: унікальний ідентифікатор помилки (error_id).

    Example:
        try:
            ...
        except Exception as e:
            eid = log_error(logger, e, context={"route": request.path})
            return render_error(eid), 500
    """
    error_id = str(uuid.uuid4())[:8].upper()
    ctx_str = " | ".join(f"{k}={v}" for k, v in (context or {}).items())

    logger.error(
        "%s | error_id=%s | type=%s | %s\n%s",
        message,
        error_id,
        type(exc).__name__,
        ctx_str,
        traceback.format_exc(),
    )
    return error_id
