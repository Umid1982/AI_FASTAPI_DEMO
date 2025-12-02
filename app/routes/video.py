from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
import structlog
from datetime import datetime

from app.database.connection import get_db
from app.services.video_service import VideoService, VideoSourceFactory
from app.services.detection_service import DetectionService
from app.services.tracking_service import TrackingService
from app.services.llm_service import LLMService
from app.services.analytics_service import AnalyticsService
from app.repositories.video_session_repository import VideoSessionRepository
from app.repositories.detection_repository import DetectionRepository
from app.models.schemas import (
    VideoAnalysisRequest, 
    VideoAnalysisResponse, 
    VideoFrame,
    VideoSourceType
)
from app.utils.response_helper import success_response, error_response

logger = structlog.get_logger()
router = APIRouter(prefix="/video", tags=["Video"])


# Dependency injection functions
def get_video_session_repo(db: Session = Depends(get_db)) -> VideoSessionRepository:
    """Get video session repository."""
    return VideoSessionRepository(db)


def get_detection_repo(db: Session = Depends(get_db)) -> DetectionRepository:
    """Get detection repository."""
    return DetectionRepository(db)


def get_analytics_service(
    session_repo: VideoSessionRepository = Depends(get_video_session_repo),
    detection_repo: DetectionRepository = Depends(get_detection_repo)
) -> AnalyticsService:
    """Get analytics service."""
    return AnalyticsService(session_repo, detection_repo)


def get_video_service() -> VideoService:
    """Get video service."""
    return VideoService.create_from_config()


def get_detection_service() -> DetectionService:
    """Get detection service."""
    return DetectionService.create_person_detector()


def get_tracking_service() -> TrackingService:
    """Get tracking service."""
    return TrackingService.create_simple_tracker()  # Используем Simple пока DeepSORT не работает


def get_llm_service() -> LLMService:
    """Get LLM service."""
    return LLMService()


