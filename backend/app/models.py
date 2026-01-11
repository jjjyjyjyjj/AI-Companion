from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, Time, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()

# == Enums
class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "companion"
    SYSTEM = "system"       

class SessionStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED" 

class PomodoroPhase(enum.Enum):
    WORK = "WORK"
    BREAK = "BREAK"


# == Models
class Client(Base):
    __tablename__ = 'client'
    
    client_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_name = Column(String(20))
    
    # Relationships
    sessions = relationship("Session", back_populates="client")
    # chat_history = relationship("ChatHistory", back_populates="client")

class Session(Base):
    __tablename__ = "session"
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client.client_id"), nullable=False)

    session_topic = Column(Text)
    duration = Column(Time)
    status = Column(SQLEnum(SessionStatus, name="session_status"), default=SessionStatus.ACTIVE)

    seconds_focused = Column(Integer, default=0)
    seconds_distracted = Column(Integer, default=0)
    avg_attention = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    client = relationship("Client", back_populates="sessions")
    # chat_history = relationship("ChatHistory", back_populates="session")
    # plan = relationship("Plan", back_populates="session", uselist=False)
    telemetry_events = relationship("TelemetryEvent", back_populates="session")

# class ChatHistory(Base):
#     __tablename__ = 'chathistory'
    
#     chat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     client_id = Column(UUID(as_uuid=True), ForeignKey('client.client_id'))
#     role = Column(SQLEnum(MessageRole, name='message_role'))
#     session_id = Column(UUID(as_uuid=True), ForeignKey('session.session_id'))
#     chat_log = Column(Text)
    
#     # Relationships
#     client = relationship("Client", back_populates="chat_history")
#     session = relationship("Session", back_populates="chat_history")    

# class Plan(Base):
#     __tablename__ = 'plans'
    
#     session_id = Column(UUID(as_uuid=True), ForeignKey('session.session_id', ondelete='CASCADE'), primary_key=True)
#     pomodoro_pattern = Column(Text)
#     qualitative_guide = Column(Text)
#     updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
#     # Relationships
#     session = relationship("Session", back_populates="plan")

# class PomodoroCycle(Base):
#     __tablename__ = 'pomodoro_cycles'
    
#     cycle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     session_id = Column(UUID(as_uuid=True), ForeignKey('session.session_id'))
#     phase = Column(SQLEnum(PomodoroPhase, name='pomodoro_phase'))
#     total_duration = Column(Integer)
#     started_at = Column(DateTime(timezone=True))
#     ended_at = Column(DateTime(timezone=True), nullable=True)
#     completed = Column(Boolean, default=False)
    
#     # Relationships
#     session = relationship("Session", back_populates="pomodoro_cycles")

class TelemetryEvent(Base):
    __tablename__ = 'telemetry_events'
    
    telemetry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("session.session_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="telemetry_events")    