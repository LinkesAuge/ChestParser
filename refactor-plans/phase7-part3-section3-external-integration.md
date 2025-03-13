# Phase 7 Part 3 - Section 3: External Platform Integration

## Overview
This document details the implementation of external platform integration for the Total Battle Analyzer API. The system enables seamless data exchange and interaction with third-party platforms, game servers, data sources, and other external systems. It provides a flexible framework for connecting to various external services, transforming data between different formats, and implementing webhook-based event notifications.

## Key Components

### 1. Integration Framework
- Generic connector interface
- Platform-specific adapters
- Connection management
- Error handling and retry mechanisms
- Caching strategy for external data

### 2. Data Exchange Services
- Data import/export capabilities
- Format transformation (JSON, XML, CSV)
- Schema validation
- Data synchronization mechanisms
- Bulk data operations

### 3. Webhook System
- Event subscription management
- Outgoing webhook triggers
- Incoming webhook handlers
- Webhook security (signatures, HMAC)
- Delivery confirmation and retry logic

### 4. Platform-Specific Integrations
- Total Battle game servers
- Cloud storage providers (Google Drive, Dropbox)
- Social media platforms
- Collaboration tools (Discord, Slack)
- Data visualization services

## Implementation Details

### 1. Integration Framework Core

```python
# src/goob_ai/integration/connector.py
from typing import Dict, Any, List, Optional, Type, TypeVar, Generic, Protocol, Union
from abc import ABC, abstractmethod
import logging
import time
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import httpx
from pydantic import BaseModel, Field
from ..config import ConfigManager
from ..utils.cache import CacheManager

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ConnectorConfig(BaseModel):
    """Configuration for external platform connector."""
    
    platform_id: str = Field(..., description="Unique identifier for the platform")
    base_url: str = Field(..., description="Base URL for API requests")
    auth_type: str = Field("none", description="Authentication type (none, basic, bearer, apikey)")
    auth_credentials: Dict[str, str] = Field(default_factory=dict, description="Authentication credentials")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    headers: Dict[str, str] = Field(default_factory=dict, description="Default headers for requests")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific parameters")
    

class ConnectorResponse(BaseModel):
    """Response from external platform connector."""
    
    success: bool = Field(..., description="Whether the request was successful")
    status_code: Optional[int] = Field(None, description="HTTP status code (if applicable)")
    data: Any = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message (if any)")
    headers: Dict[str, str] = Field(default_factory=dict, description="Response headers")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    

class ExternalPlatformConnector(ABC):
    """Base class for external platform connectors."""
    
    def __init__(self, config: ConnectorConfig, cache_manager: Optional[CacheManager] = None) -> None:
        """
        Initialize external platform connector.
        
        Args:
            config: Connector configuration
            cache_manager: Cache manager for caching responses
        """
        self.config = config
        self.cache_manager = cache_manager
        self.client = self._create_client()
        
        # Load platform-specific configuration
        self._initialize_platform()
        
    def _create_client(self) -> httpx.AsyncClient:
        """
        Create HTTP client for the connector.
        
        Returns:
            Asynchronous HTTP client
        """
        # Configure client with default settings
        client_kwargs = {
            "base_url": self.config.base_url,
            "timeout": self.config.timeout,
            "headers": self.config.headers.copy(),
        }
        
        # Add authentication if needed
        if self.config.auth_type == "basic":
            client_kwargs["auth"] = (
                self.config.auth_credentials.get("username", ""),
                self.config.auth_credentials.get("password", "")
            )
            
        # Create client
        return httpx.AsyncClient(**client_kwargs)
        
    def _initialize_platform(self) -> None:
        """Initialize platform-specific configuration."""
        # Override in subclasses to perform platform-specific initialization
        pass
        
    async def _add_auth_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Add authentication headers to request.
        
        Args:
            headers: Existing headers
            
        Returns:
            Headers with authentication added
        """
        result = headers.copy()
        
        # Add authentication headers based on auth type
        if self.config.auth_type == "bearer":
            result["Authorization"] = f"Bearer {self.config.auth_credentials.get('token', '')}"
        elif self.config.auth_type == "apikey":
            key_name = self.config.auth_credentials.get("key_name", "X-API-Key")
            key_value = self.config.auth_credentials.get("key_value", "")
            result[key_name] = key_value
            
        return result
        
    async def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = False,
        cache_ttl: Optional[int] = None,
    ) -> ConnectorResponse:
        """
        Make HTTP request to external platform.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Request headers
            use_cache: Whether to use cache for GET requests
            cache_ttl: Cache TTL in seconds
            
        Returns:
            Connector response
        """
        # Prepare request
        url = path if path.startswith(("http://", "https://")) else path
        req_headers = self.config.headers.copy()
        if headers:
            req_headers.update(headers)
            
        # Add authentication headers
        req_headers = await self._add_auth_headers(req_headers)
        
        # Check cache for GET requests
        cache_key = None
        if use_cache and method.upper() == "GET" and self.cache_manager:
            cache_key = f"{self.config.platform_id}:{method}:{url}:{json.dumps(params or {})}"
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return ConnectorResponse(
                    success=True,
                    data=cached_data,
                    headers={},
                    timestamp=datetime.now()
                )
                
        # Make request with retry logic
        for attempt in range(self.config.max_retries + 1):
            try:
                # Make request
                start_time = time.time()
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=req_headers,
                    timeout=self.config.timeout
                )
                duration = time.time() - start_time
                
                # Log request details
                logger.debug(
                    f"{method} {url} completed in {duration:.2f}s with status {response.status_code}"
                )
                
                # Create response object
                response_headers = dict(response.headers)
                
                if 200 <= response.status_code < 300:
                    # Success
                    response_data = None
                    content_type = response.headers.get("content-type", "")
                    
                    if "application/json" in content_type:
                        response_data = response.json()
                    else:
                        response_data = response.text
                        
                    result = ConnectorResponse(
                        success=True,
                        status_code=response.status_code,
                        data=response_data,
                        headers=response_headers,
                        timestamp=datetime.now()
                    )
                    
                    # Cache successful GET responses
                    if cache_key and method.upper() == "GET" and self.cache_manager:
                        await self.cache_manager.set(
                            cache_key, 
                            response_data, 
                            ttl=cache_ttl or 300  # Default 5 minutes
                        )
                        
                    return result
                else:
                    # Error
                    error_message = f"HTTP {response.status_code}: {response.text}"
                    
                    # Check if we should retry based on status code
                    if (
                        attempt < self.config.max_retries and 
                        response.status_code in (429, 500, 502, 503, 504)
                    ):
                        retry_delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Request failed with {error_message}. "
                            f"Retrying in {retry_delay:.2f}s ({attempt + 1}/{self.config.max_retries})"
                        )
                        await asyncio.sleep(retry_delay)
                        continue
                        
                    return ConnectorResponse(
                        success=False,
                        status_code=response.status_code,
                        error=error_message,
                        headers=response_headers,
                        timestamp=datetime.now()
                    )
                    
            except httpx.RequestError as e:
                # Connection error
                error_message = f"Request error: {str(e)}"
                
                if attempt < self.config.max_retries:
                    retry_delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Request failed with {error_message}. "
                        f"Retrying in {retry_delay:.2f}s ({attempt + 1}/{self.config.max_retries})"
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                    
                return ConnectorResponse(
                    success=False,
                    error=error_message,
                    timestamp=datetime.now()
                )
                
        # This should not be reached, but just in case
        return ConnectorResponse(
            success=False,
            error="Maximum retries exceeded",
            timestamp=datetime.now()
        )
        
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
    ) -> ConnectorResponse:
        """
        Make GET request to external platform.
        
        Args:
            path: Request path
            params: Query parameters
            headers: Request headers
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds
            
        Returns:
            Connector response
        """
        return await self._make_request(
            method="GET",
            path=path,
            params=params,
            headers=headers,
            use_cache=use_cache,
            cache_ttl=cache_ttl
        )
        
    async def post(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ConnectorResponse:
        """
        Make POST request to external platform.
        
        Args:
            path: Request path
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Request headers
            
        Returns:
            Connector response
        """
        return await self._make_request(
            method="POST",
            path=path,
            params=params,
            data=data,
            json_data=json_data,
            headers=headers
        )
        
    async def put(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ConnectorResponse:
        """
        Make PUT request to external platform.
        
        Args:
            path: Request path
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Request headers
            
        Returns:
            Connector response
        """
        return await self._make_request(
            method="PUT",
            path=path,
            params=params,
            data=data,
            json_data=json_data,
            headers=headers
        )
        
    async def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ConnectorResponse:
        """
        Make DELETE request to external platform.
        
        Args:
            path: Request path
            params: Query parameters
            headers: Request headers
            
        Returns:
            Connector response
        """
        return await self._make_request(
            method="DELETE",
            path=path,
            params=params,
            headers=headers
        )
        
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to external platform.
        
        Returns:
            True if connection is successful, False otherwise
        """
        pass
        
    async def close(self) -> None:
        """Close the connector and release resources."""
        await self.client.aclose()


class ConnectorRegistry:
    """Registry for external platform connectors."""
    
    def __init__(self, config_manager: ConfigManager, cache_manager: Optional[CacheManager] = None) -> None:
        """
        Initialize connector registry.
        
        Args:
            config_manager: Configuration manager
            cache_manager: Cache manager for caching responses
        """
        self.config_manager = config_manager
        self.cache_manager = cache_manager
        self.connectors: Dict[str, ExternalPlatformConnector] = {}
        self.connector_classes: Dict[str, Type[ExternalPlatformConnector]] = {}
        
    def register_connector_class(self, platform_id: str, connector_class: Type[ExternalPlatformConnector]) -> None:
        """
        Register connector class for platform.
        
        Args:
            platform_id: Platform identifier
            connector_class: Connector class
        """
        self.connector_classes[platform_id] = connector_class
        
    async def get_connector(self, platform_id: str) -> Optional[ExternalPlatformConnector]:
        """
        Get connector for platform.
        
        Args:
            platform_id: Platform identifier
            
        Returns:
            Connector instance or None if not found
        """
        # Return existing connector if already initialized
        if platform_id in self.connectors:
            return self.connectors[platform_id]
            
        # Check if connector class is registered
        if platform_id not in self.connector_classes:
            logger.error(f"No connector class registered for platform: {platform_id}")
            return None
            
        # Get platform configuration
        platforms_config = self.config_manager.get("integration", {}).get("platforms", {})
        if platform_id not in platforms_config:
            logger.error(f"No configuration found for platform: {platform_id}")
            return None
            
        # Create connector config
        config_data = platforms_config[platform_id]
        config = ConnectorConfig(
            platform_id=platform_id,
            **config_data
        )
        
        # Create connector instance
        connector_class = self.connector_classes[platform_id]
        connector = connector_class(config, self.cache_manager)
        
        # Store in registry
        self.connectors[platform_id] = connector
        
        return connector
        
    async def close_all(self) -> None:
        """Close all connectors and release resources."""
        for connector in self.connectors.values():
            await connector.close()
            
        self.connectors.clear()

## Implementation Steps

The implementation of the External Platform Integration system will be carried out in several phases. Each phase focuses on specific components and builds on the previous work.

### Phase 1: Core Integration Framework (Days 1-7)

1. **Setup Integration Framework (Days 1-2)**
   - Implement `ConnectorConfig` and `ConnectorResponse` classes
   - Create the abstract `ExternalPlatformConnector` base class
   - Develop the `ConnectorRegistry` for managing platform connectors

2. **Data Exchange Services (Days 3-4)**
   - Create the `DataExchangeService` class
   - Implement data import/export functionality
   - Support for JSON, XML, and CSV transformations
   - Develop schema validation logic

3. **Total Battle Game Server Integration (Days 5-7)**
   - Implement the `TotalBattleConnector` class for game server integration
   - Create methods for player data, battle data, and chest data access
   - Develop connection testing and authentication logic
   - Add caching strategy for external data

### Phase 2: Webhook System (Days 8-14)

1. **Webhook Service Core (Days 8-9)**
   - Implement the `WebhookEvent` and `WebhookSubscription` models
   - Create the `WebhookService` class
   - Implement subscription management functionality
   - Develop storage and persistence mechanisms

2. **Event Delivery System (Days 10-12)**
   - Create delivery queue processing infrastructure
   - Implement webhook delivery logic with retry mechanisms
   - Develop webhook signature generation for security
   - Create event handler registration and notification system

3. **API Integration (Days 13-14)**
   - Create the `integration_router` for FastAPI
   - Implement webhook subscription endpoints
   - Create platform testing endpoints
   - Implement data import/export endpoints
   - Develop event triggering endpoint

### Phase 3: Cloud Storage & Social Media Integration (Days 15-21)

1. **Cloud Storage Integration (Days 15-17)**
   - Create connectors for Google Drive and Dropbox
   - Implement file upload, download, and listing functionality
   - Develop authentication flows and token management
   - Create data synchronization capabilities

2. **Collaboration Tool Integration (Days 18-19)**
   - Implement Discord and Slack connectors
   - Create notification and alert functionality
   - Develop message formatting for different platforms
   - Add webhook support for incoming messages

3. **Data Visualization Services (Days 20-21)**
   - Create connectors for data visualization platforms
   - Implement chart and visualization export functionality
   - Develop embedding and sharing capabilities
   - Create data filtering and transformation options

## Dependencies

The External Platform Integration system relies on the following dependencies:

1. Python 3.8+
2. httpx (for asynchronous HTTP requests)
3. pydantic (for data validation and serialization)
4. FastAPI (for API endpoints)
5. python-multipart (for handling multipart form data)
6. cryptography (for security and signature generation)
7. xmltodict (for XML processing)
8. ujson (for faster JSON processing)

## Testing Strategy

1. **Unit Tests**
   - Test each connector and service independently
   - Validate data transformation between formats
   - Verify webhook delivery and retry logic
   - Test security features including signature generation

2. **Integration Tests**
   - Test the complete flow from external data retrieval to processing
   - Verify webhook subscription and event delivery
   - Test API endpoints with mock data
   - Validate error handling and retry mechanisms

3. **External Platform Integration Tests**
   - Create test accounts on external platforms
   - Verify authentication flows with real endpoints
   - Test data synchronization with actual services
   - Validate webhook delivery to test endpoints

4. **Performance Testing**
   - Measure throughput for data import/export operations
   - Test webhook delivery under load
   - Verify caching effectiveness
   - Test recovery from external service failures

## Security Considerations

1. **Authentication Security**
   - Store API keys and tokens securely
   - Implement token rotation for long-lived connections
   - Use OAuth 2.0 for secure authentication flows
   - Implement secure storage for credentials

2. **Webhook Security**
   - Generate and verify webhook signatures using HMAC
   - Implement rate limiting for webhook subscriptions
   - Validate webhook URLs to prevent server-side request forgery
   - Use HTTPS for all webhook endpoints

3. **Data Security**
   - Encrypt sensitive data in transit and at rest
   - Implement proper error handling to prevent data leakage
   - Validate input data to prevent injection attacks
   - Apply proper access control to API endpoints

## Next Steps

1. Implement the core integration framework
2. Develop platform-specific connectors, starting with Total Battle
3. Create the webhook system
4. Implement API endpoints
5. Develop cloud storage and collaboration tool integrations
6. Create comprehensive documentation and examples
7. Conduct thorough testing of all components 