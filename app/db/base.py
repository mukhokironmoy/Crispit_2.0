from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path


# Creating the engine
DATABASE_URL = "sqlite:///crispit.db"
engine = create_engine(DATABASE_URL, echo=False)

# Defining the decalrative base
Base = declarative_base()

# Create session factory
SessionLocal = sessionmaker(bind=engine)