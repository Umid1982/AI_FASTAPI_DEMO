from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DetectionType(str, Enum):
    """Types of detected objects."""
    PERSON = "person"
    CAR = "car"
    BAG = "bag"
    PHONE = "phone"


class TrackingStatus(str, Enum):
    """Tracking status for objects."""
    ACTIVE = "active"
    LOST = "lost"
    REMOVED = "removed"


class VideoSourceType(str, Enum):
    """Video source types."""
    WEBCAM = "webcam"
    RTSP = "rtsp"
    FILE = "file"


# Detection and Tracking Models
class BoundingBox(BaseModel):
    """Bounding box coordinates."""
    x1: float = Field(..., description="Top-left x coordinate")
    y1: float = Field(..., description="Top-left y coordinate")
    x2: float = Field(..., description="Bottom-right x coordinate")
    y2: float = Field(..., description="Bottom-right y coordinate")
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1
    
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


class Detection(BaseModel):
    """Single object detection."""
    class_id: int = Field(..., description="YOLO class ID")
    class_name: str = Field(..., description="Class name")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")


class TrackedObject(BaseModel):
    """Tracked object with ID."""
    id: str = Field(..., description="Unique object ID")
    track_id: int = Field(..., description="Unique tracking ID")
    detection: Detection = Field(..., description="Current detection")
    status: TrackingStatus = Field(default=TrackingStatus.ACTIVE, description="Tracking status")
    first_seen: datetime = Field(default_factory=datetime.now, description="First detection time")
    last_seen: datetime = Field(default_factory=datetime.now, description="Last detection time")
    total_detections: int = Field(default=1, description="Total detection count")
    duration: float = Field(default=0.0, description="Duration in seconds")
    is_active: bool = Field(default=True, description="Whether object is currently active")
    
    @property
    def calculated_duration(self) -> float:
        """Duration in seconds since first seen."""
        return (self.last_seen - self.first_seen).total_seconds()


class VideoFrame(BaseModel):
    """Video frame with detections."""
    timestamp: datetime = Field(default_factory=datetime.now, description="Frame timestamp")
    frame_number: int = Field(..., description="Frame number in sequence")
    detections: List[Detection] = Field(default_factory=list, description="Detected objects")
    tracked_objects: List[TrackedObject] = Field(default_factory=list, description="Tracked objects")


# Analytics Models
class HeatmapPoint(BaseModel):
    """Heatmap data point."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    intensity: float = Field(..., ge=0, description="Heat intensity")
    timestamp: datetime = Field(default_factory=datetime.now, description="Detection time")


class AnalyticsData(BaseModel):
    """Analytics data for a session."""
    session_id: str = Field(..., description="Unique session identifier")
    start_time: datetime = Field(..., description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    total_frames: int = Field(default=0, description="Total processed frames")
    total_people: int = Field(default=0, description="Total unique people detected")
    peak_people_count: int = Field(default=0, description="Peak people count")
    average_stay_time: float = Field(default=0.0, description="Average stay time in seconds")
    heatmap_points: List[HeatmapPoint] = Field(default_factory=list, description="Heatmap data")
    peak_hours: List[str] = Field(default_factory=list, description="Peak activity hours")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# API Request/Response Models
class VideoAnalysisRequest(BaseModel):
    """Request to start video analysis."""
    source_type: VideoSourceType = Field(..., description="Video source type")
    source_path: Optional[str] = Field(None, description="Path to video file or RTSP URL")
    duration: Optional[int] = Field(None, ge=1, description="Analysis duration in seconds")
    confidence_threshold: Optional[float] = Field(None, ge=0, le=1, description="Detection confidence threshold")


class VideoAnalysisResponse(BaseModel):
    """Response from video analysis."""
    session_id: str = Field(..., description="Analysis session ID")
    status: str = Field(..., description="Analysis status")
    message: str = Field(..., description="Status message")
    analytics: Optional[AnalyticsData] = Field(None, description="Analytics data")


class ReportRequest(BaseModel):
    """Request to generate report."""
    session_id: str = Field(..., description="Session ID to generate report for")
    report_type: str = Field(default="summary", description="Type of report to generate")
    include_heatmap: bool = Field(default=True, description="Include heatmap data")
    include_timeline: bool = Field(default=True, description="Include timeline data")


class ReportResponse(BaseModel):
    """Generated report response."""
    session_id: str = Field(..., description="Session ID")
    report_type: str = Field(..., description="Report type")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation time")
    summary: str = Field(..., description="AI-generated summary")
    analytics: AnalyticsData = Field(..., description="Analytics data")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw analytics data")


# Error Models
class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False, description="Success status")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")


class SuccessResponse(BaseModel):
    """Success response model."""
    success: bool = Field(default=True, description="Success status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
