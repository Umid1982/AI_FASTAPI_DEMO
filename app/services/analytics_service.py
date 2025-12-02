from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime, timedelta
import structlog
from app.models.schemas import TrackedObject, HeatmapPoint, AnalyticsData, VideoFrame
from app.repositories.video_session_repository import VideoSessionRepository
from app.repositories.detection_repository import DetectionRepository

logger = structlog.get_logger()


class AnalyticsService:
    """Service for video analytics operations."""
    
    def __init__(self, session_repo: VideoSessionRepository, detection_repo: DetectionRepository):
        self.session_repo = session_repo
        self.detection_repo = detection_repo
    
    def calculate_analytics(self, frames: List[VideoFrame], session_id: str) -> AnalyticsData:
        """Calculate comprehensive analytics from video frames."""
        try:
            # Extract all tracked objects from frames
            all_tracked_objects = []
            for frame in frames:
                all_tracked_objects.extend(frame.tracked_objects)
            
            # Calculate basic statistics
            # For now, use peak_people_count as total_people because SimpleTrackingStrategy
            # doesn't track the same person across frames - it creates new objects for each detection
            peak_people_count = self._calculate_peak_people_count(frames)
            total_people = peak_people_count  # Use peak as total until we implement proper tracking
            average_stay_time = self._calculate_average_stay_time(all_tracked_objects)
            
            # Calculate heatmap points
            heatmap_points = self._calculate_heatmap_points(all_tracked_objects)
            
            # Calculate peak hours
            peak_hours = self._calculate_peak_hours(frames)
            
            # Calculate session duration
            if frames:
                session_duration = (frames[-1].timestamp - frames[0].timestamp).total_seconds()
            else:
                session_duration = 0.0
            
            analytics = AnalyticsData(
                session_id=session_id,
                start_time=frames[0].timestamp if frames else datetime.now(),
                end_time=frames[-1].timestamp if frames else None,
                total_frames=len(frames),
                total_people=total_people,
                peak_people_count=peak_people_count,
                average_stay_time=average_stay_time,
                heatmap_points=heatmap_points,
                peak_hours=peak_hours,
                metadata={
                    "total_detections": sum(len(frame.detections) for frame in frames),
                    "total_tracked_objects": len(all_tracked_objects),
                    "session_duration": session_duration
                }
            )
            
            logger.info("Analytics calculated", session_id=session_id, total_people=total_people)
            return analytics
            
        except Exception as e:
            logger.error("Failed to calculate analytics", session_id=session_id, error=str(e))
            raise
    
    def _calculate_peak_people_count(self, frames: List[VideoFrame]) -> int:
        """Calculate peak number of people in any single frame."""
        if not frames:
            return 0
        
        peak_count = 0
        for frame in frames:
            people_count = len([obj for obj in frame.tracked_objects if obj.detection.class_name == "person"])
            peak_count = max(peak_count, people_count)
        
        return peak_count
    
    def _calculate_average_stay_time(self, tracked_objects: List[TrackedObject]) -> float:
        """Calculate average stay time for tracked objects."""
        if not tracked_objects:
            return 0.0
        
        # Calculate duration from first_seen to last_seen
        total_duration = 0.0
        for obj in tracked_objects:
            duration = (obj.last_seen - obj.first_seen).total_seconds()
            total_duration += duration
        
        return total_duration / len(tracked_objects)
    
    def _calculate_heatmap_points(self, tracked_objects: List[TrackedObject]) -> List[HeatmapPoint]:
        """Calculate heatmap points from tracked objects."""
        heatmap_points = []
        
        for obj in tracked_objects:
            if obj.detection.class_name == "person":
                # Use center of bounding box as heatmap point
                center_x, center_y = obj.detection.bbox.center
                
                # Calculate intensity based on duration and confidence
                intensity = obj.duration * obj.detection.confidence
                
                heatmap_point = HeatmapPoint(
                    x=center_x,
                    y=center_y,
                    intensity=intensity,
                    timestamp=obj.last_seen
                )
                heatmap_points.append(heatmap_point)
        
        return heatmap_points
    
    def _calculate_peak_hours(self, frames: List[VideoFrame]) -> List[str]:
        """Calculate peak activity hours."""
        if not frames:
            return []
        
        # Group frames by hour
        hourly_counts = {}
        for frame in frames:
            hour = frame.timestamp.hour
            people_count = len([obj for obj in frame.tracked_objects if obj.detection.class_name == "person"])
            
            if hour not in hourly_counts:
                hourly_counts[hour] = []
            hourly_counts[hour].append(people_count)
        
        # Calculate average people count per hour
        hourly_averages = {}
        for hour, counts in hourly_counts.items():
            hourly_averages[hour] = sum(counts) / len(counts)
        
        # Find peak hours (above average)
        if not hourly_averages:
            return []
        
        overall_average = sum(hourly_averages.values()) / len(hourly_averages)
        peak_hours = [
            f"{hour:02d}:00-{hour+1:02d}:00"
            for hour, avg in hourly_averages.items()
            if avg > overall_average
        ]
        
        return sorted(peak_hours)
    
    def generate_heatmap_data(self, heatmap_points: List[HeatmapPoint], width: int = 100, height: int = 100) -> np.ndarray:
        """Generate heatmap matrix from heatmap points."""
        try:
            # Initialize heatmap matrix
            heatmap = np.zeros((height, width))
            
            if not heatmap_points:
                return heatmap
            
            # Normalize coordinates to heatmap dimensions
            max_x = max(point.x for point in heatmap_points)
            min_x = min(point.x for point in heatmap_points)
            max_y = max(point.y for point in heatmap_points)
            min_y = min(point.y for point in heatmap_points)
            
            if max_x == min_x or max_y == min_y:
                return heatmap
            
            for point in heatmap_points:
                # Normalize coordinates
                norm_x = int((point.x - min_x) / (max_x - min_x) * (width - 1))
                norm_y = int((point.y - min_y) / (max_y - min_y) * (height - 1))
                
                # Add intensity to heatmap
                heatmap[norm_y, norm_x] += point.intensity
            
            logger.debug("Heatmap data generated", shape=heatmap.shape)
            return heatmap
            
        except Exception as e:
            logger.error("Failed to generate heatmap data", error=str(e))
            return np.zeros((height, width))
    
    def get_session_analytics(self, session_id: str) -> Optional[AnalyticsData]:
        """Get analytics for a specific session."""
        try:
            session_data = self.session_repo.get_session_with_analytics(session_id)
            if not session_data:
                return None
            
            session = session_data["session"]
            
            # Convert SQLAlchemy HeatmapPoint objects to Pydantic models
            heatmap_points_pydantic = []
            for db_point in session_data["heatmap_points"]:
                heatmap_points_pydantic.append(
                    HeatmapPoint(
                        x=db_point.x,
                        y=db_point.y,
                        intensity=db_point.intensity,
                        timestamp=db_point.timestamp
                    )
                )
            
            # Create analytics data from session
            analytics = AnalyticsData(
                session_id=session_id,
                start_time=session.start_time,
                end_time=session.end_time,
                total_frames=session.total_frames,
                total_people=session.total_people,
                peak_people_count=session.peak_people_count,
                average_stay_time=session.average_stay_time,
                heatmap_points=heatmap_points_pydantic,
                peak_hours=[],  # Would need to calculate from stored data
                metadata={}  # No metadata field in VideoSession model
            )
            
            logger.info("Session analytics retrieved", session_id=session_id)
            return analytics
            
        except Exception as e:
            logger.error("Failed to get session analytics", session_id=session_id, error=str(e))
            raise
    
    def get_detection_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get detection statistics for a session."""
        try:
            stats = self.detection_repo.get_detection_stats(session_id)
            logger.info("Detection statistics retrieved", session_id=session_id)
            return stats
        except Exception as e:
            logger.error("Failed to get detection statistics", session_id=session_id, error=str(e))
            raise
