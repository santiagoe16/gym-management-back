from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
import pymysql

# Register pymysql as the MySQL driver
pymysql.install_as_MySQLdb()

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_normal_session():
    return Session( engine )

def get_session():
    with Session(engine) as session:
        yield session 