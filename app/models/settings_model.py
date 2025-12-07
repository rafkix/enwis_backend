from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    language = Column(String, default="en")
    notification = Column(Boolean, default=True)
    dark_mode = Column(Boolean, default=False)

    user = relationship("User", back_populates="settings")
