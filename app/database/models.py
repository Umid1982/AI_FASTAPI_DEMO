from sqlalchemy import Column, String, DateTime, Integer, Float, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class VideoSession(Base):
    __tablename__ = "video_sessions"
    
    id = Column(String, primary_key=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="active")
    source_type = Column(String, nullable=False)
    source_path = Column(String, nullable=True)
    total_frames = Column(Integer, default=0)
    processed_frames = Column(Integer, default=0)
    detections_count = Column(Integer, default=0)
    total_people = Column(Integer, default=0)
    peak_people_count = Column(Integer, default=0)
    average_stay_time = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    detections = relationship("Detection", back_populates="session", cascade="all, delete-orphan")
    tracked_objects = relationship("TrackedObject", back_populates="session", cascade="all, delete-orphan")
    heatmap_points = relationship("HeatmapPoint", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="session", cascade="all, delete-orphan")

class Detection(Base):
    __tablename__ = "detections"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("video_sessions.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    class_name = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_width = Column(Float, nullable=False)
    bbox_height = Column(Float, nullable=False)
    
    # Relationships
    session = relationship("VideoSession", back_populates="detections")

class TrackedObject(Base):
    __tablename__ = "tracked_objects"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("video_sessions.id"), nullable=False)
    track_id = Column(Integer, nullable=False)
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_detections = Column(Integer, default=1)
    duration = Column(Float, default=0.0)  # Duration in seconds
    is_active = Column(Boolean, default=True)
    
    # Relationships
    session = relationship("VideoSession", back_populates="tracked_objects")

class HeatmapPoint(Base):
    __tablename__ = "heatmap_points"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("video_sessions.id"), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    intensity = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    session = relationship("VideoSession", back_populates="heatmap_points")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("video_sessions.id"), nullable=False)
    report_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    session = relationship("VideoSession", back_populates="reports")
