import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
import time
import logging

from app.core.config import settings

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_requests_total', 
    'Total API requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds', 
    'API request duration'
)

ACTIVE_DEVICES = Gauge(
    'active_devices_total', 
    'Number of active devices'
)

NOTIFICATION_QUEUE_SIZE = Gauge(
    'notification_queue_size', 
    'Pending notifications'
)

MATCHES_CREATED = Counter(
    'job_matches_created_total',
    'Total job matches created'
)

NOTIFICATIONS_SENT = Counter(
    'push_notifications_sent_total',
    'Total push notifications sent',
    ['status']
)

# Structured logging setup
def setup_logging():
    """Setup structured logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

class MonitoringMiddleware:
    """Middleware for request monitoring and logging"""
    
    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        request = Request(scope, receive)
        
        # Create response wrapper to capture status
        response_info = {"status_code": 200}
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_info["status_code"] = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            response_info["status_code"] = 500
            self.logger.error("Request failed", 
                            method=request.method,
                            path=request.url.path,
                            error=str(e))
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            method = request.method
            path = request.url.path
            status = response_info["status_code"]
            
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
            REQUEST_DURATION.observe(duration)
            
            # Log request
            self.logger.info("api_request",
                           method=method,
                           path=path,
                           status=status,
                           duration=duration,
                           user_agent=request.headers.get('user-agent', ''),
                           ip=request.client.host if request.client else '')

def setup_monitoring(app):
    """Setup monitoring middleware and endpoints"""
    if settings.PROMETHEUS_ENABLED:
        # Add monitoring middleware
        app.add_middleware(MonitoringMiddleware)
        
        # Add metrics endpoint
        @app.get("/metrics")
        async def get_metrics():
            return Response(
                generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
    
    # Setup structured logging
    setup_logging()

# Monitoring utilities
class MetricsCollector:
    """Utility class for collecting custom metrics"""
    
    @staticmethod
    def record_device_registration():
        """Record device registration"""
        # This would be called from the device registration endpoint
        pass
    
    @staticmethod
    def record_match_created():
        """Record job match creation"""
        MATCHES_CREATED.inc()
    
    @staticmethod
    def record_notification_sent(status: str):
        """Record push notification sent"""
        NOTIFICATIONS_SENT.labels(status=status).inc()
    
    @staticmethod
    def update_active_devices(count: int):
        """Update active devices gauge"""
        ACTIVE_DEVICES.set(count)
    
    @staticmethod
    def update_notification_queue_size(size: int):
        """Update notification queue size"""
        NOTIFICATION_QUEUE_SIZE.set(size)

# Global metrics collector instance
metrics = MetricsCollector()