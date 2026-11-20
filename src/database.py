
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Load database credentials from the .env file
load_dotenv()

# Read database settings
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_database_engine():
    """
    Create a SQLAlchemy connection engine for PostgreSQL.
    """

    required_settings = {
        "DB_HOST": DB_HOST,
        "DB_PORT": DB_PORT,
        "DB_NAME": DB_NAME,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD
    }

    missing_settings = [
        name
        for name, value in required_settings.items()
        if not value or not value.strip()
    ]

    if missing_settings:
        raise ValueError(
            f"Missing database settings: {', '.join(missing_settings)}"
        )

    # Validate PostgreSQL port
    try:
        database_port = int(DB_PORT)
    except (TypeError, ValueError):
        raise ValueError("DB_PORT must be a valid integer.")

    if not 1 <= database_port <= 65535:
        raise ValueError("DB_PORT must be between 1 and 65535.")

    # Safely construct the database URL
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=database_port,
        database=DB_NAME
    )

    # Create an engine with connection health checks
    engine = create_engine(
        database_url,
        pool_pre_ping=True
    )

    return engine


def test_database_connection():
    """
    Test whether Python can connect to PostgreSQL.
    """

    engine = None

    try:
        engine = get_database_engine()

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("Successfully connected to PostgreSQL!")
        return True

    except Exception as error:
        print(f"Database connection failed: {error}")
        return False

    finally:
        if engine is not None:
            engine.dispose()
