#!/usr/bin/env python3
"""
API Monitor
-----------
Monitoring and alerting system for API usage and performance.
"""

import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from api_rate_limiter import rate_limiter

class APIMonitor:
    """Monitor API usage and provide alerts."""
    
    def __init__(self, log_file='api_usage.log'):
        self.log_file = log_file
        self.alert_thresholds = {
            'error_rate': 10,  # Alert if error rate > 10%
            'cache_hit_rate': 50,  # Alert if cache hit rate < 50%
            'rate_limit_rate': 5,  # Alert if rate limit rate > 5%
            'daily_usage': {
                'huggingface': 8000,  # Alert if daily usage > 80% of limit
                'openai': 4000
            }
        }
    
    def log_usage(self):
        """Log current usage statistics to file."""
        stats = rate_limiter.get_usage_stats()
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats
        }
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def check_alerts(self):
        """Check for alert conditions and return list of alerts."""
        stats = rate_limiter.get_usage_stats()
        alerts = []
        
        for api_name, api_stats in stats.items():
            if api_name == 'cache_info':
                continue
            
            total_requests = api_stats.get('total_requests', 0)
            if total_requests == 0:
                continue
            
            # Error rate alert
            error_rate = (api_stats.get('errors', 0) / total_requests) * 100
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'high_error_rate',
                    'api': api_name,
                    'value': error_rate,
                    'threshold': self.alert_thresholds['error_rate'],
                    'message': f'High error rate for {api_name}: {error_rate:.1f}%'
                })
            
            # Cache hit rate alert
            cache_hit_rate = stats['cache_info']['cache_hit_rate'].get(api_name, 0)
            if cache_hit_rate < self.alert_thresholds['cache_hit_rate']:
                alerts.append({
                    'type': 'low_cache_hit_rate',
                    'api': api_name,
                    'value': cache_hit_rate,
                    'threshold': self.alert_thresholds['cache_hit_rate'],
                    'message': f'Low cache hit rate for {api_name}: {cache_hit_rate:.1f}%'
                })
            
            # Rate limit alert
            rate_limit_rate = (api_stats.get('rate_limited', 0) / total_requests) * 100
            if rate_limit_rate > self.alert_thresholds['rate_limit_rate']:
                alerts.append({
                    'type': 'high_rate_limit',
                    'api': api_name,
                    'value': rate_limit_rate,
                    'threshold': self.alert_thresholds['rate_limit_rate'],
                    'message': f'High rate limit rate for {api_name}: {rate_limit_rate:.1f}%'
                })
            
            # Daily usage alert
            if api_name in self.alert_thresholds['daily_usage']:
                threshold = self.alert_thresholds['daily_usage'][api_name]
                if total_requests > threshold:
                    alerts.append({
                        'type': 'high_daily_usage',
                        'api': api_name,
                        'value': total_requests,
                        'threshold': threshold,
                        'message': f'High daily usage for {api_name}: {total_requests} requests'
                    })
        
        return alerts
    
    def print_alerts(self):
        """Print any active alerts."""
        alerts = self.check_alerts()
        
        if not alerts:
            return
        
        print("\n" + "🚨" * 20)
        print("API USAGE ALERTS")
        print("🚨" * 20)
        
        for alert in alerts:
            print(f"⚠️  {alert['message']}")
        
        print("🚨" * 20 + "\n")
    
    def generate_daily_report(self):
        """Generate a daily usage report."""
        stats = rate_limiter.get_usage_stats()
        
        print("\n" + "📊" * 20)
        print("DAILY API USAGE REPORT")
        print("📊" * 20)
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_requests = 0
        total_cached = 0
        total_errors = 0
        
        for api_name, api_stats in stats.items():
            if api_name == 'cache_info':
                continue
            
            requests = api_stats.get('total_requests', 0)
            cached = api_stats.get('cached_responses', 0)
            errors = api_stats.get('errors', 0)
            
            total_requests += requests
            total_cached += cached
            total_errors += errors
            
            print(f"\n{api_name.upper()}:")
            print(f"  📈 Requests: {requests}")
            print(f"  💾 Cached: {cached}")
            print(f"  ❌ Errors: {errors}")
            
            if requests > 0:
                cache_rate = (cached / requests) * 100
                error_rate = (errors / requests) * 100
                print(f"  📊 Cache Hit Rate: {cache_rate:.1f}%")
                print(f"  📊 Error Rate: {error_rate:.1f}%")
        
        print(f"\nTOTALS:")
        print(f"  📈 Total Requests: {total_requests}")
        print(f"  💾 Total Cached: {total_cached}")
        print(f"  ❌ Total Errors: {total_errors}")
        
        if total_requests > 0:
            overall_cache_rate = (total_cached / total_requests) * 100
            overall_error_rate = (total_errors / total_requests) * 100
            print(f"  📊 Overall Cache Hit Rate: {overall_cache_rate:.1f}%")
            print(f"  📊 Overall Error Rate: {overall_error_rate:.1f}%")
        
        print("📊" * 20 + "\n")
        
        # Check and print alerts
        self.print_alerts()
    
    def serve_metrics(self, port=8000):
        """Serve Prometheus metrics on HTTP endpoint."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        class MetricsHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/metrics':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    
                    # Generate Prometheus metrics
                    metrics = self.generate_prometheus_metrics()
                    self.wfile.write(metrics.encode())
                elif self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "healthy"}')
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'Not Found')
            
            def generate_prometheus_metrics(self):
                """Generate Prometheus-formatted metrics."""
                stats = rate_limiter.get_usage_stats()
                metrics = []
                
                # API request metrics
                for api_name, api_stats in stats.items():
                    if api_name == 'cache_info':
                        continue
                    
                    total_requests = api_stats.get('total_requests', 0)
                    errors = api_stats.get('errors', 0)
                    cached = api_stats.get('cached_responses', 0)
                    rate_limited = api_stats.get('rate_limited', 0)
                    
                    metrics.extend([
                        f'# HELP email_categorizer_api_requests_total Total API requests',
                        f'# TYPE email_categorizer_api_requests_total counter',
                        f'email_categorizer_api_requests_total{{api="{api_name}"}} {total_requests}',
                        '',
                        f'# HELP email_categorizer_api_errors_total Total API errors',
                        f'# TYPE email_categorizer_api_errors_total counter',
                        f'email_categorizer_api_errors_total{{api="{api_name}"}} {errors}',
                        '',
                        f'# HELP email_categorizer_api_cached_total Total cached responses',
                        f'# TYPE email_categorizer_api_cached_total counter',
                        f'email_categorizer_api_cached_total{{api="{api_name}"}} {cached}',
                        '',
                        f'# HELP email_categorizer_api_rate_limited_total Total rate limited requests',
                        f'# TYPE email_categorizer_api_rate_limited_total counter',
                        f'email_categorizer_api_rate_limited_total{{api="{api_name}"}} {rate_limited}',
                        ''
                    ])
                    
                    # Calculate rates
                    if total_requests > 0:
                        error_rate = (errors / total_requests) * 100
                        cache_hit_rate = (cached / total_requests) * 100
                        rate_limit_rate = (rate_limited / total_requests) * 100
                        
                        metrics.extend([
                            f'# HELP email_categorizer_api_error_rate_percent API error rate percentage',
                            f'# TYPE email_categorizer_api_error_rate_percent gauge',
                            f'email_categorizer_api_error_rate_percent{{api="{api_name}"}} {error_rate:.2f}',
                            '',
                            f'# HELP email_categorizer_api_cache_hit_rate_percent Cache hit rate percentage',
                            f'# TYPE email_categorizer_api_cache_hit_rate_percent gauge',
                            f'email_categorizer_api_cache_hit_rate_percent{{api="{api_name}"}} {cache_hit_rate:.2f}',
                            '',
                            f'# HELP email_categorizer_api_rate_limit_rate_percent Rate limit rate percentage',
                            f'# TYPE email_categorizer_api_rate_limit_rate_percent gauge',
                            f'email_categorizer_api_rate_limit_rate_percent{{api="{api_name}"}} {rate_limit_rate:.2f}',
                            ''
                        ])
                
                # System metrics
                metrics.extend([
                    f'# HELP email_categorizer_system_timestamp_seconds Current system timestamp',
                    f'# TYPE email_categorizer_system_timestamp_seconds gauge',
                    f'email_categorizer_system_timestamp_seconds {time.time()}',
                    '',
                    f'# HELP email_categorizer_alerts_active Number of active alerts',
                    f'# TYPE email_categorizer_alerts_active gauge',
                    f'email_categorizer_alerts_active {len(self.check_alerts())}',
                    ''
                ])
                
                return '\n'.join(metrics)
            
            def log_message(self, format, *args):
                """Override to reduce logging noise."""
                pass
        
        # Bind to specific handler instance
        MetricsHandler.check_alerts = lambda self: api_monitor.check_alerts()
        
        server = HTTPServer(('0.0.0.0', port), MetricsHandler)
        print(f"📊 Metrics server started on port {port}")
        print(f"🔗 Metrics endpoint: http://localhost:{port}/metrics")
        print(f"❤️  Health endpoint: http://localhost:{port}/health")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n📊 Metrics server stopped")
            server.shutdown()

# Global monitor instance
api_monitor = APIMonitor()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="API Usage Monitor")
    parser.add_argument('--report', action='store_true', help='Generate daily report')
    parser.add_argument('--alerts', action='store_true', help='Check for alerts')
    parser.add_argument('--log', action='store_true', help='Log current usage')
    parser.add_argument('--serve-metrics', action='store_true', help='Start Prometheus metrics server')
    parser.add_argument('--port', type=int, default=8000, help='Port for metrics server (default: 8000)')
    
    args = parser.parse_args()
    
    if args.serve_metrics:
        api_monitor.serve_metrics(args.port)
    elif args.report:
        api_monitor.generate_daily_report()
    elif args.alerts:
        api_monitor.print_alerts()
    elif args.log:
        api_monitor.log_usage()
        print("Usage logged successfully.")
    else:
        # Default: show current status
        rate_limiter.print_usage_report()
        api_monitor.print_alerts()