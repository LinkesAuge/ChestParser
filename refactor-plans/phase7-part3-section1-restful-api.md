# Phase 7 Part 3 - Section 1: RESTful API Implementation

## Overview
This document details the implementation of a RESTful API for the Total Battle Analyzer application. The API will provide external access to the application's data and functionality, enabling third-party integrations, data exchange, and remote access capabilities. The API follows REST principles with a resource-oriented architecture, standardized HTTP methods, and comprehensive documentation.

## Key Components

### 1. API Architecture
- Resource-oriented design
- Versioned API endpoints
- Consistent URL structure
- Standard HTTP methods
- JSON response formatting
- Comprehensive error handling

### 2. Resource Endpoints
- Player data resources
- Battle data resources
- Chest analysis resources
- Statistical data resources
- Report generation resources
- Application management resources

### 3. Request/Response Handling
- Input validation
- Content negotiation
- Response formatting
- Pagination and filtering
- Error standardization
- Status code usage

### 4. Performance Optimization
- Response caching
- Rate limiting
- Request throttling
- Asynchronous processing
- Database query optimization
- Resource compression

## Implementation Details

### 1. API Server Setup

```python
# src/goob_ai/api/server.py
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from ..config import ConfigManager
from ..services.data_service import DataService
from ..services.analysis_service import AnalysisService
from ..services.report_service import ReportService
from .router import api_router
from .middleware import RateLimitMiddleware, CacheMiddleware, LoggingMiddleware

logger = logging.getLogger(__name__)

class APIServer:
    """API server for the Total Battle Analyzer application."""
    
    def __init__(
        self, 
        config_manager: ConfigManager,
        data_service: DataService,
        analysis_service: AnalysisService,
        report_service: ReportService,
        host: str = "127.0.0.1",
        port: int = 8000
    ) -> None:
        """
        Initialize the API server.
        
        Args:
            config_manager: Application configuration manager
            data_service: Data access service
            analysis_service: Data analysis service
            report_service: Report generation service
            host: Server host address
            port: Server port
        """
        self.config_manager = config_manager
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Total Battle Analyzer API",
            description="API for accessing and analyzing Total Battle game data",
            version="1.0.0",
            docs_url=None,  # We'll serve custom docs
            redoc_url=None,
        )
        
        # Store services for dependency injection
        self.data_service = data_service
        self.analysis_service = analysis_service
        self.report_service = report_service
        
        # Configure middlewares
        self._configure_middlewares()
        
        # Mount static files
        self._mount_static_files()
        
        # Include API router
        self._include_router()
        
        # Add custom documentation route
        self._add_docs_route()
        
    def _configure_middlewares(self) -> None:
        """Configure API middlewares."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config_manager.get("api", {}).get(
                "cors_origins", ["http://localhost:8080"]
            ),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Rate limiting middleware
        self.app.add_middleware(
            RateLimitMiddleware,
            rate_limit=self.config_manager.get("api", {}).get(
                "rate_limit", 100
            ),  # requests per minute
        )
        
        # Caching middleware
        self.app.add_middleware(
            CacheMiddleware,
            cache_ttl=self.config_manager.get("api", {}).get(
                "cache_ttl", 300
            ),  # seconds
        )
        
        # Logging middleware
        self.app.add_middleware(LoggingMiddleware)
        
    def _mount_static_files(self) -> None:
        """Mount static files for the API."""
        static_dir = Path(self.config_manager.get_app_dir()) / "static"
        static_dir.mkdir(exist_ok=True, parents=True)
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
    def _include_router(self) -> None:
        """Include the API router."""
        self.app.include_router(
            api_router,
            prefix="/api/v1",
            dependencies=[Depends(self._get_services)],
        )
        
    def _add_docs_route(self) -> None:
        """Add custom documentation route."""
        @self.app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html() -> Response:
            """Serve custom Swagger UI."""
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title="Total Battle Analyzer API Documentation",
                swagger_js_url="/static/swagger-ui-bundle.js",
                swagger_css_url="/static/swagger-ui.css",
            )
            
    async def _get_services(self) -> Dict[str, Any]:
        """
        Dependency injection for services.
        
        Returns:
            Dict of services
        """
        return {
            "data_service": self.data_service,
            "analysis_service": self.analysis_service,
            "report_service": self.report_service,
            "config_manager": self.config_manager,
        }
        
    def start(self) -> None:
        """Start the API server."""
        logger.info(f"Starting API server on {self.host}:{self.port}")
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
```

