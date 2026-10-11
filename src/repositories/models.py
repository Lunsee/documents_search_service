from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rubrics: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
