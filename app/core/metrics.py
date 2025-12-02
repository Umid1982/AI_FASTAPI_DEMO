"""Prometheus metrics definitions."""

from prometheus_client import Counter, Histogram

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Video analysis metrics
video_analysis_total = Counter(
    'video_analysis_total',
    'Total video analysis sessions',
    ['status']
)

# Frame processing metrics
frames_processed_total = Counter(
    'frames_processed_total',
    'Total frames processed',
    ['session_id']
)

# Detection metrics
detections_total = Counter(
    'detections_total',
    'Total object detections',
    ['class_name']
)

