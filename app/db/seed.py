from pathlib import Path
from .base import SessionLocal
from .models import ProcessingModes, DefaultNotesModes
from app.config.logging import logger


def seed_default_notes_modes():
    session = SessionLocal()

    # Load prompts safely
    PROMPT_01 = Path(r"data\prompts\01_Crispit_Default_txt.txt").read_text(encoding="utf-8")
    PROMPT_02 = Path(r"data\prompts\02_Crispit_Default_pdf.txt").read_text(encoding="utf-8")
    PROMPT_03 = Path(r"data\prompts\03_Crispit_Default_pdf_long.txt").read_text(encoding="utf-8")

    if session.query(DefaultNotesModes).count() == 0:
        default_modes = [
            ("Crispit (Text)", PROMPT_01, "txt", "note_mode:1"),
            ("Crispit (Fit to 1 page)", PROMPT_02, "pdf","note_mode:2"),
            ("Crispit (Detailed pdf)", PROMPT_03, "pdf","note_mode:3"),
        ]

        try:
            for name, prompt, output_type, callback_data in default_modes:
                session.add(
                    DefaultNotesModes(
                        name=name,
                        prompt=prompt,
                        output_type=output_type,
                        callback_data=callback_data
                    )
                )
            session.commit()
            logger.info("🌱 DefaultNotesModes seeded.")
        except Exception as e:
            session.rollback()
            logger.exception(f"Error seeding DefaultNotesModes: {e}")
    else:
        logger.info("🌱 DefaultNotesModes already seeded. No reseeding required.")

    session.close()



def seed_batch_modes():
    session = SessionLocal()

    if session.query(ProcessingModes).count() == 0:
        default_modes = [
            ("Single", "Each summary returned as a separate document", "pr_mode:single"),
            ("Batch (Default)", "All summaries merged into one document", "pr_mode:batch_default"),
            ("Batch (One per page/text)", "Each summary fit into one page.", "pr_mode:batch_1pp")
        ]

        try:
            for name, desc, callback_data in default_modes:
                session.add(ProcessingModes(name=name, description=desc, callback_data=callback_data))
            session.commit()
            logger.info("🌱 BatchModes seeded.")
        except Exception as e:
            session.rollback()
            logger.exception(f"Error seeding BatchModes: {e}")
    else:
        logger.info("🌱 BatchModes already seeded. No reseeding required.")

    session.close()
