# Flask Middleware for Automatic Metrics Collection

from flask import request, g
import time
import threading
import psutil
import os
from .prometheus_metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes,
    memory_usage_bytes,
    cpu_usage_percent,
    open_file_descriptors,
    database_connections_active
)

# Global counter for active connections
active_connections = 0
active_connections_lock = threading.Lock()

def setup_metrics_middleware(app):
    """Setup all metrics middleware for the Flask app"""
    
    @app.before_request
    def before_request():
        """Start timing request and increment active connections"""
        global active_connections
        
        g.start_time = time.time()
        
        with active_connections_lock:
            active_connections += 1
    
    @app.after_request
    def after_request(response):
        """Record metrics after each request"""
        global active_connections
        
        if hasattr(g, 'start_time'):
            # Request duration
            duration = time.time() - g.start_time
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(duration)
            
            # Request count
            http_requests_total.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status_code=response.status_code,
                client_ip=request.remote_addr or 'unknown'
            ).inc()
            
            # Request size
            request_size = len(request.get_data())
            if request_size > 0:
                http_request_size_bytes.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(request_size)
            
            # Response size
            response_data = response.get_data()
            if response_data:
                response_size = len(response_data)
                http_response_size_bytes.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status_code=response.status_code
                ).observe(response_size)
        
        with active_connections_lock:
            active_connections -= 1
        
        return response
    
    # Start system metrics collection thread
    start_system_metrics_collection()

def start_system_metrics_collection():
    """Start background thread to collect system metrics"""
    def collect_system_metrics():
        while True:
            try:
                # Memory usage
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                memory_usage_bytes.set(memory_info.rss)
                
                # CPU usage
                cpu_percent = process.cpu_percent()
                cpu_usage_percent.set(cpu_percent)
                
                # Open file descriptors
                try:
                    num_fds = process.num_fds()
                    open_file_descriptors.set(num_fds)
                except AttributeError:
                    # Windows doesn't support num_fds()
                    pass
                
                # Database connections (you can implement this based on your DB setup)
                database_connections_active.set(get_active_db_connections())
                
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
            
            time.sleep(10)  # Collect every 10 seconds
    
    metrics_thread = threading.Thread(target=collect_system_metrics, daemon=True)
    metrics_thread.start()

def get_active_db_connections():
    """Get number of active database connections - implement based on your DB"""
    # Mock implementation - replace with real database pool query
    # Example for SQLAlchemy:
    # from your_app.database import db
    # return db.engine.pool.checkedout()
    return 5  # Replace with actual implementation