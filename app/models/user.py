from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.client_id"), nullable=False, unique=True)
    created_at = Column(Date, nullable=False, default=date.today)

    client = relationship("Client")