### 2. API Router and Resource Endpoints

```python
# src/goob_ai/api/router.py
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from typing import Dict, List, Any, Optional
import logging
from ..services.data_service import DataService
from ..services.analysis_service import AnalysisService
from ..services.report_service import ReportService
from .models import (
    PlayerData, BattleData, ChestData, 
    AnalysisRequest, AnalysisResponse, 
    ReportRequest, ReportResponse,
    ErrorResponse, PaginatedResponse
)
from .dependencies import get_services, validate_api_key

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter()

# Player data endpoints
player_router = APIRouter(
    prefix="/players",
    tags=["players"],
    dependencies=[Depends(validate_api_key)],
    responses={404: {"model": ErrorResponse}},
)

@player_router.get("/", response_model=PaginatedResponse[PlayerData])
async def get_players(
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(100, ge=1, le=1000, description="Limit response to N items"),
    name: Optional[str] = Query(None, description="Filter by player name"),
    services: Dict[str, Any] = Depends(get_services),
):
    """
    Get list of players with optional filtering.
    """
    data_service = services["data_service"]
    
    # Apply filters
    filters = {}
    if name:
        filters["name"] = name
        
    # Get data from service
    result = data_service.get_players(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    # Format as paginated response
    return {
        "items": result["data"],
        "total": result["total"],
        "page": skip // limit + 1,
        "pages": (result["total"] + limit - 1) // limit,
    }

@player_router.get("/{player_id}", response_model=PlayerData)
async def get_player(
    player_id: str = Path(..., description="Player ID or name"),
    services: Dict[str, Any] = Depends(get_services),
):
    """
    Get detailed information about a player.
    """
    data_service = services["data_service"]
    
    # Get player data
    player = data_service.get_player(player_id)
    
    if not player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
    return player

@player_router.get("/{player_id}/battles", response_model=PaginatedResponse[BattleData])
async def get_player_battles(
    player_id: str = Path(..., description="Player ID or name"),
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(100, ge=1, le=1000, description="Limit response to N items"),
    services: Dict[str, Any] = Depends(get_services),
):
    """
    Get battles for a specific player.
    """
    data_service = services["data_service"]
    
    # Get player battles
    result = data_service.get_player_battles(
        player_id=player_id,
        skip=skip,
        limit=limit
    )
    
    if not result["data"] and skip == 0:
        raise HTTPException(status_code=404, detail=f"No battles found for player {player_id}")
        
    # Format as paginated response
    return {
        "items": result["data"],
        "total": result["total"],
        "page": skip // limit + 1,
        "pages": (result["total"] + limit - 1) // limit,
    }

# More player endpoints...

# Battle data endpoints
battle_router = APIRouter(
    prefix="/battles",
    tags=["battles"],
    dependencies=[Depends(validate_api_key)],
    responses={404: {"model": ErrorResponse}},
)

@battle_router.get("/", response_model=PaginatedResponse[BattleData])
async def get_battles(
    skip: int = Query(0, ge=0, description="Skip first N items"),
    limit: int = Query(100, ge=1, le=1000, description="Limit response to N items"),
    date_from: Optional[str] = Query(None, description="Filter by date (from)"),
    date_to: Optional[str] = Query(None, description="Filter by date (to)"),
    services: Dict[str, Any] = Depends(get_services),
):
    """
    Get list of battles with optional filtering.
    """
    data_service = services["data_service"]
    
    # Apply filters
    filters = {}
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
        
    # Get data from service
    result = data_service.get_battles(
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    # Format as paginated response
    return {
        "items": result["data"],
        "total": result["total"],
        "page": skip // limit + 1,
        "pages": (result["total"] + limit - 1) // limit,
    }

# More battle endpoints...

# Chest data endpoints
chest_router = APIRouter(
    prefix="/chests",
    tags=["chests"],
    dependencies=[Depends(validate_api_key)],
    responses={404: {"model": ErrorResponse}},
)

# Analysis endpoints
analysis_router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    dependencies=[Depends(validate_api_key)],
    responses={404: {"model": ErrorResponse}},
)

@analysis_router.post("/", response_model=AnalysisResponse)
async def perform_analysis(
    analysis_request: AnalysisRequest,
    services: Dict[str, Any] = Depends(get_services),
):
    """
    Perform custom analysis on the data.
    """
    analysis_service = services["analysis_service"]
    
    # Perform analysis
    result = analysis_service.perform_analysis(
        analysis_type=analysis_request.analysis_type,
        parameters=analysis_request.parameters,
        filters=analysis_request.filters
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="No results found for this analysis")
        
    return {
        "analysis_type": analysis_request.analysis_type,
        "parameters": analysis_request.parameters,
        "filters": analysis_request.filters,
        "results": result,
    }

# Report endpoints
report_router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(validate_api_key)],
    responses={404: {"model": ErrorResponse}},
)

@report_router.post("/", response_model=ReportResponse)
async def generate_report(
    report_request: ReportRequest,
    services: Dict[str, Any] = Depends(get_services),
):
    """
    Generate a custom report.
    """
    report_service = services["report_service"]
    
    # Generate report
    result = report_service.generate_report(
        report_type=report_request.report_type,
        parameters=report_request.parameters,
        format=report_request.format
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Failed to generate report")
        
    return {
        "report_type": report_request.report_type,
        "parameters": report_request.parameters,
        "format": report_request.format,
        "content": result["content"],
        "content_type": result["content_type"],
    }

# Include all routers in the main API router
api_router.include_router(player_router)
api_router.include_router(battle_router)
api_router.include_router(chest_router)
api_router.include_router(analysis_router)
api_router.include_router(report_router)
```