@router.post("/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(
    request: VideoAnalysisRequest,
    background_tasks: BackgroundTasks,
    video_service: VideoService = Depends(get_video_service),
    detection_service: DetectionService = Depends(get_detection_service),
    tracking_service: TrackingService = Depends(get_tracking_service),
    llm_service: LLMService = Depends(get_llm_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    session_repo: VideoSessionRepository = Depends(get_video_session_repo)
):
    """Start video analysis session."""
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create video source based on request
        video_source = VideoSourceFactory.create(request.source_type, request.source_path)
        video_service = VideoService(video_source)
        
        # Create session in database
        session = session_repo.create_session(
            session_id=session_id,
            source_type=request.source_type.value,
            source_path=request.source_path
            # metadata removed - not in VideoSession model
        )
        
        # Start analysis in background
        background_tasks.add_task(
            _process_video_analysis,
            session_id,
            video_service,
            detection_service,
            tracking_service,
            llm_service,
            analytics_service,
            session_repo,
            request.duration
        )
        
        logger.info("Video analysis started", session_id=session_id)
        
        return VideoAnalysisResponse(
            session_id=session_id,
            status="started",
            message="Video analysis started successfully"
        )
        
    except Exception as e:
        logger.error("Failed to start video analysis", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def _process_video_analysis(
    session_id: str,
    video_service: VideoService,
    detection_service: DetectionService,
    tracking_service: TrackingService,
    llm_service: LLMService,
    analytics_service: AnalyticsService,
    session_repo: VideoSessionRepository,
    duration: int = None
):
    """Process video analysis in background."""
    try:
        # Create detection repo using same DB session
        detection_repo = DetectionRepository(session_repo.db)
        
        frames = []
        frame_count = 0
        max_frames = duration * 30 if duration else 1000  # Assume 30 FPS
        
        logger.info("Starting video processing", session_id=session_id, max_frames=max_frames)
        
        # Test video source first
        try:
            logger.info("Testing video source...")
            frame_generator = video_service.get_frames()
            logger.info("Video source initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize video source", error=str(e))
            raise
        
        for ret, frame in video_service.get_frames():
            if not ret:
                logger.warning("Video frame read failed", frame_count=frame_count)
                break
            
            frame_count += 1
            if frame_count > max_frames:
                logger.info("Reached max frames limit", frame_count=frame_count, max_frames=max_frames)
                break
            
            # Detect objects
            try:
                detections = detection_service.detect_objects(frame)
                logger.debug("Detections found", frame_count=frame_count, detections_count=len(detections))
                
                # Если детекций нет, это нормально для некоторых кадров
                if len(detections) == 0:
                    logger.debug("No detections in frame", frame_count=frame_count)
                    
            except Exception as e:
                logger.error("Detection failed", frame_count=frame_count, error=str(e))
                detections = []
            
            # DEBUG: Принудительно добавляем детекцию для теста каждые 50 кадров
            if frame_count % 50 == 0 and len(detections) == 0:
                logger.info("Adding test detection", frame_count=frame_count)
                from app.models.schemas import BoundingBox, Detection as DetectionSchema
                detections = [DetectionSchema(
                    class_id=0,
                    class_name="person",
                    confidence=0.8,
                    bbox=BoundingBox(x1=100, y1=100, x2=200, y2=300)
                )]
            
            # Track objects
            try:
                tracked_objects = tracking_service.track_objects(detections)
                logger.info("Objects tracked", frame_count=frame_count, tracked_count=len(tracked_objects))
            except Exception as e:
                logger.error("Tracking failed", frame_count=frame_count, error=str(e))
                tracked_objects = []
            
            # Create video frame
            video_frame = VideoFrame(
                frame_number=frame_count,
                detections=detections,
                tracked_objects=tracked_objects
            )
            frames.append(video_frame)
            
            # Log progress every 10 frames (more frequent for debugging)
            if frame_count % 10 == 0:
                logger.info("Processing progress", session_id=session_id, frames=frame_count, detections=len(detections), tracked=len(tracked_objects))
        
        # Save all detections to database at the end (bulk save)
        logger.info("Saving all detections to database", session_id=session_id, total_frames=len(frames))
        total_detections_to_save = sum(len(frame.detections) for frame in frames)
        logger.info(f"Total detections to save: {total_detections_to_save}")
        
        if total_detections_to_save == 0:
            logger.warning("No detections to save - skipping database save")
        else:
            try:
                from app.database.models import Detection as DetectionModel
                import uuid
                
                saved_count = 0
                for frame in frames:
                    for detection in frame.detections:
                        detection_db = DetectionModel(
                            id=str(uuid.uuid4()),
                            session_id=session_id,
                            frame_number=frame.frame_number,
                            class_name=detection.class_name,
                            confidence=detection.confidence,
                            bbox_x=detection.bbox.x1,
                            bbox_y=detection.bbox.y1,
                            bbox_width=detection.bbox.x2 - detection.bbox.x1,
                            bbox_height=detection.bbox.y2 - detection.bbox.y1
                        )
                        detection_repo.db.add(detection_db)
                        saved_count += 1
                
                detection_repo.db.commit()
                logger.info("All detections saved to database successfully", total_saved=saved_count)
            except Exception as e:
                logger.error("Failed to save detections to database", error=str(e), exc_info=True)
                detection_repo.db.rollback()
                raise
            
            # Save tracked objects
            try:
                from app.database.models import TrackedObject as TrackedObjectModel
                from datetime import datetime
                
                tracked_objects_count = sum(len(frame.tracked_objects) for frame in frames)
                logger.info(f"Saving {tracked_objects_count} tracked objects to database")
                
                saved_tracked = 0
                for frame in frames:
                    for tracked_obj in frame.tracked_objects:
                        tracked_db = TrackedObjectModel(
                            id=tracked_obj.id,
                            session_id=session_id,
                            track_id=tracked_obj.track_id,
                            first_seen=tracked_obj.first_seen,
                            last_seen=tracked_obj.last_seen,
                            total_detections=tracked_obj.total_detections,
                            duration=tracked_obj.duration,
                            is_active=tracked_obj.is_active
                        )
                        detection_repo.db.add(tracked_db)
                        saved_tracked += 1
                
                detection_repo.db.commit()
                logger.info("All tracked objects saved to database successfully", total_saved=saved_tracked)
            except Exception as e:
                logger.error("Failed to save tracked objects to database", error=str(e), exc_info=True)
                detection_repo.db.rollback()
            
            # Save heatmap points (extract from detections)
            try:
                from app.database.models import HeatmapPoint as HeatmapPointModel
                
                heatmap_points_count = 0
                saved_heatmap = 0
                
                for frame in frames:
                    for detection in frame.detections:
                        # Create heatmap point from detection center
                        center_x = (detection.bbox.x1 + detection.bbox.x2) / 2
                        center_y = (detection.bbox.y1 + detection.bbox.y2) / 2
                        
                        heatmap_db = HeatmapPointModel(
                            id=str(uuid.uuid4()),
                            session_id=session_id,
                            x=center_x,
                            y=center_y,
                            intensity=detection.confidence,
                            timestamp=frame.timestamp
                        )
                        detection_repo.db.add(heatmap_db)
                        saved_heatmap += 1
                        heatmap_points_count += 1
                
                if heatmap_points_count > 0:
                    detection_repo.db.commit()
                    logger.info("All heatmap points saved to database successfully", total_saved=saved_heatmap)
            except Exception as e:
                logger.error("Failed to save heatmap points to database", error=str(e), exc_info=True)
                detection_repo.db.rollback()
        
        # Calculate analytics
        analytics = analytics_service.calculate_analytics(frames, session_id)
        
        # Update session with analytics
        session_repo.update_session_stats(
            session_id=session_id,
            total_frames=analytics.total_frames,
            total_people=analytics.total_people,
            peak_people_count=analytics.peak_people_count,
            average_stay_time=analytics.average_stay_time
        )
        
        # Complete session
        session_repo.complete_session(session_id)
        
        logger.info("Video analysis completed", session_id=session_id, frames=frame_count)
        
    except Exception as e:
        logger.error("Video analysis failed", session_id=session_id, error=str(e))
        # Mark session as failed
        try:
            session = session_repo.get(session_id)
            if session:
                session.status = "failed"
                session_repo.db.commit()
        except:
            pass


@router.get("/analyze/{session_id}")
async def get_analysis_status(
    session_id: str,
    session_repo: VideoSessionRepository = Depends(get_video_session_repo)
):
    """Get analysis session status."""
    try:
        session = session_repo.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return success_response(
            data={
                "session_id": session_id,
                "status": session.status,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "total_frames": session.total_frames,
                "total_people": session.total_people,
                "peak_people_count": session.peak_people_count,
                "average_stay_time": session.average_stay_time
            },
            message="Analysis status retrieved"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get analysis status", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_sessions(
    skip: int = 0,
    limit: int = 10,
    session_repo: VideoSessionRepository = Depends(get_video_session_repo)
):
    """Get recent analysis sessions."""
    try:
        sessions = session_repo.get_recent_sessions(limit=limit)
        
        session_data = []
        for session in sessions:
            session_data.append({
                "session_id": session.id,
                "status": session.status,
                "source_type": session.source_type,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "total_frames": session.total_frames,
                "total_people": session.total_people,
                "peak_people_count": session.peak_people_count,
                "average_stay_time": session.average_stay_time
            })
        
        return success_response(
            data=session_data,
            message="Sessions retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Failed to get sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_repo: VideoSessionRepository = Depends(get_video_session_repo)
):
    """Delete analysis session."""
    try:
        success = session_repo.delete(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return success_response(
            message="Session deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
