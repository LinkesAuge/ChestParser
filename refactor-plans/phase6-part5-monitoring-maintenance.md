# Phase 6 Part 5: Monitoring and Maintenance

## Overview

This document outlines the fifth and final part of Phase 6, which focuses on implementing comprehensive monitoring and maintenance procedures for the Total Battle Analyzer application. Having established a CI/CD pipeline and deployment processes in previous parts, this part will ensure the application remains reliable, performant, and secure in production over time.

Proper monitoring and maintenance are critical to maintaining a high-quality application, detecting issues before they impact users, and ensuring that the system evolves smoothly. This document details the implementation of alerting systems, scheduled maintenance procedures, performance monitoring, and continuous improvement processes.

## Implementation Tasks

### 1. Proactive Monitoring System

#### 1.1 System Health Monitoring

We'll implement a comprehensive system health monitoring solution using Prometheus and Grafana:

```python
# app/monitoring/health.py
import psutil
import logging
import threading
import time
from typing import Dict, Any, List, Optional
from prometheus_client import Gauge

logger = logging.getLogger(__name__)

# Define metrics
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_bytes', 'Memory usage in bytes')
SYSTEM_DISK_USAGE = Gauge('system_disk_usage_percent', 'Disk usage percentage')
SYSTEM_OPEN_FILES = Gauge('system_open_files_count', 'Number of open files')
SYSTEM_UPTIME = Gauge('system_uptime_seconds', 'System uptime in seconds')

class SystemHealthMonitor:
    """Monitors system health metrics."""
    
    def __init__(self, interval: int = 60):
        """Initialize the system health monitor.
        
        Args:
            interval: Interval in seconds between health checks
        """
        self.interval = interval
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Start the health monitoring."""
        with self._lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self._thread.start()
                logger.info(f"System health monitoring started with interval {self.interval}s")
    
    def stop(self) -> None:
        """Stop the health monitoring."""
        with self._lock:
            if self._running:
                self._running = False
                if self._thread:
                    self._thread.join(timeout=5)
                logger.info("System health monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                self._collect_metrics()
            except Exception as e:
                logger.error(f"Error collecting health metrics: {str(e)}")
            
            time.sleep(self.interval)
    
    def _collect_metrics(self) -> None:
        """Collect and update all system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        SYSTEM_CPU_USAGE.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        SYSTEM_MEMORY_USAGE.set(memory.used)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        SYSTEM_DISK_USAGE.set(disk.percent)
        
        # Open files (Linux only)
        try:
            open_files = len(psutil.Process().open_files())
            SYSTEM_OPEN_FILES.set(open_files)
        except (psutil.AccessDenied, AttributeError):
            pass
        
        # Uptime
        uptime = time.time() - psutil.boot_time()
        SYSTEM_UPTIME.set(uptime)
        
        logger.debug(f"Health metrics collected: CPU {cpu_percent}%, "
                    f"Memory {memory.used / (1024*1024):.1f}MB, "
                    f"Disk {disk.percent}%")

# Create singleton instance
health_monitor = SystemHealthMonitor()

def init_app(app) -> None:
    """Initialize health monitoring for the application."""
    health_monitor.start()
    
    # Register shutdown handler
    if hasattr(app, 'teardown_appcontext'):
        @app.teardown_appcontext
        def shutdown_health_monitor(exception=None):
            health_monitor.stop()
```

#### 1.2 Performance Metrics Collection

We'll implement detailed application performance monitoring:

