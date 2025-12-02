from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
import structlog
from datetime import datetime
from app.models.schemas import Detection, TrackedObject, TrackingStatus, BoundingBox

logger = structlog.get_logger()


class TrackingStrategy(ABC):
    """Abstract base class for tracking strategies."""
    
    @abstractmethod
    def track(self, detections: List[Detection]) -> List[TrackedObject]:
        """Track objects from detections."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset tracking state."""
        pass


class SimpleTrackingStrategy(TrackingStrategy):
    """Simple tracking strategy (original implementation)."""
    
    def __init__(self):
        self.next_id = 0
        self.tracked_objects: Dict[int, TrackedObject] = {}
    
    def track(self, detections: List[Detection]) -> List[TrackedObject]:
        """Simple tracking implementation."""
        tracked = []
        
        for detection in detections:
            tracked_obj = TrackedObject(
                id=f"simple_{self.next_id}",
                track_id=self.next_id,
                detection=detection,
                status=TrackingStatus.ACTIVE,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                total_detections=1,
                duration=0.0,
                is_active=True
            )
            
            self.tracked_objects[self.next_id] = tracked_obj
            tracked.append(tracked_obj)
            self.next_id += 1
        
        logger.debug("Simple tracking completed", tracked_count=len(tracked))
        return tracked
    
    def reset(self) -> None:
        """Reset tracking state."""
        self.next_id = 0
        self.tracked_objects.clear()
        logger.info("Simple tracking reset")


class DeepSORTTrackingStrategy(TrackingStrategy):
    """DeepSORT-based tracking strategy."""
    
    def __init__(self, max_cosine_distance: float = 0.2, nn_budget: int = 100):
        try:
            from deep_sort_realtime.deep_sort.deep_sort import DeepSort
            self.tracker = DeepSort(
                max_cosine_distance=max_cosine_distance,
                nn_budget=nn_budget
            )
            self.tracked_objects: Dict[int, TrackedObject] = {}
            logger.info("DeepSORT tracking strategy initialized")
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning("DeepSORT not available, falling back to simple tracking", error=str(e))
            self.tracker = None
            self.tracked_objects: Dict[int, TrackedObject] = {}
    
    def track(self, detections: List[Detection]) -> List[TrackedObject]:
        """Track objects using DeepSORT."""
        if not self.tracker:
            # Fallback to simple tracking
            return self._simple_track(detections)
        
        try:
            # Convert detections to DeepSORT format
            detections_array = []
            for detection in detections:
                bbox = detection.bbox
                detections_array.append([
                    bbox.x1, bbox.y1, bbox.x2 - bbox.x1, bbox.y2 - bbox.y1,
                    detection.confidence
                ])
            
            if not detections_array:
                return []
            
            # Track objects
            tracks = self.tracker.update_tracks(detections_array, frame=None)
            
            tracked = []
            for track in tracks:
                if not track.is_confirmed():
                    continue
                
                track_id = track.track_id
                bbox = track.to_ltwh()
                
                # Create bounding box
                bbox_obj = BoundingBox(
                    x1=bbox[0],
                    y1=bbox[1],
                    x2=bbox[0] + bbox[2],
                    y2=bbox[1] + bbox[3]
                )
                
                # Create detection
                detection = Detection(
                    class_id=0,  # Assume person for now
                    class_name="person",
                    confidence=1.0,  # DeepSORT handles confidence internally
                    bbox=bbox_obj
                )
                
                # Update or create tracked object
                if track_id in self.tracked_objects:
                    tracked_obj = self.tracked_objects[track_id]
                    tracked_obj.detection = detection
                    tracked_obj.last_seen = datetime.now()
                    tracked_obj.total_detections += 1
                    tracked_obj.duration = (tracked_obj.last_seen - tracked_obj.first_seen).total_seconds()
                else:
                    tracked_obj = TrackedObject(
                        id=f"deepsort_{track_id}",
                        track_id=track_id,
                        detection=detection,
                        status=TrackingStatus.ACTIVE,
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        total_detections=1,
                        duration=0.0,
                        is_active=True
                    )
                    self.tracked_objects[track_id] = tracked_obj
                
                tracked.append(tracked_obj)
            
            logger.debug("DeepSORT tracking completed", tracked_count=len(tracked))
            return tracked
            
        except Exception as e:
            logger.error("DeepSORT tracking failed", error=str(e))
            return self._simple_track(detections)
    
    def _simple_track(self, detections: List[Detection]) -> List[TrackedObject]:
        """Fallback simple tracking."""
        tracked = []
        for i, detection in enumerate(detections):
            tracked_obj = TrackedObject(
                id=f"fallback_{i}",
                track_id=i,
                detection=detection,
                status=TrackingStatus.ACTIVE,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                total_detections=1,
                duration=0.0,
                is_active=True
            )
            tracked.append(tracked_obj)
        return tracked
    
    def reset(self) -> None:
        """Reset tracking state."""
        if self.tracker:
            self.tracker = None
        self.tracked_objects.clear()
        logger.info("DeepSORT tracking reset")


class TrackingService:
    """Service for object tracking operations."""
    
    def __init__(self, strategy: TrackingStrategy = None):
        self.strategy = strategy or SimpleTrackingStrategy()
        self.total_tracked = 0
    
    @classmethod
    def create_simple_tracker(cls) -> 'TrackingService':
        """Create simple tracking service."""
        strategy = SimpleTrackingStrategy()
        return cls(strategy)
    
    @classmethod
    def create_deepsort_tracker(cls) -> 'TrackingService':
        """Create DeepSORT tracking service."""
        strategy = DeepSORTTrackingStrategy()
        return cls(strategy)
    
    def track_objects(self, detections: List[Detection]) -> List[TrackedObject]:
        """Track objects from detections."""
        try:
            tracked = self.strategy.track(detections)
            self.total_tracked += len(tracked)
            
            logger.debug("Object tracking completed", tracked_count=len(tracked))
            return tracked
            
        except Exception as e:
            logger.error("Object tracking failed", error=str(e))
            raise
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get tracking statistics."""
        return {
            "total_tracked": self.total_tracked,
            "strategy": self.strategy.__class__.__name__
        }
    
    def reset(self) -> None:
        """Reset tracking state."""
        self.strategy.reset()
        self.total_tracked = 0
        logger.info("Tracking service reset")
