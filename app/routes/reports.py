from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import structlog
from datetime import datetime

from app.database.connection import get_db
from app.services.llm_service import LLMService
from app.services.analytics_service import AnalyticsService
from app.repositories.video_session_repository import VideoSessionRepository
from app.repositories.detection_repository import DetectionRepository
from app.core.redis_cache import redis_cache
from app.models.schemas import (
    ReportRequest,
    ReportResponse,
    AnalyticsData
)
from app.utils.response_helper import success_response, error_response

logger = structlog.get_logger()
router = APIRouter(prefix="/reports", tags=["Reports"])


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


def get_llm_service() -> LLMService:
    """Get LLM service."""
    return LLMService()


@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    llm_service: LLMService = Depends(get_llm_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Generate AI-powered analytics report."""
    try:
        # Get analytics data for the session
        analytics = analytics_service.get_session_analytics(request.session_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Session not found or no analytics data available")
        
        # Prepare data for LLM
        llm_data = {
            "total_people": analytics.total_people,
            "peak_people_count": analytics.peak_people_count,
            "average_stay_time": analytics.average_stay_time,
            "total_frames": analytics.total_frames,
            "session_duration": (analytics.end_time - analytics.start_time).total_seconds() if analytics.end_time else 0,
            "peak_hours": analytics.peak_hours,
            "heatmap_points_count": len(analytics.heatmap_points)
        }
        
        # Generate report using LLM
        if request.report_type == "summary":
            summary = await llm_service.generate_report(llm_data)
        else:
            # For other report types, generate summary for now
            summary = await llm_service.generate_report(llm_data)
        
        # Convert analytics to dict with ISO format for datetime fields
        analytics_dict = analytics.dict()
        
        # Convert datetime fields to ISO strings
        if analytics.start_time:
            analytics_dict['start_time'] = analytics.start_time.isoformat()
        if analytics.end_time:
            analytics_dict['end_time'] = analytics.end_time.isoformat()
        
        # Convert heatmap points (they are already Pydantic models)
        if analytics.heatmap_points:
            heatmap_points_list = []
            for point in analytics.heatmap_points:
                point_dict = point.dict()
                # Convert datetime to ISO string
                if point_dict.get('timestamp'):
                    point_dict['timestamp'] = point.timestamp.isoformat()
                heatmap_points_list.append(point_dict)
            analytics_dict['heatmap_points'] = heatmap_points_list
        
        # Create response dictionary (FastAPI will handle datetime serialization)
        response_data = {
            "session_id": request.session_id,
            "report_type": request.report_type,
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "analytics": analytics_dict,
            "raw_data": llm_data if request.include_heatmap else None
        }
        
        logger.info("Report generated successfully", session_id=request.session_id, report_type=request.report_type)
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate report", session_id=request.session_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/sessions/{session_id}/analytics")
async def get_session_analytics(
    session_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics data for a session."""
    try:
        # Try to get from cache
        cache_key = f"analytics:{session_id}"
        cached_data = redis_cache.get(cache_key)
        
        if cached_data:
            logger.info("Returning analytics from cache", session_id=session_id)
            return success_response(
                data=cached_data,
                message="Analytics data retrieved successfully (cached)"
            )
        
        # Get from database
        analytics = analytics_service.get_session_analytics(session_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Session not found or no analytics data available")
        
        # Convert to dict with ISO format for datetime fields
        analytics_dict = analytics.dict()
        if analytics_dict.get('start_time'):
            analytics_dict['start_time'] = analytics.start_time.isoformat() if analytics.start_time else None
        if analytics_dict.get('end_time'):
            analytics_dict['end_time'] = analytics.end_time.isoformat() if analytics.end_time else None
        
        # Convert heatmap points timestamps to ISO
        if analytics_dict.get('heatmap_points'):
            for point in analytics_dict['heatmap_points']:
                if point.get('timestamp') and isinstance(point['timestamp'], datetime):
                    point['timestamp'] = point['timestamp'].isoformat()
        
        # Save to cache (TTL: 1 hour)
        redis_cache.set(cache_key, analytics_dict, ttl=3600)
        logger.info("Cached analytics data", session_id=session_id)
        
        return success_response(
            data=analytics_dict,
            message="Analytics data retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session analytics", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/heatmap")
async def get_heatmap_data(
    session_id: str,
    width: int = 100,
    height: int = 100,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get heatmap data for a session."""
    try:
        analytics = analytics_service.get_session_analytics(session_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Session not found or no analytics data available")
        
        # Generate heatmap data
        heatmap_matrix = analytics_service.generate_heatmap_data(
            analytics.heatmap_points, 
            width, 
            height
        )
        
        return success_response(
            data={
                "session_id": session_id,
                "width": width,
                "height": height,
                "heatmap_matrix": heatmap_matrix.tolist(),
                "points_count": len(analytics.heatmap_points)
            },
            message="Heatmap data retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get heatmap data", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/detection-stats")
async def get_detection_statistics(
    session_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detection statistics for a session."""
    try:
        stats = analytics_service.get_detection_statistics(session_id)
        
        return success_response(
            data=stats,
            message="Detection statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Failed to get detection statistics", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    llm_service: LLMService = Depends(get_llm_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get AI-generated session summary."""
    try:
        analytics = analytics_service.get_session_analytics(session_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Session not found or no analytics data available")
        
        # Prepare summary data
        summary_data = {
            "total_people": analytics.total_people,
            "peak_people_count": analytics.peak_people_count,
            "average_stay_time": analytics.average_stay_time,
            "session_duration": (analytics.end_time - analytics.start_time).total_seconds() if analytics.end_time else 0,
            "peak_hours": analytics.peak_hours
        }
        
        # Generate summary
        summary = await llm_service.generate_summary(str(summary_data))
        
        return success_response(
            data={
                "session_id": session_id,
                "summary": summary,
                "analytics": summary_data
            },
            message="Session summary generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate session summary", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
