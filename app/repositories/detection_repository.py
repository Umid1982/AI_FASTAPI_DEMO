from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime
from app.database.models import Detection
from app.repositories.base_repository import BaseRepository
import structlog

logger = structlog.get_logger()


class DetectionRepository(BaseRepository[Detection]):
    """Repository for detection operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Detection)
    
    def create_detection(
        self,
        session_id: str,
        frame_number: int,
        class_id: int,
        class_name: str,
        confidence: float,
        bbox_x1: float,
        bbox_y1: float,
        bbox_x2: float,
        bbox_y2: float
    ) -> Detection:
        """Create a new detection."""
        detection_data = {
            "session_id": session_id,
            "frame_number": frame_number,
            "class_id": class_id,
            "class_name": class_name,
            "confidence": confidence,
            "bbox_x1": bbox_x1,
            "bbox_y1": bbox_y1,
            "bbox_x2": bbox_x2,
            "bbox_y2": bbox_y2
        }
        return self.create(detection_data)
    
    def get_session_detections(
        self,
        session_id: str,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Detection]:
        """Get detections for a specific session."""
        try:
            return (
                self.db.query(Detection)
                .filter(Detection.session_id == session_id)
                .order_by(Detection.frame_number)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error("Failed to get session detections", session_id=session_id, error=str(e))
            raise
    
    def get_detections_by_class(
        self,
        session_id: str,
        class_name: str,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Detection]:
        """Get detections by class name for a session."""
        try:
            return (
                self.db.query(Detection)
                .filter(
                    and_(
                        Detection.session_id == session_id,
                        Detection.class_name == class_name
                    )
                )
                .order_by(Detection.frame_number)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error("Failed to get detections by class", session_id=session_id, class_name=class_name, error=str(e))
            raise
    
    def get_detections_by_confidence(
        self,
        session_id: str,
        min_confidence: float,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Detection]:
        """Get detections above confidence threshold."""
        try:
            return (
                self.db.query(Detection)
                .filter(
                    and_(
                        Detection.session_id == session_id,
                        Detection.confidence >= min_confidence
                    )
                )
                .order_by(desc(Detection.confidence))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error("Failed to get detections by confidence", session_id=session_id, min_confidence=min_confidence, error=str(e))
            raise
    
    def get_detection_stats(self, session_id: str) -> Dict[str, Any]:
        """Get detection statistics for a session."""
        try:
            # Total detections
            total_detections = (
                self.db.query(Detection)
                .filter(Detection.session_id == session_id)
                .count()
            )
            
            # Detections by class
            class_counts = (
                self.db.query(Detection.class_name, func.count(Detection.id))
                .filter(Detection.session_id == session_id)
                .group_by(Detection.class_name)
                .all()
            )
            
            # Average confidence
            avg_confidence = (
                self.db.query(func.avg(Detection.confidence))
                .filter(Detection.session_id == session_id)
                .scalar()
            ) or 0.0
            
            # Frame range
            frame_range = (
                self.db.query(
                    func.min(Detection.frame_number),
                    func.max(Detection.frame_number)
                )
                .filter(Detection.session_id == session_id)
                .first()
            )
            
            return {
                "total_detections": total_detections,
                "class_counts": dict(class_counts),
                "average_confidence": round(avg_confidence, 3),
                "frame_range": {
                    "min": frame_range[0] if frame_range[0] else 0,
                    "max": frame_range[1] if frame_range[1] else 0
                }
            }
        except Exception as e:
            logger.error("Failed to get detection stats", session_id=session_id, error=str(e))
            raise
    
    def get_detections_in_bbox(
        self,
        session_id: str,
        bbox_x1: float,
        bbox_y1: float,
        bbox_x2: float,
        bbox_y2: float,
        overlap_threshold: float = 0.5
    ) -> List[Detection]:
        """Get detections that overlap with specified bounding box."""
        try:
            # Calculate overlap area
            detections = (
                self.db.query(Detection)
                .filter(Detection.session_id == session_id)
                .all()
            )
            
            overlapping = []
            for detection in detections:
                # Calculate intersection
                x1 = max(bbox_x1, detection.bbox_x1)
                y1 = max(bbox_y1, detection.bbox_y1)
                x2 = min(bbox_x2, detection.bbox_x2)
                y2 = min(bbox_y2, detection.bbox_y2)
                
                if x1 < x2 and y1 < y2:
                    intersection = (x2 - x1) * (y2 - y1)
                    
                    # Calculate union
                    area1 = (detection.bbox_x2 - detection.bbox_x1) * (detection.bbox_y2 - detection.bbox_y1)
                    area2 = (bbox_x2 - bbox_x1) * (bbox_y2 - bbox_y1)
                    union = area1 + area2 - intersection
                    
                    # Calculate IoU
                    iou = intersection / union if union > 0 else 0
                    
                    if iou >= overlap_threshold:
                        overlapping.append(detection)
            
            return overlapping
        except Exception as e:
            logger.error("Failed to get detections in bbox", session_id=session_id, error=str(e))
            raise
    
    def delete_session_detections(self, session_id: str) -> int:
        """Delete all detections for a session."""
        try:
            deleted_count = (
                self.db.query(Detection)
                .filter(Detection.session_id == session_id)
                .delete()
            )
            
            self.db.commit()
            logger.info("Deleted session detections", session_id=session_id, count=deleted_count)
            return deleted_count
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to delete session detections", session_id=session_id, error=str(e))
            raise
