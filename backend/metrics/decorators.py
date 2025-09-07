# Decorators for Easy Metrics Tracking

from functools import wraps
from flask import request
import time
from .prometheus_metrics import (
    database_queries_total,
    database_query_duration_seconds,
    errors_total,
    exceptions_total,
    user_registrations_total,
    user_logins_total,
    orders_created_total,
    revenue_total
)

def track_database_query(operation, table):
    """Decorator to track database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                database_queries_total.labels(
                    operation=operation,
                    table=table,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                database_queries_total.labels(
                    operation=operation,
                    table=table,
                    status='error'
                ).inc()
                errors_total.labels(
                    error_type='database_error',
                    endpoint=request.endpoint or 'unknown',
                    severity='high'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                database_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        return wrapper
    return decorator

def track_business_metric(metric_name, **metric_labels):
    """Decorator to track business metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Track different business metrics based on metric_name
                if metric_name == 'user_registration' and result:
                    user_registrations_total.inc()
                elif metric_name == 'user_login' and result:
                    user_logins_total.inc()
                elif metric_name == 'order_created' and result:
                    # Extract labels from function result or arguments
                    payment_method = metric_labels.get('payment_method', 'unknown')
                    category = metric_labels.get('product_category', 'general')
                    orders_created_total.labels(
                        payment_method=payment_method,
                        product_category=category
                    ).inc()
                    
                    # Track revenue if amount provided
                    amount = metric_labels.get('amount', 0)
                    if amount > 0:
                        revenue_total.labels(
                            currency=metric_labels.get('currency', 'USD'),
                            product_category=category
                        ).inc(amount)
                
                return result
            except Exception as e:
                exceptions_total.labels(
                    exception_type=type(e).__name__,
                    endpoint=request.endpoint or 'unknown'
                ).inc()
                raise
        return wrapper
    return decorator

def track_errors(error_type='general', severity='medium'):
    """Decorator to track errors in specific functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                errors_total.labels(
                    error_type=error_type,
                    endpoint=request.endpoint or 'unknown',
                    severity=severity
                ).inc()
                exceptions_total.labels(
                    exception_type=type(e).__name__,
                    endpoint=request.endpoint or 'unknown'
                ).inc()
                raise
        return wrapper
    return decorator

# Convenience decorators for common use cases
def track_user_registration(func):
    """Shortcut decorator for user registration tracking"""
    return track_business_metric('user_registration')(func)

def track_user_login(func):
    """Shortcut decorator for user login tracking"""
    return track_business_metric('user_login')(func)

def track_database_read(table):
    """Shortcut decorator for database read operations"""
    return track_database_query('select', table)

def track_database_write(table):
    """Shortcut decorator for database write operations"""
    return track_database_query('insert', table)

def track_database_update(table):
    """Shortcut decorator for database update operations"""
    return track_database_query('update', table)