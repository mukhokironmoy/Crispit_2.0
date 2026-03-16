from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, DateTime, TIMESTAMP, UniqueConstraint, select, union_all, literal
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    current_mode_callback = Column(String, default="note_mode:1")
    current_processing = Column(String, default="Single")

    # Relationships
    note_modes = relationship("NotesModes", back_populates="user", cascade="all, delete-orphan")
    video_requests = relationship("VideoRequests", back_populates="user", cascade="all, delete-orphan")

class DefaultNotesModes(Base):
    __tablename__ = "default_notes_modes"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    prompt = Column(Text, nullable=False, default="Summarise the following and give in a crisp bulleted manner.")
    output_type = Column(Enum("pdf","txt", name="global_output_type_enum"),default="pdf", nullable=False)
    callback_data = Column(String, nullable=False, unique=True)    


class NotesModes(Base):
    __tablename__ = "notes_modes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    prompt = Column(Text, nullable=False, default="Summarise the following and give in a crisp bulleted manner in under 2500 characters. No fluff. Give only the required output.")
    output_type = Column(Enum("pdf","txt", name="output_type_enum"),default="txt", nullable=False)
    callback_data = Column(String, nullable=False, unique=True)    

    # Relationships
    user = relationship("User", back_populates="note_modes")

    __table_args__ = (UniqueConstraint("user_id", "name"),)

    # method to get the name for a given callback
    @classmethod
    def get_name_for_callback(cls, session, user_id, callback_data):
        user_mode = (
            select(cls.name)
            .where(
                cls.user_id == user_id,
                cls.callback_data == callback_data,
            )
        )

        default_mode = (
            select(DefaultNotesModes.name)
            .where(DefaultNotesModes.callback_data == callback_data)
        )

        result = session.execute(
            union_all(user_mode, default_mode).limit(1)
        ).scalar_one_or_none()

        return result
    
    # method to get the output for a given callback
    @classmethod
    def get_output_for_callback(cls, session, user_id, callback_data):
        user_mode = (
            select(cls.output_type)
            .where(
                cls.user_id == user_id,
                cls.callback_data == callback_data,
            )
        )

        default_mode = (
            select(DefaultNotesModes.output_type)
            .where(DefaultNotesModes.callback_data == callback_data)
        )

        result = session.execute(
            union_all(user_mode, default_mode).limit(1)
        ).scalar_one_or_none()

        return result

    # method to get the prompt for a given callback 
    @classmethod
    def get_prompt_for_callback(cls, session, user_id, callback_data):
        user_mode = (
            select(cls.prompt)
            .where(
                cls.user_id == user_id,
                cls.callback_data == callback_data,
            )
        )

        default_mode = (
            select(DefaultNotesModes.prompt)
            .where(DefaultNotesModes.callback_data == callback_data)
        )

        result = session.execute(
            union_all(
                user_mode,
                default_mode
            ).limit(1)
        ).scalar_one_or_none()

        return result


class ProcessingModes(Base):
    __tablename__ = "processing_modes"

    id = Column(Integer, primary_key=True)
    name = Column(Enum("Single","Batch (Default)","Batch (One per page/text)", name="processing_mode_name"), nullable=False, unique=True)
    description = Column(Text)
    callback_data = Column(String, nullable=False)

class VideoRequests(Base):
    __tablename__ = "video_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Text, nullable=False)
    mode_used = Column(String, default=None)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    transcript_path = Column(Text, default=None, nullable=True)
    notes_path = Column(Text, default=None, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)


    # Relationships
    user = relationship("User", back_populates="video_requests")

class ReusableRequests(Base):
    __tablename__ = "reusable_requests"

    id = Column(Integer, primary_key=True)
    video_id = Column(Text, nullable=False)
    type = Column(Enum("Transcript", "Notes", name="file_type_enum"), nullable=False)
    mode = Column(String, default=None)
    file_path = Column(String, nullable=False)

    __table_args__ = (
    UniqueConstraint("video_id", "type", "mode", name="uq_common_file_map"),
    )






