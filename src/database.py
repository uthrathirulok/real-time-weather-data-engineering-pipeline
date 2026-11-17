
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
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
        name for name, value in required_settings.items()
        if not value
    ]

    if missing_settings:
        raise ValueError(
            f"Missing database settings: {', '.join(missing_settings)}"
        )

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME
    )

    engine = create_engine(database_url)

    return engine


def test_database_connection():
    """
    Test whether Python can connect to PostgreSQL.
    """

    try:
        engine = get_database_engine()

        with engine.connect() as connection:
            print("Successfully connected to PostgreSQL!")

        engine.dispose()
        return True

    except Exception as error:
        print(f"Database connection failed: {error}")
        return False
