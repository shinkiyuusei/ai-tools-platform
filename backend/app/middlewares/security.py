"""
Security middleware for commercial-grade protection
Implements security headers, CORS policies, and input validation
"""
from flask import request, g, after_this_request
import re


def add_security_headers(response):
    """Add security headers to all responses"""
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    response.headers['Content-Security-Policy'] = csp
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # HSTS (only in production)
    if not g.get('is_dev'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response


def validate_input_data(data: dict, required_fields: list = None, max_length: dict = None):
    """
    Validate input data for security
    - Check required fields
    - Validate field lengths
    - Sanitize against injection attacks
    """
    errors = []
    
    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field} is required")
    
    # Check field lengths
    if max_length:
        for field, max_len in max_length.items():
            if field in data and data[field] and len(str(data[field])) > max_len:
                errors.append(f"{field} exceeds maximum length of {max_len}")
    
    # Check for SQL injection patterns
    sql_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER)\b)',
        r'(--|;|\/\*|\*\/)',
        r'(\bOR\b|\bAND\b).*=.*=',
    ]
    
    for field, value in data.items():
        if isinstance(value, str):
            for pattern in sql_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    errors.append(f"{field} contains invalid characters")
                    break
    
    if errors:
        from ...core.errors import AppError, ErrorCode
        raise AppError(ErrorCode.PARAM_INVALID, "; ".join(errors))
    
    return True


def sanitize_string(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks
    """
    if not input_str:
        return ""
    
    # Remove null bytes
    input_str = input_str.replace('\x00', '')
    
    # Limit length
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    # Remove potentially dangerous HTML tags
    dangerous_tags = ['<script', '</script', '<iframe', '</iframe', '<object', '</object']
    for tag in dangerous_tags:
        input_str = input_str.replace(tag, '')
    
    return input_str.strip()


def log_security_event(event_type: str, details: dict):
    """
    Log security events for monitoring and audit trails
    """
    from datetime import datetime
    from ...extensions import get_redis_client
    
    client = get_redis_client()
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'user_id': g.get('user_id'),
        'details': details
    }
    
    # Store in Redis for recent events (last 24 hours)
    client.lpush('security_events', str(log_entry))
    client.ltrim('security_events', 0, 9999)
    client.expire('security_events', 86400)
    
    # Also store in MongoDB for long-term storage
    from ...extensions import get_mongo_db
    mongo = get_mongo_db()
    mongo['t_security_logs'].insert_one(log_entry)
