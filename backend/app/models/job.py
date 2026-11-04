import uuid
from sqlalchemy import BigInteger,DateTime,String,Text,func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False,unique=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_byte:Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="uploaded")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(),nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(),nullable=False)