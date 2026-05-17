from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=True)
    github_id = Column(String(100), unique=True, nullable=True)

    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
