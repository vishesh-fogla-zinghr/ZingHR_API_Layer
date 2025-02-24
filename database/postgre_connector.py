# app/database/cockroach_connector.py

# --- Begin CockroachDB version patch ---
import sqlalchemy.dialects.postgresql.psycopg2 as pg_dialect

def postgre_get_server_version_info(self, connection):
    # Return a fixed version tuple.
    # You can adjust this tuple if needed.
    return (25, 1, 0)

# Override the default method with our patch.
pg_dialect.PGDialect_psycopg2._get_server_version_info = postgre_get_server_version_info
# --- End CockroachDB version patch ---

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
#from app.config import settings

# Build the connection URL for CockroachDB (in insecure mode).
# COCKROACH_DATABASE_URL = (
#     f"postgresql+psycopg2://{settings.COCKROACH_USER}:{settings.COCKROACH_PASSWORD}@{settings.COCKROACH_HOST}:{settings.COCKROACH_PORT}/{settings.COCKROACH_DB}?sslmode=disable"
# )

POSTGRE_DATABASE_URL = ()

cockroach_engine = create_engine(POSTGRE_DATABASE_URL, echo=True)

def test_cockroach_connection():
    try:
        with cockroach_engine.connect() as connection:
            print("✅ Successfully connected to database!")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
    
CockroachSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cockroach_engine)
CockroachBase = declarative_base()

test_cockroach_connection()
 