from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta
from app.database.models import VideoSession, Detection, TrackedObject, HeatmapPoint, Report
from app.repositories.base_repository import BaseRepository
import structlog

logger = structlog.get_logger()


class VideoSessionRepository(BaseRepository[VideoSession]):
    """Repository for video session operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, VideoSession)
    
    def create_session(
        self,
        session_id: str,
        source_type: str,
        source_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VideoSession:
        """Create a new video session."""
        session_data = {
            "id": session_id,
            "source_type": source_type,
            "source_path": source_path,
            "status": "active"
            # metadata removed - not in VideoSession model
        }
        return self.create(session_data)
    
    def get_active_sessions(self) -> List[VideoSession]:
        """Get all active sessions."""
        try:
            return (
                self.db.query(VideoSession)
                .filter(VideoSession.status == "active")
                .order_by(desc(VideoSession.start_time))
                .all()
            )
        except Exception as e:
            logger.error("Failed to get active sessions", error=str(e))
            raise
    
    def complete_session(self, session_id: str) -> Optional[VideoSession]:
        """Mark session as completed."""
        try:
            session = self.get(session_id)
            if not session:
                return None
            
            session.status = "completed"
            session.end_time = datetime.now()
            self.db.commit()
            self.db.refresh(session)
            
            logger.info("Session completed", session_id=session_id)
            return session
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to complete session", session_id=session_id, error=str(e))
            raise
    
    def update_session_stats(
        self,
        session_id: str,
        total_frames: int,
        total_people: int,
        peak_people_count: int,
        average_stay_time: float
    ) -> Optional[VideoSession]:
        """Update session statistics."""
        try:
            session = self.get(session_id)
            if not session:
                return None
            
            session.total_frames = total_frames
            session.total_people = total_people
            session.peak_people_count = peak_people_count
            session.average_stay_time = average_stay_time
            
            self.db.commit()
            self.db.refresh(session)
            
            logger.debug("Updated session stats", session_id=session_id)
            return session
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update session stats", session_id=session_id, error=str(e))
            raise
    
    def get_sessions_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[VideoSession]:
        """Get sessions within date range."""
        try:
            return (
                self.db.query(VideoSession)
                .filter(
                    and_(
                        VideoSession.start_time >= start_date,
                        VideoSession.start_time <= end_date
                    )
                )
                .order_by(desc(VideoSession.start_time))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error("Failed to get sessions by date range", error=str(e))
            raise
    
    def get_session_with_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session with full analytics data."""
        try:
            session = self.get(session_id)
            if not session:
                return None
            
            # Get detections count
            detections_count = (
                self.db.query(Detection)
                .filter(Detection.session_id == session_id)
                .count()
            )
            
            # Get tracked objects count
            tracked_objects_count = (
                self.db.query(TrackedObject)
                .filter(TrackedObject.session_id == session_id)
                .count()
            )
            
            # Get heatmap points
            heatmap_points = (
                self.db.query(HeatmapPoint)
                .filter(HeatmapPoint.session_id == session_id)
                .all()
            )
            
            # Get reports
            reports = (
                self.db.query(Report)
                .filter(Report.session_id == session_id)
                .order_by(desc(Report.generated_at))
                .all()
            )
            
            return {
                "session": session,
                "detections_count": detections_count,
                "tracked_objects_count": tracked_objects_count,
                "heatmap_points": heatmap_points,
                "reports": reports
            }
        except Exception as e:
            logger.error("Failed to get session with analytics", session_id=session_id, error=str(e))
            raise
    
    def get_recent_sessions(self, limit: int = 10) -> List[VideoSession]:
        """Get recent sessions."""
        try:
            return (
                self.db.query(VideoSession)
                .order_by(desc(VideoSession.start_time))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error("Failed to get recent sessions", error=str(e))
            raise
    
    def delete_old_sessions(self, days: int = 30) -> int:
        """Delete sessions older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted_count = (
                self.db.query(VideoSession)
                .filter(VideoSession.start_time < cutoff_date)
                .delete()
            )
            
            self.db.commit()
            logger.info("Deleted old sessions", count=deleted_count, days=days)
            return deleted_count
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to delete old sessions", error=str(e))
            raise
