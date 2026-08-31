from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from database.index import Base


class Thread(Base):
    __tablename__ = "threads"
    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(255))
    thread_name: Mapped[str] = mapped_column(String(255))
