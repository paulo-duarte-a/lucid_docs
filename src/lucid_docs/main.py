import os
import uuid
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI
from fastapi import Request, Response

from pythonjsonlogger import json as jsonlogger

from lucid_docs.routers import upload, query, authentication
from lucid_docs.core.config import settings
from lucid_docs.core.database import database


track_id_var: ContextVar[str] = ContextVar("track_id", default="-")


class PlainTextFormatter(logging.Formatter):
    """
    Custom formatter for plain text logs.
    """
    def format(self, record):
        if not hasattr(record, 'track_id'):
            record.track_id = track_id_var.get()

        log_fmt = "%(asctime)s - %(name)s - %(levelname)s - [track_id: %(track_id)s] - %(message)s"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds extra fields to the log record.
    """
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['track_id'] = track_id_var.get()
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        log_record['logger_name'] = record.name
        log_record['module'] = record.module
        log_record['funcName'] = record.funcName
        log_record['lineno'] = record.lineno


def setup_logging(log_level_str: str = "INFO", log_format: str = "plain"):
    """
    Set up logging configuration with the given log level and format.

    Args:
        log_level_str (str): Logging level as a string (default is "INFO").
        log_format (str): Format of the log output ("plain" or "json").
    """
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if log_format.lower() == "json":
        formatter = CustomJsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s %(track_id)s'
        )
    else:
        formatter = PlainTextFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").propagate = True
    logging.getLogger("fastapi").propagate = True


async def track_id_middleware(request: Request, call_next):
    """
    Middleware that assigns a unique track_id to each request for logging.

    Args:
        request (Request): The incoming request.
        call_next: Callable to process the next middleware or endpoint.

    Returns:
        Response: The response with a custom header indicating the track_id.
    """
    request_track_id = str(uuid.uuid4())
    token = track_id_var.set(request_track_id)

    response: Response = await call_next(request)
    response.headers["X-Track-ID"] = request_track_id

    track_id_var.reset(token)
    return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown operations.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    logging.basicConfig(level=logging.INFO)

    temp_path = Path(settings.TEMP_STORAGE_PATH)
    temp_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Temporary directory: {temp_path.absolute()}")

    chroma_path = Path(settings.CHROMA_PERSIST_DIR)
    chroma_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"ChromaDB directory: {chroma_path.absolute()}")

    try:
        await database.connect()
        logging.info("Database connection established")
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        raise

    yield

    await database.disconnect()
    logging.info("Application terminated")
    

LOG_FORMAT = os.getenv("LOG_FORMAT", "plain")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

setup_logging(log_level_str=LOG_LEVEL, log_format=LOG_FORMAT)

root_logger = logging.getLogger()
root_logger.info(f"Application starting with log format: {LOG_FORMAT} and log level: {LOG_LEVEL}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan
    )

    app.middleware("http")(track_id_middleware)

    app.include_router(upload.router)
    app.include_router(query.router)
    app.include_router(authentication.router)

    @app.get("/health")
    async def health_check():
        """
        Health check endpoint to confirm the service is running.
        """
        health_info = {
            "status": "ok",
            "services": {}
        }
        db_health = await database.health_check()
        health_info["services"]["database"] = db_health
        if not health_info["services"]["database"]:
            health_info["status"] = "degraded"
        return health_info

    return app