# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .env import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
  engine = create_engine(str(settings.DATABASE_URL))
  db = sessionmaker(bind=engine)()
  try:
      yield db
  finally:
      db.close()