```python
# app/monitoring/performance.py
import time
import functools
import threading
from typing import Dict, Any, Callable, Optional
from prometheus_client import Summary, Histogram, Counter, Gauge

# Define metrics
REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint', 'method']
)

DB_QUERY_LATENCY = Histogram(
    'app_db_query_latency_seconds',
    'Database query latency in seconds',
    ['query_type']
)

FUNCTION_LATENCY = Summary(
    'app_function_latency_seconds',
    'Function execution latency in seconds',
    ['function_name']
)

ERROR_COUNTER = Counter(
    'app_error_count',
    'Number of errors',
    ['type', 'location']
)

ACTIVE_USERS = Gauge(
    'app_active_users',
    'Number of active users'
)

# Request latency middleware for Flask
def init_app(app):
    """Initialize performance monitoring for a Flask application."""
    @app.before_request
    def before_request():
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        latency = time.time() - request.start_time
        endpoint = request.endpoint or 'unknown'
        REQUEST_LATENCY.labels(
            endpoint=endpoint,
            method=request.method
        ).observe(latency)
        return response
    
    # Database query instrumentation
    if hasattr(app, 'db'):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            start_time = conn.info['query_start_time'].pop()
            latency = time.time() - start_time
            query_type = statement.split(' ')[0].lower()
            DB_QUERY_LATENCY.labels(query_type=query_type).observe(latency)

# Function timing decorator
def monitor_performance(function_name: Optional[str] = None):
    """Decorator to monitor function performance."""
    def decorator(func):
        nonlocal function_name
        if function_name is None:
            function_name = func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                latency = time.time() - start_time
                FUNCTION_LATENCY.labels(function_name=function_name).observe(latency)
        
        return wrapper
    
    if callable(function_name):
        # Used as @monitor_performance without parentheses
        func = function_name
        function_name = func.__name__
        return decorator(func)
    
    # Used as @monitor_performance() or @monitor_performance('name')
    return decorator

# Error tracking
def track_error(error_type: str, location: str) -> None:
    """Track an error occurrence."""
    ERROR_COUNTER.labels(type=error_type, location=location).inc()

# Active user tracking
class UserTracker:
    """Tracks active users in the application."""
    
    def __init__(self):
        """Initialize the user tracker."""
        self.active_users = set()
        self._lock = threading.Lock()
    
    def track_login(self, user_id: str) -> None:
        """Track a user login."""
        with self._lock:
            self.active_users.add(user_id)
            ACTIVE_USERS.set(len(self.active_users))
    
    def track_logout(self, user_id: str) -> None:
        """Track a user logout."""
        with self._lock:
            if user_id in self.active_users:
                self.active_users.remove(user_id)
                ACTIVE_USERS.set(len(self.active_users))

# Create singleton instance
user_tracker = UserTracker()

#### 1.3 Real-Time Alerting

We'll set up real-time alerting based on our metrics:

```yaml
# config/prometheus/alert_rules.yml
groups:
  - name: app_alerts
    rules:
      # High CPU usage alert
      - alert: HighCpuUsage
        expr: system_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage ({{ $value }}%)"
          description: "CPU usage has been above 80% for more than 5 minutes."
      
      # High memory usage alert
      - alert: HighMemoryUsage
        expr: (system_memory_usage_bytes / node_memory_MemTotal_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage ({{ $value | humanizePercentage }})"
          description: "Memory usage has been above 85% for more than 5 minutes."
      
      # High disk usage alert
      - alert: HighDiskUsage
        expr: system_disk_usage_percent > 85
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage ({{ $value }}%)"
          description: "Disk usage has been above 85% for more than 15 minutes."
      
      # High error rate alert
      - alert: HighErrorRate
        expr: sum(rate(app_error_count[5m])) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate ({{ $value }} errors/sec)"
          description: "Application is experiencing a high error rate (> 10 errors/sec)."
      
      # Slow response time alert
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, sum(rate(app_request_latency_seconds_bucket[5m])) by (le)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time (95th percentile > 1s)"
          description: "Application response time is slow. 95th percentile is above 1 second."
```

Implementation of the alert manager:

```python
# app/monitoring/alerting.py
import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class AlertManager:
    """Manages alert notifications to various channels."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the alert manager.
        
        Args:
            config_path: Path to the alerting configuration file
        """
        if config_path is None:
            config_path = os.environ.get(
                'ALERT_CONFIG_PATH',
                str(Path(__file__).parent.parent.parent / 'config' / 'alerting.json')
            )
        
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load the alerting configuration.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            The loaded configuration
        """
        try:
            with open(config_path) as f:
                config = json.load(f)
            logger.info(f"Loaded alert configuration from {config_path}")
            return config
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading alert configuration: {str(e)}")
            return {"channels": {}}
    
    def send_alert(self, 
                  alert_name: str, 
                  severity: str, 
                  summary: str, 
                  description: str,
                  details: Optional[Dict[str, Any]] = None) -> None:
        """Send an alert to all configured channels.
        
        Args:
            alert_name: Name of the alert
            severity: Severity level (critical, warning, info)
            summary: Short summary of the alert
            description: Detailed description
            details: Additional details as key-value pairs
        """
        if not self.config.get("channels"):
            logger.warning("No alert channels configured, alert not sent")
            return
        
        for channel_type, channel_config in self.config["channels"].items():
            if not channel_config.get("enabled", False):
                continue
            
            try:
                if channel_type == "slack":
                    self._send_slack_alert(
                        channel_config, alert_name, severity, summary, description, details
                    )
                elif channel_type == "email":
                    self._send_email_alert(
                        channel_config, alert_name, severity, summary, description, details
                    )
                elif channel_type == "pagerduty":
                    self._send_pagerduty_alert(
                        channel_config, alert_name, severity, summary, description, details
                    )
                else:
                    logger.warning(f"Unsupported alert channel: {channel_type}")
            except Exception as e:
                logger.error(f"Error sending alert to {channel_type}: {str(e)}")
    
    def _send_slack_alert(self, 
                         config: Dict[str, Any],
                         alert_name: str,
                         severity: str,
                         summary: str,
                         description: str,
                         details: Optional[Dict[str, Any]]) -> None:
        """Send an alert to Slack.
        
        Args:
            config: Slack channel configuration
            alert_name: Name of the alert
            severity: Severity level
            summary: Short summary
            description: Detailed description
            details: Additional details
        """
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.error("Slack webhook URL not configured")
            return
        
        # Color based on severity
        color = {
            "critical": "#FF0000",  # Red
            "warning": "#FFA500",   # Orange
            "info": "#0000FF"       # Blue
        }.get(severity.lower(), "#808080")  # Gray default
        
        # Format details
        detail_text = ""
        if details:
            detail_text = "\n".join(f"• *{k}*: {v}" for k, v in details.items())
        
        # Prepare payload
        payload = {
            "attachments": [{
                "fallback": summary,
                "color": color,
                "title": f"[{severity.upper()}] {alert_name}",
                "text": f"{summary}\n\n{description}",
                "fields": [
                    {"title": "Details", "value": detail_text, "short": False}
                ] if detail_text else []
            }]
        }
        
        # Send to Slack
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.error(f"Error sending Slack alert: {response.text}")
    
    def _send_email_alert(self,
                        config: Dict[str, Any],
                        alert_name: str,
                        severity: str,
                        summary: str,
                        description: str,
                        details: Optional[Dict[str, Any]]) -> None:
        """Send an alert via email.
        
        Args:
            config: Email channel configuration
            alert_name: Name of the alert
            severity: Severity level
            summary: Short summary
            description: Detailed description
            details: Additional details
        """
        # This would use an email library like smtplib
        # For brevity, we'll just log the action
        recipients = config.get("recipients", [])
        logger.info(f"Would send email alert to {recipients}: {summary}")
    
    def _send_pagerduty_alert(self,
                             config: Dict[str, Any],
                             alert_name: str,
                             severity: str,
                             summary: str,
                             description: str,
                             details: Optional[Dict[str, Any]]) -> None:
        """Send an alert to PagerDuty.
        
        Args:
            config: PagerDuty channel configuration
            alert_name: Name of the alert
            severity: Severity level
            summary: Short summary
            description: Detailed description
            details: Additional details
        """
        # This would use the PagerDuty API
        # For brevity, we'll just log the action
        service_key = config.get("service_key")
        logger.info(f"Would send PagerDuty alert with key {service_key}: {summary}")

# Create singleton instance
alert_manager = AlertManager()
```

Example alerting configuration:

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/services/TXXXXXXXX/BXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX",
      "channel": "#alerts",
      "username": "AlertBot"
    },
    "email": {
      "enabled": true,
      "smtp_server": "smtp.example.com",
      "smtp_port": 587,
      "username": "alerts@example.com",
      "password": "{{ SMTP_PASSWORD }}",
      "recipients": ["team@example.com"]
    },
    "pagerduty": {
      "enabled": false,
      "service_key": "{{ PAGERDUTY_SERVICE_KEY }}"
    }
  },
  "severity_routing": {
    "critical": ["slack", "email", "pagerduty"],
    "warning": ["slack", "email"],
    "info": ["slack"]
  }
}
```

#### 1.4 Monitoring Dashboards

We'll set up Grafana dashboards to visualize our monitoring data. Here's the configuration for our main application dashboard:

```yaml
# config/grafana/dashboards/application_overview.json
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      },
      {
        "datasource": "Prometheus",
        "enable": true,
        "expr": "changes(app_version[1h]) > 0",
        "iconColor": "rgba(255, 96, 96, 1)",
        "name": "Deployments",
        "titleFormat": "New deployment"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "panels": [
    {
      "collapsed": false,
      "datasource": null,
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "id": 12,
      "panels": [],
      "title": "System Overview",
      "type": "row"
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 1
      },
      "hiddenSeries": false,
      "id": 2,
      "legend": {
        "avg": false,
        "current": true,
        "max": true,
        "min": false,
        "show": true,
        "total": false,
        "values": true
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "dataLinks": []
      },
      "percentage": false,
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "system_cpu_usage_percent",
          "interval": "",
          "legendFormat": "CPU Usage",
          "refId": "A"
        }
      ],
      "thresholds": [
        {
          "colorMode": "critical",
          "fill": true,
          "line": true,
          "op": "gt",
          "value": 80,
          "yaxis": "left"
        }
      ],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "CPU Usage",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "percent",
          "label": null,
          "logBase": 1,
          "max": "100",
          "min": "0",
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 1
      },
      "hiddenSeries": false,
      "id": 4,
      "legend": {
        "avg": false,
        "current": true,
        "max": true,
        "min": false,
        "show": true,
        "total": false,
        "values": true
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "dataLinks": []
      },
      "percentage": false,
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "system_memory_usage_bytes / 1024 / 1024",
          "interval": "",
          "legendFormat": "Memory Usage",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Memory Usage",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "mbytes",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": "0",
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    }
    // Additional panels omitted for brevity
  ],
  "refresh": "10s",
  "schemaVersion": 22,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "Total Battle Analyzer - Application Overview",
  "uid": "app_overview",
  "version": 1
}
```

#### 1.5 Alert Severity Levels and Response Procedures

We'll define clear severity levels and response procedures for different types of alerts:

```markdown
# Alert Severity Levels and Response Procedures

## Severity Levels

### Critical (P1)
- **Definition**: Severe incident with significant impact on users. Service is down or unusable.
- **Response Time**: Immediate (within 15 minutes)
- **Notification Channels**: Slack, Email, PagerDuty (24/7 on-call)
- **Examples**: 
  - Application is completely down
  - Database is unreachable
  - Data corruption detected
  - Security breach detected

### Warning (P2)
- **Definition**: Partial system degradation affecting some users or functionality.
- **Response Time**: Within 1 hour during business hours
- **Notification Channels**: Slack, Email
- **Examples**:
  - High error rates (above threshold but not causing complete failure)
  - Performance degradation (slow response times)
  - Resource utilization approaching limits (CPU, memory, disk)
  - Non-critical component failures

### Info (P3)
- **Definition**: Minor issues or anomalies that don't significantly impact users.
- **Response Time**: Next business day
- **Notification Channels**: Slack
- **Examples**:
  - Minor performance variations
  - Non-critical warning signs that need attention
  - Successful but noteworthy system events
  - Minor configuration issues

## Response Procedures

### Critical (P1) Response Procedure
1. **Immediate Acknowledgment**: Responder acknowledges the alert within 15 minutes
2. **Assessment**: Quickly assess the scope and impact
3. **Communication**: Post initial status update in #incidents channel
4. **Mitigation**: 
   - Apply immediate mitigation actions (e.g., restart service, rollback deployment)
   - If cannot be quickly resolved, assemble incident response team
5. **Resolution**:
   - Address root cause
   - Verify service restoration
   - Update status page
6. **Post-Incident**:
   - Document incident in incident management system
   - Schedule post-mortem meeting within 24 hours
   - Create follow-up tasks to prevent recurrence

### Warning (P2) Response Procedure
1. **Acknowledgment**: Responder acknowledges the alert within 1 hour
2. **Assessment**: Investigate the cause and potential impact
3. **Communication**: Post status in #alerts channel if impact may spread
4. **Mitigation**: Address the issue during business hours
5. **Resolution**: 
   - Implement solution
   - Monitor for improvement
6. **Documentation**: 
   - Document the issue and resolution
   - Create follow-up tasks if needed

### Info (P3) Response Procedure
1. **Acknowledgment**: Review during next business day
2. **Assessment**: Determine if further investigation is needed
3. **Resolution**: 
   - Address during normal work cycles
   - Track in regular backlog
4. **Documentation**:
   - Document if pattern emerges
```

Automation script for alert response procedures:

```python
# scripts/alert_response.py
#!/usr/bin/env python3
"""
Alert response helper script.

This script provides guidance and automation for responding to alerts
based on their severity level.
"""

import argparse
import datetime
import subprocess
import sys
import webbrowser
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Alert response helper')
    parser.add_argument('alert_id', help='Alert ID to respond to')
    parser.add_argument('--severity', choices=['critical', 'warning', 'info'], 
                        default='warning', help='Alert severity')
    parser.add_argument('--acknowledge', action='store_true', 
                        help='Acknowledge the alert')
    parser.add_argument('--resolve', action='store_true',
                        help='Resolve the alert')
    parser.add_argument('--create-incident', action='store_true',
                        help='Create an incident ticket')
    return parser.parse_args()

def load_alert_details(alert_id):
    """Load alert details from the alert database."""
    # In a real implementation, this would query an alert database
    # For demo purposes, we'll return mock data
    return {
        'id': alert_id,
        'name': 'High CPU Usage',
        'description': 'CPU usage has been above 80% for more than 5 minutes',
        'timestamp': datetime.datetime.now().isoformat(),
        'metric': 'system_cpu_usage_percent',
        'value': '85.2',
        'threshold': '80'
    }

def acknowledge_alert(alert_id):
    """Acknowledge an alert."""
    logger.info(f"Acknowledging alert {alert_id}")
    # In a real implementation, this would call the alerting system API
    return True

def resolve_alert(alert_id):
    """Resolve an alert."""
    logger.info(f"Resolving alert {alert_id}")
    # In a real implementation, this would call the alerting system API
    return True

def create_incident_ticket(alert_details):
    """Create an incident ticket for the alert."""
    logger.info(f"Creating incident ticket for alert {alert_details['id']}")
    # In a real implementation, this would call the incident management system API
    
    # For demo purposes, generate a ticket template
    incident_template = f"""
    # Incident: {alert_details['name']}
    
    ## Overview
    Alert ID: {alert_details['id']}
    Triggered: {alert_details['timestamp']}
    Metric: {alert_details['metric']}
    Value: {alert_details['value']} (Threshold: {alert_details['threshold']})
    
    ## Description
    {alert_details['description']}
    
    ## Impact Assessment
    [TO BE FILLED]
    
    ## Actions Taken
    [TO BE FILLED]
    
    ## Resolution
    [TO BE FILLED]
    
    ## Next Steps
    [TO BE FILLED]
    """
    
    # Write to a file for reference
    incident_file = Path(f"incident_{alert_details['id']}.md")
    with open(incident_file, 'w') as f:
        f.write(incident_template)
    
    logger.info(f"Incident template created at {incident_file}")
    return str(incident_file)

def show_response_procedure(severity):
    """Show the response procedure for the given severity level."""
    procedures = {
        'critical': """
        Critical (P1) Response Procedure:
        1. Immediate Acknowledgment (within 15 minutes)
        2. Quick Assessment of scope and impact
        3. Post initial status update in #incidents channel
        4. Apply immediate mitigation actions
        5. If cannot be quickly resolved, assemble incident response team
        6. Address root cause and verify service restoration
        7. Schedule post-mortem meeting within 24 hours
        """,
        'warning': """
        Warning (P2) Response Procedure:
        1. Acknowledgment within 1 hour
        2. Investigate the cause and potential impact
        3. Post status in #alerts channel if impact may spread
        4. Address the issue during business hours
        5. Implement solution and monitor for improvement
        6. Document the issue and resolution
        """,
        'info': """
        Info (P3) Response Procedure:
        1. Review during next business day
        2. Determine if further investigation is needed
        3. Address during normal work cycles
        4. Document if pattern emerges
        """
    }
    
    print(f"\nRecommended response procedure (Severity: {severity.upper()}):")
    print(procedures.get(severity, "No procedure defined for this severity level"))

def open_monitoring_dashboard():
    """Open the monitoring dashboard in a browser."""
    # In a real implementation, this would open the specific dashboard for the alert
    dashboard_url = "http://localhost:3000/d/app_overview"
    logger.info(f"Opening dashboard: {dashboard_url}")
    try:
        webbrowser.open(dashboard_url)
    except Exception as e:
        logger.error(f"Error opening dashboard: {str(e)}")

def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Load alert details
        alert_details = load_alert_details(args.alert_id)
        
        # Display alert information
        print(f"\nAlert: {alert_details['name']} ({args.alert_id})")
        print(f"Description: {alert_details['description']}")
        print(f"Timestamp: {alert_details['timestamp']}")
        print(f"Value: {alert_details['value']} (Threshold: {alert_details['threshold']})")
        
        # Show response procedure
        show_response_procedure(args.severity)
        
        # Process actions
        if args.acknowledge:
            acknowledge_alert(args.alert_id)
        
        if args.create_incident:
            incident_file = create_incident_ticket(alert_details)
            print(f"\nIncident ticket created: {incident_file}")
        
        if args.resolve:
            resolve_alert(args.alert_id)
        
        # Open monitoring dashboard
        open_monitoring_dashboard()
        
        return 0
    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

This comprehensive monitoring system will provide real-time visibility into the health and performance of the Total Battle Analyzer application, enabling proactive detection of issues before they impact users. The combination of system metrics, application performance data, and automated alerting creates a robust foundation for maintaining reliable service.

### 2. Automated Maintenance Procedures

- [ ] Implement database maintenance automation
- [ ] Set up log rotation and archiving
- [ ] Create scheduled backup procedures
- [ ] Configure dependency update scanning
- [ ] Implement system cleanup routines

### 3. Incident Response Framework

- [ ] Establish incident classification system
- [ ] Create incident response procedures
- [ ] Implement post-mortem analysis template
- [ ] Set up incident tracking and resolution
- [ ] Configure status page automation

### 4. Continuous Health Assessment

- [ ] Implement regular security scanning
- [ ] Configure performance regression testing
- [ ] Set up user experience monitoring
- [ ] Create monthly health reports
- [ ] Implement technical debt tracking

### 5. Documentation and Knowledge Management

- [ ] Establish maintenance documentation standards
- [ ] Create operational runbooks
- [ ] Implement knowledge base for common issues
- [ ] Set up change management documentation
- [ ] Create maintenance training materials 

## Implementation Approach

The implementation of Phase 6 Part 5 will follow a structured timeline to ensure all components are properly integrated into the Total Battle Analyzer project. The estimated duration for this phase is approximately 3 weeks, divided across the following activities:

### Week 1: Core Monitoring System (Days 1-5)

1. **Day 1-2: System Health Monitoring**
   - Set up Prometheus and Grafana infrastructure
   - Implement system metrics collection (CPU, memory, disk)
   - Create basic health dashboards

2. **Day 3-4: Performance Metrics**
   - Implement application-specific metrics
   - Set up performance monitoring for critical paths
   - Create performance dashboards

3. **Day 5: Alerting System**
   - Configure alert thresholds and rules
   - Set up notification channels (Slack, email)
   - Test alert notifications

### Week 2: Maintenance and Response Procedures (Days 6-10)

4. **Day 6-7: Automated Maintenance**
   - Implement database maintenance routines
   - Configure log rotation and backup procedures
   - Set up dependency scanning

5. **Day 8-9: Incident Response Framework**
   - Establish incident classification system
   - Create response procedures for different severity levels
   - Implement incident tracking

6. **Day 10: Continuous Health Assessment**
   - Configure security scanning
   - Set up performance regression testing
   - Implement technical debt tracking

### Week 3: Documentation and Refinement (Days 11-15)

7. **Day 11-12: Knowledge Management**
   - Create operational runbooks
   - Develop knowledge base structure
   - Document maintenance procedures

8. **Day 13-14: Integration and Testing**
   - Integrate all monitoring components
   - Test the complete monitoring system
   - Fine-tune alerts and thresholds

9. **Day 15: Review and Handover**
   - Conduct a comprehensive review
   - Prepare handover documentation
   - Train team members on the monitoring system

### Dependencies

This phase has dependencies on:
- Completed Phase 6 Part 4: Continuous Deployment Setup
- Operational production-like environments for testing
- Access to monitoring infrastructure (Prometheus, Grafana)
- Proper permissions for alert notifications

### Risk Mitigation

1. **Alert Fatigue**: Start with conservative thresholds and adjust based on actual application behavior to prevent too many alerts.
2. **Resource Consumption**: Monitor the impact of the monitoring tools themselves to ensure they don't significantly impact application performance.
3. **Security**: Ensure monitoring data doesn't expose sensitive information and access to dashboards is properly secured.
4. **Knowledge Transfer**: Schedule training sessions to ensure all team members understand how to use and maintain the monitoring systems.

This phased approach ensures that monitoring and maintenance capabilities are built incrementally, with opportunities for testing and refinement at each stage.

## Conclusion

The monitoring and maintenance implementation outlined in this document establishes a comprehensive framework for ensuring the long-term reliability, performance, and security of the Total Battle Analyzer application. By implementing these systems and procedures, we achieve several key benefits:

### Proactive Issue Detection

The robust monitoring system enables us to detect potential issues before they impact users. Through real-time performance metrics, system health checks, and automated alerting, we can identify and address anomalies early, maintaining a high-quality user experience.

### Reduced Operational Overhead

Automation plays a central role in our maintenance strategy, from database maintenance routines to dependency updates and backup procedures. This significantly reduces manual effort and human error, allowing the development team to focus on delivering new features rather than managing routine maintenance tasks.

### Rapid Incident Resolution

With clear incident response procedures, alerts categorized by severity, and comprehensive diagnostic tools, the team can respond quickly and effectively to any issues that arise. The established frameworks ensure consistent handling of incidents regardless of who is responding.

### Continuous Improvement

The health assessment processes and technical debt tracking provide mechanisms for ongoing evaluation and improvement of the application. By regularly reviewing system performance, security posture, and user feedback, we can identify opportunities for enhancement and prioritize improvements effectively.

### Knowledge Preservation

Through comprehensive documentation, operational runbooks, and a centralized knowledge base, we ensure that critical information is preserved and accessible. This reduces dependency on specific team members and facilitates knowledge transfer to new team members.

### Implementation Approach

The implementation of the monitoring and maintenance systems will be approached methodically:

1. Start with core monitoring infrastructure (system health and performance metrics)
2. Implement alerting systems with proper thresholds and notification channels
3. Set up automated maintenance procedures for critical components
4. Establish incident response frameworks and documentation
5. Develop ongoing health assessment processes
6. Create comprehensive documentation and knowledge management systems

By following this approach, we will establish a solid foundation for maintaining the Total Battle Analyzer application throughout its lifecycle, ensuring it remains performant, secure, and reliable for users. 