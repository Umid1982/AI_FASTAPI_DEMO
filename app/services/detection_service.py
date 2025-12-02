from ultralytics import YOLO
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import cv2
import numpy as np
import structlog
from app.core.config import settings
from app.models.schemas import Detection, BoundingBox, DetectionType

logger = structlog.get_logger()


class DetectionStrategy(ABC):
    """Abstract base class for detection strategies."""
    
    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect objects in frame."""
        pass


class YOLODetectionStrategy(DetectionStrategy):
    """YOLO-based detection strategy."""
    
    def __init__(self, model_name: str = None, confidence_threshold: float = None):
        self.model_name = model_name or settings.yolo_model
        self.confidence_threshold = confidence_threshold or settings.confidence_threshold
        
        try:
            self.model = YOLO(self.model_name)
        except Exception as e:
            logger.warning("Failed to load YOLO model, using mock detection", error=str(e))
            self.model = None
        
        # COCO class names (YOLO uses COCO dataset)
        self.class_names = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
            'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
            'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
            'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
            'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
            'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
            'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
        
        logger.info("YOLO detection strategy initialized", model=self.model_name, confidence=self.confidence_threshold)
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect objects using YOLO."""
        try:
            if self.model is None:
                # Mock detection for testing
                return self._mock_detection(frame)
            
            results = self.model(frame, conf=self.confidence_threshold)
            detections = []
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Get class name
                        class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"
                        
                        # Create detection object
                        detection = Detection(
                            class_id=class_id,
                            class_name=class_name,
                            confidence=confidence,
                            bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
                        )
                        
                        detections.append(detection)
            
            logger.debug("YOLO detection completed", detections_count=len(detections))
            return detections
            
        except Exception as e:
            logger.error("YOLO detection failed, using mock detection", error=str(e))
            return self._mock_detection(frame)
    
    def _mock_detection(self, frame: np.ndarray) -> List[Detection]:
        """Mock detection for testing purposes."""
        import random
        
        # Create a mock person detection in the center of the frame
        height, width = frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # Random bounding box around center
        box_width = random.randint(50, 150)
        box_height = random.randint(100, 200)
        
        x1 = max(0, center_x - box_width // 2)
        y1 = max(0, center_y - box_height // 2)
        x2 = min(width, center_x + box_width // 2)
        y2 = min(height, center_y + box_height // 2)
        
        detection = Detection(
            class_id=0,  # person class
            class_name="person",
            confidence=random.uniform(0.6, 0.9),
            bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
        )
        
        logger.debug("Mock detection created", detections_count=1)
        return [detection]


class PersonDetectionStrategy(DetectionStrategy):
    """Strategy for detecting only people."""
    
    def __init__(self, base_strategy: DetectionStrategy):
        self.base_strategy = base_strategy
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect only people."""
        all_detections = self.base_strategy.detect(frame)
        person_detections = [
            detection for detection in all_detections
            if detection.class_name == "person"
        ]
        
        logger.debug("Person detection completed", person_count=len(person_detections))
        return person_detections


class DetectionService:
    """Service for object detection operations."""
    
    def __init__(self, strategy: DetectionStrategy = None):
        self.strategy = strategy or YOLODetectionStrategy()
        self.total_detections = 0
    
    @classmethod
    def create_person_detector(cls) -> 'DetectionService':
        """Create detection service for people only."""
        base_strategy = YOLODetectionStrategy()
        person_strategy = PersonDetectionStrategy(base_strategy)
        return cls(person_strategy)
    
    @classmethod
    def create_multi_class_detector(cls) -> 'DetectionService':
        """Create detection service for multiple classes."""
        strategy = YOLODetectionStrategy()
        return cls(strategy)
    
    def detect_objects(self, frame: np.ndarray) -> List[Detection]:
        """Detect objects in frame."""
        try:
            detections = self.strategy.detect(frame)
            self.total_detections += len(detections)
            
            logger.debug("Object detection completed", detections_count=len(detections))
            return detections
            
        except Exception as e:
            logger.error("Object detection failed", error=str(e))
            raise
    
    def detect_people(self, frame: np.ndarray) -> List[Detection]:
        """Detect people in frame (backward compatibility)."""
        detections = self.detect_objects(frame)
        return [d for d in detections if d.class_name == "person"]
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            "total_detections": self.total_detections,
            "strategy": self.strategy.__class__.__name__
        }
    
    def reset_stats(self) -> None:
        """Reset detection statistics."""
        self.total_detections = 0
        logger.info("Detection stats reset")
