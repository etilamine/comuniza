"""
Rate limiting configuration and utilities for Comuniza.
Implements strict rate limiting with CloudFlare-aware IP detection.
"""

import time
import redis
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django_ratelimit.core import is_ratelimited
import logging

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Configuration for strict rate limiting across different endpoint types."""
    
    # Authentication endpoints - VERY STRICT
    AUTH_LOGIN = '5/m'  # 5 attempts per minute
    AUTH_REGISTER = '3/h'  # 3 registrations per hour  
    AUTH_PASSWORD_RESET = '3/h'  # 3 password resets per hour
    AUTH_PASSWORD_CHANGE = '10/h'  # 10 password changes per hour
    
    # API endpoints - STRICT
    API_READ = '60/s'  # 60 requests per second
    API_WRITE = '10/s'  # 10 write requests per second
    API_SEARCH = '30/s'  # 30 search requests per second
    API_UPLOAD = '5/m'  # 5 file uploads per minute
    
    # Messaging endpoints - STRICT
    MESSAGE_SEND = '20/m'  # 20 messages per minute
    CONVERSATION_CREATE = '10/h'  # 10 new conversations per hour
    
    # Content endpoints - MODERATE
    ITEM_CREATE = '10/h'  # 10 items created per hour
    ITEM_UPDATE = '100/h'  # 100 item updates per hour
    LOAN_REQUEST = '20/h'  # 20 loan requests per hour
    
    # General endpoints - LENIENT
    GENERAL = '1000/h'  # 1000 requests per hour
    PROFILE_VIEW = '200/m'  # 200 profile views per minute


def get_client_ip(request):
    """
    Get real client IP from request headers.
    CloudFlare-aware implementation with error handling.
    """
    if not request or not hasattr(request, 'META'):
        logger.warning("Invalid request object in get_client_ip")
        return '127.0.0.1'  # Fallback IP
    
    try:
        # Check CloudFlare headers first
        cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_connecting_ip:
            return cf_connecting_ip
        
        # Check standard X-Forwarded-For header
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            ip = x_forwarded_for.split(',')[0].strip()
            return ip
        
        # Fall back to remote address
        remote_addr = request.META.get('REMOTE_ADDR')
        return remote_addr or '127.0.0.1'
    except Exception as e:
        logger.error(f"Error extracting client IP: {e}")
        return '127.0.0.1'  # Fallback IP on error


def get_rate_limit_key(group, request):
    """
    Generate rate limit key with IP and user context.
    """
    try:
        client_ip = get_client_ip(request)
        
        # Include user ID if authenticated
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            user_id = getattr(request.user, 'id', 'unknown')
            return f"rl:{group}:{client_ip}:user{user_id}"
        
        return f"rl:{group}:{client_ip}:anon"
    except Exception as e:
        logger.error(f"Error generating rate limit key: {e}")
        return f"rl:{group}:127.0.0.1:error"  # Fallback key


class SlidingWindowRateLimiter:
    """
    Advanced rate limiting with sliding window algorithm.
    Uses Redis for distributed rate limiting.
    """
    
    def __init__(self):
        self.redis_client = None
        try:
            import redis
            # Use database 2 for rate limiting (consistent with ratelimit cache)
            self.redis_client = redis.Redis(host='redis', port=6379, db=2, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
    
    def is_allowed(self, key, limit, window_seconds):
        """
        Check if request is allowed using sliding window algorithm.
        
        Args:
            key: Rate limit key
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            tuple: (allowed, remaining, reset_time)
        """
        if not self.redis_client:
            # Fallback to Django cache
            return self._cache_is_allowed(key, limit, window_seconds)
        
        try:
            now = time.time()
            window_start = now - window_seconds
            
            # Remove old entries outside the window
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_count = self.redis_client.zcard(key)
            
            if current_count >= limit:
                # Get oldest request time for reset time
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                reset_time = int(oldest[0][1] + window_seconds) if oldest else int(now + window_seconds)
                return False, 0, reset_time
            
            # Add current request
            self.redis_client.zadd(key, {str(now): now})
            self.redis_client.expire(key, window_seconds)
            
            remaining = limit - current_count - 1
            reset_time = int(now + window_seconds)
            
            return True, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Sliding window rate limiting error: {e}")
            # Fail open - allow request if Redis fails
            return True, limit - 1, int(time.time() + window_seconds)
    
    def _cache_is_allowed(self, key, limit, window_seconds):
        """Fallback implementation using Django cache."""
        cache_key = f"rate_limit:{key}"
        
        # Get current count and timestamp
        data = cache.get(cache_key, {'count': 0, 'reset_time': time.time()})
        
        now = time.time()
        
        # Check if window has expired
        if now >= data['reset_time']:
            data = {'count': 0, 'reset_time': now + window_seconds}
        
        if data['count'] >= limit:
            return False, 0, int(data['reset_time'])
        
        # Increment count
        data['count'] += 1
        cache.set(cache_key, data, window_seconds)
        
        remaining = limit - data['count']
        return True, remaining, int(data['reset_time'])


# Global sliding window rate limiter instance
sliding_limiter = SlidingWindowRateLimiter()


def custom_ratelimit(group, key=None, rate=None, method='GET', block=False):
    """
    Custom rate limiting decorator with sliding window support.
    Works with both function-based and class-based views.
    """
    def decorator(view_func):
        def _wrapped_view(*args, **kwargs):
            # Extract request object for both function and class-based views
            request = None
            if len(args) >= 2 and hasattr(args[0], 'request'):
                # Class-based view method: (self, request, ...)
                request = args[1]
            elif len(args) >= 1 and hasattr(args[0], 'META'):
                # Function-based view: (request, ...)
                request = args[0]
            else:
                # Fallback - try to find request in args
                for arg in args:
                    if hasattr(arg, 'META'):
                        request = arg
                        break
            
            if not request:
                # No valid request found, skip rate limiting and allow request
                logger.warning("Rate limiting skipped: no valid request object found")
                return view_func(*args, **kwargs)
            
            # Generate rate limit key
            rate_limit_key = key or get_rate_limit_key(group, request)
            
            # Parse rate (e.g., "5/m" -> 5 requests per 60 seconds)
            if rate:
                limit_str, period = rate.split('/')
                limit = int(limit_str)
                
                if period == 's':
                    window = 1
                elif period == 'm':
                    window = 60
                elif period == 'h':
                    window = 3600
                elif period == 'd':
                    window = 86400
                else:
                    window = 60  # Default to minute
            else:
                # Use default rate from config
                rate_config = getattr(RateLimitConfig, group.upper(), '100/m')
                limit_str, period = rate_config.split('/')
                limit = int(limit_str)
                window = 60 if period == 'm' else 3600 if period == 'h' else 1
            
            # Check rate limit using sliding window
            allowed, remaining, reset_time = sliding_limiter.is_allowed(
                rate_limit_key, limit, window
            )
            
            if not allowed:
                # Log rate limit violation
                logger.warning(
                    f"Rate limit exceeded: {group} for {get_client_ip(request)}",
                    extra={
                        'group': group,
                        'ip': get_client_ip(request),
                        'limit': limit,
                        'window': window
                    }
                )
                
                # Add audit log for security event
                from apps.core.audit import AuditManager
                AuditManager.log_security_event(
                    request,
                    'rate_limit_exceeded',
                    details={
                        'group': group,
                        'limit': limit,
                        'window': window,
                        'reset_time': reset_time
                    },
                    severity='medium'
                )
                
                if block:
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests. Try again in {reset_time - int(time.time())} seconds.',
                        'retry_after': reset_time - int(time.time())
                    }, status=429)
            
            # Add rate limit headers
            response = view_func(*args, **kwargs)
            if hasattr(response, '__setitem__'):  # Check if response is dict-like
                try:
                    response['X-RateLimit-Limit'] = str(limit)
                    response['X-RateLimit-Remaining'] = str(remaining)
                    response['X-RateLimit-Reset'] = str(reset_time)
                except Exception as e:
                    logger.warning(f"Failed to set rate limit headers: {e}")
            
            return response
        
        return _wrapped_view
    return decorator


# Pre-configured decorators for common use cases
def strict_auth_rate_limit(view_func):
    """Very strict rate limiting for authentication endpoints."""
    return custom_ratelimit('auth_login', rate=RateLimitConfig.AUTH_LOGIN, block=True)(view_func)


def strict_api_rate_limit(view_func):
    """Strict rate limiting for API endpoints."""
    return custom_ratelimit('api_write', rate=RateLimitConfig.API_WRITE, block=True)(view_func)


def message_rate_limit(view_func):
    """Rate limiting for messaging endpoints."""
    return custom_ratelimit('message_send', rate=RateLimitConfig.MESSAGE_SEND, block=True)(view_func)


def content_creation_rate_limit(view_func):
    """Rate limiting for content creation endpoints."""
    return custom_ratelimit('item_create', rate=RateLimitConfig.ITEM_CREATE, block=True)(view_func)