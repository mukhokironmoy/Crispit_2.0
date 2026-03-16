from .base import Base, engine
from .models import *
from .seed import seed_batch_modes, seed_default_notes_modes
from app.config.logging import logger

def init_db():
    logger.info("🚀 Initializing database...")

    # Create all tables
    Base.metadata.create_all(engine)

    # Seed the default notes modes
    seed_default_notes_modes()

    # Seed the batch modes
    seed_batch_modes()

    logger.info("✅ Database ready!")

if __name__ == "__main__":
    init_db()