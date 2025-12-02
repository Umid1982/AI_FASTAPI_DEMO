import cv2
from abc import ABC, abstractmethod
from typing import Generator, Optional, Tuple
import structlog
from app.core.config import settings
from app.models.schemas import VideoSourceType

logger = structlog.get_logger()


class VideoSource(ABC):
    """Abstract base class for video sources."""
    
    @abstractmethod
    def get_frames(self) -> Generator[Tuple[bool, cv2.Mat], None, None]:
        """Get video frames generator."""
        pass
    
    @abstractmethod
    def release(self) -> None:
        """Release video source."""
        pass
    
    @abstractmethod
    def is_opened(self) -> bool:
        """Check if video source is opened."""
        pass


class WebcamVideoSource(VideoSource):
    """Webcam video source."""
    
    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.cap = cv2.VideoCapture(device_id)
        
        if not self.cap.isOpened():
            raise IOError(f"Failed to open webcam device: {device_id}")
        
        logger.info("Webcam source initialized", device_id=device_id)
    
    def get_frames(self) -> Generator[Tuple[bool, cv2.Mat], None, None]:
        """Get webcam frames."""
        while True:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to read frame from webcam")
                break
            yield ret, frame
    
    def release(self) -> None:
        """Release webcam."""
        if self.cap.isOpened():
            self.cap.release()
            logger.info("Webcam released")
    
    def is_opened(self) -> bool:
        """Check if webcam is opened."""
        return self.cap.isOpened()


class RTSPVideoSource(VideoSource):
    """RTSP video source."""
    
    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self.cap = cv2.VideoCapture(rtsp_url)
        
        if not self.cap.isOpened():
            raise IOError(f"Failed to open RTSP stream: {rtsp_url}")
        
        logger.info("RTSP source initialized", url=rtsp_url)
    
    def get_frames(self) -> Generator[Tuple[bool, cv2.Mat], None, None]:
        """Get RTSP frames."""
        while True:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to read frame from RTSP stream")
                break
            yield ret, frame
    
    def release(self) -> None:
        """Release RTSP stream."""
        if self.cap.isOpened():
            self.cap.release()
            logger.info("RTSP stream released")
    
    def is_opened(self) -> bool:
        """Check if RTSP stream is opened."""
        return self.cap.isOpened()


class FileVideoSource(VideoSource):
    """Video file source."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.cap = cv2.VideoCapture(file_path)
        
        if not self.cap.isOpened():
            raise IOError(f"Failed to open video file: {file_path}")
        
        # Get video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info("File source initialized", file_path=file_path, fps=self.fps, frame_count=self.frame_count)
    
    def get_frames(self) -> Generator[Tuple[bool, cv2.Mat], None, None]:
        """Get video file frames."""
        while True:
            ret, frame = self.cap.read()
            if not ret:
                logger.info("End of video file reached")
                break
            yield ret, frame
    
    def release(self) -> None:
        """Release video file."""
        if self.cap.isOpened():
            self.cap.release()
            logger.info("Video file released")
    
    def is_opened(self) -> bool:
        """Check if video file is opened."""
        return self.cap.isOpened()


class VideoSourceFactory:
    """Factory for creating video sources."""
    
    @staticmethod
    def create(source_type: VideoSourceType, source_path: Optional[str] = None) -> VideoSource:
        """Create video source based on type."""
        if source_type == VideoSourceType.WEBCAM:
            device_id = int(source_path) if source_path and source_path.isdigit() else 0
            return WebcamVideoSource(device_id)
        elif source_type == VideoSourceType.RTSP:
            if not source_path:
                raise ValueError("RTSP URL is required for RTSP source")
            return RTSPVideoSource(source_path)
        elif source_type == VideoSourceType.FILE:
            if not source_path:
                raise ValueError("File path is required for file source")
            # Convert to absolute path if relative
            import os
            if not os.path.isabs(source_path):
                source_path = os.path.abspath(source_path)
            return FileVideoSource(source_path)
        else:
            raise ValueError(f"Unsupported video source type: {source_type}")


class VideoService:
    """Service for video processing operations."""
    
    def __init__(self, source: VideoSource):
        self.source = source
        self.frame_count = 0
    
    @classmethod
    def create_from_config(cls) -> 'VideoService':
        """Create VideoService from configuration."""
        source_type = VideoSourceType.WEBCAM  # Default
        source_path = "0"  # Default webcam
        
        # Determine source type based on configuration
        if settings.rtsp_url:
            source_type = VideoSourceType.RTSP
            source_path = settings.rtsp_url
        elif settings.video_source == "file":
            source_type = VideoSourceType.FILE
            source_path = settings.video_source_path
        elif settings.video_source == "webcam":
            source_type = VideoSourceType.WEBCAM
            source_path = "0"
        elif settings.video_source and settings.video_source != "0":
            if settings.video_source.startswith("rtsp://"):
                source_type = VideoSourceType.RTSP
                source_path = settings.video_source
            else:
                source_type = VideoSourceType.FILE
                source_path = settings.video_source
        
        video_source = VideoSourceFactory.create(source_type, source_path)
        return cls(video_source)
    
    def get_frames(self) -> Generator[Tuple[bool, cv2.Mat], None, None]:
        """Get video frames with frame counting."""
        for ret, frame in self.source.get_frames():
            self.frame_count += 1
            yield ret, frame
    
    def release(self) -> None:
        """Release video source."""
        self.source.release()
        logger.info("Video service released", total_frames=self.frame_count)
    
    def is_opened(self) -> bool:
        """Check if video source is opened."""
        return self.source.is_opened()
    
    def get_frame_count(self) -> int:
        """Get total frame count."""
        return self.frame_count