### 3. API Models

```python
# src/goob_ai/api/models.py
from typing import Dict, List, Any, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Generic type for paginated responses
T = TypeVar('T')

class ErrorResponse(BaseModel):
    """Error response model."""
    
    detail: str = Field(..., description="Error details")
    code: Optional[str] = Field(None, description="Error code")
    
class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    
class PlayerData(BaseModel):
    """Player data model."""
    
    id: str = Field(..., description="Player ID")
    name: str = Field(..., description="Player name")
    total_battles: int = Field(..., description="Total number of battles")
    total_score: int = Field(..., description="Total score")
    average_score: float = Field(..., description="Average score per battle")
    chest_count: int = Field(..., description="Number of chests obtained")
    last_battle: Optional[datetime] = Field(None, description="Last battle date")
    
class BattleData(BaseModel):
    """Battle data model."""
    
    id: str = Field(..., description="Battle ID")
    player_id: str = Field(..., description="Player ID")
    player_name: str = Field(..., description="Player name")
    date: datetime = Field(..., description="Battle date")
    score: int = Field(..., description="Battle score")
    chest_type: Optional[str] = Field(None, description="Chest type obtained")
    chest_value: Optional[int] = Field(None, description="Chest value")
    source: str = Field(..., description="Battle source")
    
class ChestData(BaseModel):
    """Chest data model."""
    
    type: str = Field(..., description="Chest type")
    count: int = Field(..., description="Number of chests")
    total_value: int = Field(..., description="Total value of chests")
    average_value: float = Field(..., description="Average value per chest")
    
class AnalysisType(str, Enum):
    """Analysis type enum."""
    
    PLAYER_PERFORMANCE = "player_performance"
    CHEST_DISTRIBUTION = "chest_distribution"
    TIME_SERIES = "time_series"
    SOURCE_COMPARISON = "source_comparison"
    PREDICTION = "prediction"
    
class AnalysisRequest(BaseModel):
    """Analysis request model."""
    
    analysis_type: AnalysisType = Field(..., description="Type of analysis to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Analysis parameters")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Data filters")
    
class AnalysisResponse(BaseModel):
    """Analysis response model."""
    
    analysis_type: AnalysisType = Field(..., description="Type of analysis performed")
    parameters: Dict[str, Any] = Field(..., description="Analysis parameters used")
    filters: Dict[str, Any] = Field(..., description="Data filters used")
    results: Dict[str, Any] = Field(..., description="Analysis results")
    
class ReportFormat(str, Enum):
    """Report format enum."""
    
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    
class ReportType(str, Enum):
    """Report type enum."""
    
    PLAYER_PERFORMANCE = "player_performance"
    CHEST_ANALYSIS = "chest_analysis"
    SOURCE_ANALYSIS = "source_analysis"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"
    
class ReportRequest(BaseModel):
    """Report request model."""
    
    report_type: ReportType = Field(..., description="Type of report to generate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    format: ReportFormat = Field(ReportFormat.HTML, description="Report format")
    
class ReportResponse(BaseModel):
    """Report response model."""
    
    report_type: ReportType = Field(..., description="Type of report generated")
    parameters: Dict[str, Any] = Field(..., description="Report parameters used")
    format: ReportFormat = Field(..., description="Report format")
    content: str = Field(..., description="Report content")
    content_type: str = Field(..., description="Content MIME type")
```

