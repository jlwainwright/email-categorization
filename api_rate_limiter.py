#!/usr/bin/env python3
"""
API Rate Limiter
----------------
Handles rate limiting, request throttling, and caching for external API calls.
Supports HuggingFace and OpenAI APIs with configurable limits.
"""

import time
import json
import hashlib
import asyncio
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Optional, Any, Callable
import requests

@dataclass
class RateLimit:
    """Rate limit configuration for an API."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_size: int = 5  # Number of requests that can be made in rapid succession

@dataclass
class APIResponse:
    """Wrapper for API responses with caching metadata."""
    data: Any
    cached: bool
    timestamp: datetime
    cache_key: str

class APIRateLimiter:
    """Thread-safe rate limiter with caching and usage monitoring."""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.request_history = defaultdict(lambda: {
            'minute': deque(),
            'hour': deque(),
            'day': deque()
        })
        
        # API Rate Limits (conservative defaults)
        self.rate_limits = {
            'huggingface': RateLimit(
                requests_per_minute=30,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_size=5
            ),
            'openai': RateLimit(
                requests_per_minute=20,
                requests_per_hour=500,
                requests_per_day=5000,
                burst_size=3
            )
        }
        
        # Response cache (in-memory)
        self.cache = {}
        self.cache_ttl = {
            'sentiment': 3600,  # 1 hour for sentiment analysis
            'categorization': 1800  # 30 minutes for categorization
        }
        
        # Usage statistics
        self.usage_stats = defaultdict(lambda: {
            'total_requests': 0,
            'cached_responses': 0,
            'rate_limited': 0,
            'errors': 0,
            'last_request': None
        })
    
    def _clean_old_requests(self, api_name: str):
        """Remove old requests from history to keep memory usage reasonable."""
        now = datetime.now()
        history = self.request_history[api_name]
        
        # Clean minute history (keep last 60 seconds)
        while history['minute'] and (now - history['minute'][0]).total_seconds() > 60:
            history['minute'].popleft()
        
        # Clean hour history (keep last 3600 seconds)
        while history['hour'] and (now - history['hour'][0]).total_seconds() > 3600:
            history['hour'].popleft()
        
        # Clean day history (keep last 86400 seconds)
        while history['day'] and (now - history['day'][0]).total_seconds() > 86400:
            history['day'].popleft()
    
    def _check_rate_limit(self, api_name: str) -> Optional[float]:
        """Check if request would exceed rate limits. Returns wait time if limited."""
        if api_name not in self.rate_limits:
            return None
        
        rate_limit = self.rate_limits[api_name]
        history = self.request_history[api_name]
        now = datetime.now()
        
        # Check minute limit
        minute_count = len(history['minute'])
        if minute_count >= rate_limit.requests_per_minute:
            oldest_minute = history['minute'][0]
            wait_time = 60 - (now - oldest_minute).total_seconds()
            if wait_time > 0:
                return wait_time
        
        # Check hour limit
        hour_count = len(history['hour'])
        if hour_count >= rate_limit.requests_per_hour:
            oldest_hour = history['hour'][0]
            wait_time = 3600 - (now - oldest_hour).total_seconds()
            if wait_time > 0:
                return wait_time
        
        # Check day limit
        day_count = len(history['day'])
        if day_count >= rate_limit.requests_per_day:
            oldest_day = history['day'][0]
            wait_time = 86400 - (now - oldest_day).total_seconds()
            if wait_time > 0:
                return wait_time
        
        return None
    
    def _record_request(self, api_name: str):
        """Record a request in the rate limiting history."""
        now = datetime.now()
        history = self.request_history[api_name]
        
        history['minute'].append(now)
        history['hour'].append(now)
        history['day'].append(now)
        
        self.usage_stats[api_name]['total_requests'] += 1
        self.usage_stats[api_name]['last_request'] = now
    
    def _generate_cache_key(self, content: str, operation: str) -> str:
        """Generate a cache key for the given content and operation."""
        # Create hash of content for consistent caching
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return f"{operation}:{content_hash}"
    
    def _get_cached_response(self, cache_key: str, operation: str) -> Optional[Any]:
        """Get cached response if available and not expired."""
        if cache_key not in self.cache:
            return None
        
        cached_item = self.cache[cache_key]
        ttl = self.cache_ttl.get(operation, 3600)
        
        if (datetime.now() - cached_item['timestamp']).total_seconds() > ttl:
            # Cache expired
            del self.cache[cache_key]
            return None
        
        return cached_item['data']
    
    def _cache_response(self, cache_key: str, data: Any):
        """Cache a response."""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def _make_request_with_backoff(self, request_func: Callable, max_retries: int = 3) -> Any:
        """Make API request with exponential backoff on rate limit errors."""
        for attempt in range(max_retries):
            try:
                response = request_func()
                
                # Check for rate limit responses
                if hasattr(response, 'status_code'):
                    if response.status_code == 429:  # Too Many Requests
                        # Extract retry-after header if available
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            wait_time = int(retry_after)
                        else:
                            # Exponential backoff
                            wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                        
                        print(f"Rate limited by API. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    elif response.status_code == 200:
                        return response
                    else:
                        print(f"API error: {response.status_code} - {response.text}")
                        if attempt == max_retries - 1:
                            return response
                        time.sleep(2 ** attempt)  # Exponential backoff for other errors
                        continue
                else:
                    return response
                    
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)
        
        raise Exception(f"Request failed after {max_retries} attempts")
    
    def throttled_request(self, api_name: str, operation: str, content: str, 
                         request_func: Callable) -> APIResponse:
        """Make a throttled API request with caching."""
        with self.lock:
            # Generate cache key
            cache_key = self._generate_cache_key(content, operation)
            
            # Check cache first
            cached_data = self._get_cached_response(cache_key, operation)
            if cached_data is not None:
                self.usage_stats[api_name]['cached_responses'] += 1
                return APIResponse(
                    data=cached_data,
                    cached=True,
                    timestamp=datetime.now(),
                    cache_key=cache_key
                )
            
            # Clean old request history
            self._clean_old_requests(api_name)
            
            # Check rate limits
            wait_time = self._check_rate_limit(api_name)
            if wait_time:
                print(f"Rate limit reached for {api_name}. Waiting {wait_time:.1f} seconds...")
                self.usage_stats[api_name]['rate_limited'] += 1
                time.sleep(wait_time)
            
            # Record the request
            self._record_request(api_name)
        
        try:
            # Make the actual request (outside the lock)
            response = self._make_request_with_backoff(request_func)
            
            # Cache the response
            with self.lock:
                self._cache_response(cache_key, response)
            
            return APIResponse(
                data=response,
                cached=False,
                timestamp=datetime.now(),
                cache_key=cache_key
            )
            
        except Exception as e:
            with self.lock:
                self.usage_stats[api_name]['errors'] += 1
            raise e
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        with self.lock:
            stats = dict(self.usage_stats)
            
            # Add current cache size
            stats['cache_info'] = {
                'total_cached_items': len(self.cache),
                'cache_hit_rate': {}
            }
            
            # Calculate cache hit rates
            for api_name in stats:
                if api_name == 'cache_info':
                    continue
                total = stats[api_name]['total_requests']
                cached = stats[api_name]['cached_responses']
                if total > 0:
                    stats['cache_info']['cache_hit_rate'][api_name] = (cached / total) * 100
                else:
                    stats['cache_info']['cache_hit_rate'][api_name] = 0
            
            return stats
    
    def update_rate_limits(self, api_name: str, rate_limit: RateLimit):
        """Update rate limits for an API."""
        with self.lock:
            self.rate_limits[api_name] = rate_limit
    
    def clear_cache(self, operation: str = None):
        """Clear cache for specific operation or all cache."""
        with self.lock:
            if operation:
                # Clear cache for specific operation
                keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{operation}:")]
                for key in keys_to_remove:
                    del self.cache[key]
            else:
                # Clear all cache
                self.cache.clear()
    
    def print_usage_report(self):
        """Print a formatted usage report."""
        stats = self.get_usage_stats()
        
        print("\n" + "=" * 60)
        print("API USAGE REPORT")
        print("=" * 60)
        
        for api_name, api_stats in stats.items():
            if api_name == 'cache_info':
                continue
                
            print(f"\n{api_name.upper()}:")
            print(f"  Total Requests: {api_stats['total_requests']}")
            print(f"  Cached Responses: {api_stats['cached_responses']}")
            print(f"  Rate Limited: {api_stats['rate_limited']}")
            print(f"  Errors: {api_stats['errors']}")
            if api_stats['last_request']:
                print(f"  Last Request: {api_stats['last_request'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            hit_rate = stats['cache_info']['cache_hit_rate'].get(api_name, 0)
            print(f"  Cache Hit Rate: {hit_rate:.1f}%")
        
        print(f"\nCACHE INFO:")
        print(f"  Total Cached Items: {stats['cache_info']['total_cached_items']}")
        print("=" * 60)

# Global rate limiter instance
rate_limiter = APIRateLimiter()

def throttled_huggingface_request(content: str, request_func: Callable) -> APIResponse:
    """Make a throttled HuggingFace API request."""
    return rate_limiter.throttled_request('huggingface', 'sentiment', content, request_func)

def throttled_openai_request(content: str, request_func: Callable) -> APIResponse:
    """Make a throttled OpenAI API request."""
    return rate_limiter.throttled_request('openai', 'categorization', content, request_func)

if __name__ == "__main__":
    # Test the rate limiter
    def mock_request():
        return {"result": "test"}
    
    print("Testing API Rate Limiter...")
    
    # Test multiple requests
    for i in range(5):
        response = rate_limiter.throttled_request('test_api', 'test_op', f'content_{i}', mock_request)
        print(f"Request {i+1}: {'Cached' if response.cached else 'Fresh'}")
    
    # Test cache hit
    response = rate_limiter.throttled_request('test_api', 'test_op', 'content_1', mock_request)
    print(f"Repeat request: {'Cached' if response.cached else 'Fresh'}")
    
    # Print usage report
    rate_limiter.print_usage_report()