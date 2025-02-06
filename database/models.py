from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    username = Column(String)
    full_name = Column(String)
    is_admin = Column(Boolean, default=False)
    penalty_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

class Attendance(Base):
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)  # present, absent, excused
    points_penalty = Column(Integer, default=0) 