### 4. API Dependencies

```python
# src/goob_ai/api/dependencies.py
from typing import Dict, Any, Optional
from fastapi import Depends, Header, HTTPException, Request
import logging

logger = logging.getLogger(__name__)

async def get_services(request: Request) -> Dict[str, Any]:
    """
    Get services from the request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict of services
    """
    return request.app.state.services

async def validate_api_key(
    api_key: str = Header(..., description="API Key for authentication"),
    request: Request = None,
) -> None:
    """
    Validate API key from request header.
    
    Args:
        api_key: API key from request header
        request: FastAPI request object
        
    Raises:
        HTTPException: If API key is invalid
    """
    services = await get_services(request)
    config_manager = services["config_manager"]
    
    # Get valid API keys from configuration
    valid_keys = config_manager.get("api", {}).get("api_keys", [])
    
    if not valid_keys or api_key not in valid_keys:
        logger.warning(f"Invalid API key attempted: {api_key}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
```

### 5. Middleware Implementation

```python
# src/goob_ai/api/middleware.py
from typing import Callable, Dict, Any
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import json

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for API rate limiting."""
    
    def __init__(self, app, rate_limit: int = 100) -> None:
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            rate_limit: Maximum requests per minute
        """
        super().__init__(app)
        self.rate_limit = rate_limit
        
        # Set up Redis connection
        try:
            self.redis = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
            )
            self.redis_available = True
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {str(e)}")
            self.redis_available = False
            
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and apply rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Next middleware function
            
        Returns:
            Response object
        """
        # Skip rate limiting if Redis is not available
        if not self.redis_available:
            return await call_next(request)
            
        # Get client IP for rate limiting
        client_ip = request.client.host
        
        # Get current minute for rate window
        current_minute = int(time.time() / 60)
        rate_key = f"rate_limit:{client_ip}:{current_minute}"
        
        # Check current rate
        current_rate = self.redis.get(rate_key)
        
        if current_rate is None:
            # First request in this minute
            self.redis.setex(rate_key, 60, 1)
        else:
            # Increment request count
            current_rate = int(current_rate)
            
            if current_rate >= self.rate_limit:
                # Rate limit exceeded
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return Response(
                    content=json.dumps({
                        "detail": "Rate limit exceeded. Try again later."
                    }),
                    status_code=429,
                    media_type="application/json",
                )
                
            # Increment request count
            self.redis.incr(rate_key)
            
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        if self.redis_available:
            try:
                current_rate = int(self.redis.get(rate_key) or 1)
                response.headers["X-Rate-Limit-Limit"] = str(self.rate_limit)
                response.headers["X-Rate-Limit-Remaining"] = str(max(0, self.rate_limit - current_rate))
                response.headers["X-Rate-Limit-Reset"] = str((current_minute + 1) * 60)
            except Exception as e:
                logger.error(f"Error setting rate limit headers: {str(e)}")
                
        return response
        
class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for API response caching."""
    
    def __init__(self, app, cache_ttl: int = 300) -> None:
        """
        Initialize cache middleware.
        
        Args:
            app: FastAPI application
            cache_ttl: Cache TTL in seconds
        """
        super().__init__(app)
        self.cache_ttl = cache_ttl
        
        # Set up Redis connection
        try:
            self.redis = redis.Redis(
                host="localhost",
                port=6379,
                db=1,
                decode_responses=True,
            )
            self.redis_available = True
        except Exception as e:
            logger.warning(f"Redis not available for caching: {str(e)}")
            self.redis_available = False
            
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and apply caching.
        
        Args:
            request: FastAPI request
            call_next: Next middleware function
            
        Returns:
            Response object
        """
        # Skip for non-GET requests
        if request.method != "GET":
            return await call_next(request)
            
        # Skip if Redis is not available
        if not self.redis_available:
            return await call_next(request)
            
        # Create cache key from request
        cache_key = f"cache:{request.url.path}:{hash(str(request.query_params))}"
        
        # Check if response is in cache
        cached_response = self.redis.get(cache_key)
        
        if cached_response:
            # Return cached response
            cached_data = json.loads(cached_response)
            
            return Response(
                content=cached_data["content"],
                status_code=cached_data["status_code"],
                headers=cached_data["headers"],
                media_type=cached_data["media_type"],
            )
            
        # Process the request
        response = await call_next(request)
        
        # Only cache successful responses
        if response.status_code == 200 and self.redis_available:
            try:
                # Get response body
                response_body = [section async for section in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(iter(response_body))
                
                # Cache response data
                response_data = {
                    "content": b"".join(response_body).decode(),
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type,
                }
                
                # Store in cache
                self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(response_data),
                )
                
                # Add cache header
                response.headers["X-Cache"] = "MISS"
            except Exception as e:
                logger.error(f"Error caching response: {str(e)}")
        else:
            # Add cache header for non-cached responses
            response.headers["X-Cache"] = "BYPASS"
            
        return response
        
class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for API request/response logging."""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: FastAPI request
            call_next: Next middleware function
            
        Returns:
            Response object
        """
        # Start timing
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Log request
        logger.info(f"API Request: {method} {path} from {client_ip}")
        
        # Process the request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"API Response: {method} {path} - Status: {response.status_code} - "
            f"Duration: {duration:.4f}s"
        )
        
        return response
```

### 6. API Service Integration

```python
# src/goob_ai/services/api_service.py
from typing import Dict, Any, Optional
import logging
import threading
from pathlib import Path
from ..config import ConfigManager
from .data_service import DataService
from .analysis_service import AnalysisService
from .report_service import ReportService
from ..api.server import APIServer

logger = logging.getLogger(__name__)

class APIService:
    """Service for managing the API server."""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        data_service: DataService,
        analysis_service: AnalysisService,
        report_service: ReportService,
    ) -> None:
        """
        Initialize the API service.
        
        Args:
            config_manager: Application configuration manager
            data_service: Data access service
            analysis_service: Data analysis service
            report_service: Report generation service
        """
        self.config_manager = config_manager
        self.data_service = data_service
        self.analysis_service = analysis_service
        self.report_service = report_service
        self.api_server: Optional[APIServer] = None
        self.api_thread: Optional[threading.Thread] = None
        
    def start_api_server(self) -> bool:
        """
        Start the API server in a background thread.
        
        Returns:
            True if server started successfully, False otherwise
        """
        if self.api_thread and self.api_thread.is_alive():
            logger.warning("API server is already running")
            return False
            
        # Get API configuration
        api_config = self.config_manager.get("api", {})
        host = api_config.get("host", "127.0.0.1")
        port = api_config.get("port", 8000)
        
        # Create API server
        self.api_server = APIServer(
            config_manager=self.config_manager,
            data_service=self.data_service,
            analysis_service=self.analysis_service,
            report_service=self.report_service,
            host=host,
            port=port,
        )
        
        # Start server in a separate thread
        self.api_thread = threading.Thread(
            target=self.api_server.start,
            daemon=True,
        )
        self.api_thread.start()
        
        logger.info(f"API server started at http://{host}:{port}")
        return True
        
    def stop_api_server(self) -> bool:
        """
        Stop the API server.
        
        Returns:
            True if server stopped successfully, False otherwise
        """
        if not self.api_thread or not self.api_thread.is_alive():
            logger.warning("API server is not running")
            return False
            
        # No direct way to stop uvicorn server, but we can try to clean up
        self.api_server = None
        self.api_thread = None
        
        logger.info("API server stopped")
        return True
        
    def is_api_server_running(self) -> bool:
        """
        Check if the API server is running.
        
        Returns:
            True if server is running, False otherwise
        """
        return self.api_thread is not None and self.api_thread.is_alive()
        
    def get_api_url(self) -> Optional[str]:
        """
        Get the URL of the API server.
        
        Returns:
            API server URL or None if server is not running
        """
        if not self.is_api_server_running() or not self.api_server:
            return None
            
        return f"http://{self.api_server.host}:{self.api_server.port}"
        
    def generate_api_key(self) -> str:
        """
        Generate a new API key.
        
        Returns:
            New API key
        """
        import secrets
        import string
        
        # Generate a random API key
        alphabet = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(alphabet) for i in range(32))
        
        # Add to configuration
        api_config = self.config_manager.get("api", {})
        api_keys = api_config.get("api_keys", [])
        api_keys.append(api_key)
        
        # Update configuration
        api_config["api_keys"] = api_keys
        self.config_manager.set("api", api_config)
        self.config_manager.save()
        
        return api_key
        
    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            api_key: API key to revoke
            
        Returns:
            True if key was revoked, False otherwise
        """
        # Get API configuration
        api_config = self.config_manager.get("api", {})
        api_keys = api_config.get("api_keys", [])
        
        # Check if key exists
        if api_key not in api_keys:
            return False
            
        # Remove key
        api_keys.remove(api_key)
        
        # Update configuration
        api_config["api_keys"] = api_keys
        self.config_manager.set("api", api_config)
        self.config_manager.save()
        
        return True
        
    def get_api_keys(self) -> list[str]:
        """
        Get list of active API keys.
        
        Returns:
            List of API keys
        """
        # Get API configuration
        api_config = self.config_manager.get("api", {})
        return api_config.get("api_keys", [])
```

## API Documentation

The API documentation is automatically generated using FastAPI's integrated OpenAPI support. This provides an interactive API documentation interface that allows developers to:

1. Browse available endpoints
2. View request/response models
3. Test API calls directly from the documentation
4. See detailed parameter descriptions
5. Understand authentication requirements

FastAPI generates this documentation automatically based on the API route definitions, request/response models, and Python type hints. Additionally, docstrings are used to provide detailed descriptions of each endpoint's functionality.

## Implementation Steps

### Week 1: Core API Infrastructure (Days 1-4)
1. Set up FastAPI server and basic middleware
2. Implement core data endpoints for players, battles, and chests
3. Create Pydantic models for request/response validation
4. Add dependency injection for services

### Week 2: Authentication and Advanced Features (Days 5-7)
1. Implement API key authentication
2. Add rate limiting and caching middleware
3. Create analysis and report endpoints
4. Set up API documentation and testing tools

## Dependencies
- Python 3.8+
- FastAPI (for API implementation)
- Uvicorn (for ASGI server)
- Pydantic (for data validation)
- Redis (for caching and rate limiting)

## Testing Strategy
1. Unit tests for API endpoints using FastAPI TestClient
2. Integration tests for API with database
3. Load testing with locust for performance validation
4. Security testing for authentication mechanisms

## Success Criteria
1. All resource endpoints function correctly with proper validation
2. API performance remains stable under load
3. Authentication system prevents unauthorized access
4. Documentation is complete and accurate
5. Rate limiting and caching provide appropriate protection and performance 