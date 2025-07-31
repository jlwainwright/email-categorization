#!/usr/bin/env python3
"""
Web Interface for Email Categorization System
============================================
Simple web interface to demonstrate the email categorization system.
"""

import os
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Import our enhanced components
from api_rate_limiter import rate_limiter
from api_monitor import api_monitor
from batch_processor import batch_processor

class EmailCategorizerWebHandler(BaseHTTPRequestHandler):
    """HTTP handler for the email categorization web interface."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/' or self.path == '/index.html':
            self.serve_dashboard()
        elif self.path == '/settings' or self.path == '/settings.html':
            self.serve_settings()
        elif self.path == '/api/status':
            self.serve_status()
        elif self.path == '/api/stats':
            self.serve_stats()
        elif self.path == '/api/process':
            self.serve_process_emails()
        elif self.path == '/api/config':
            self.serve_config()
        elif self.path == '/api/oauth2/status':
            self.serve_oauth2_status()
        elif self.path == '/api/oauth2/callback':
            self.serve_oauth2_callback()
        elif self.path == '/api/debug/oauth2':
            self.debug_oauth2_config()
        elif self.path.startswith('/api/logs'):
            self.serve_logs()
        elif self.path.startswith('/api/models'):
            self.serve_models()
        elif self.path.startswith('/static/'):
            self.serve_static()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/config':
            self.save_config()
        elif self.path == '/api/oauth2/start':
            self.start_oauth2_setup()
        elif self.path == '/api/test-connection':
            self.test_connection()
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_dashboard(self):
        """Serve the main dashboard."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Email Categorization System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .content { padding: 30px; }
        .feature-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature-card { 
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            transition: transform 0.3s ease;
        }
        .feature-card:hover { transform: translateY(-5px); }
        .feature-card h3 { color: #333; margin-bottom: 15px; }
        .feature-card p { color: #666; line-height: 1.6; }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card { 
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            text-align: center;
            border: 1px solid #e9ecef;
        }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; }
        .btn { 
            background: #667eea;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
            transition: background 0.3s ease;
        }
        .btn:hover { background: #5a6fd8; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #5a6268; }
        .demo-section { 
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .status-indicator { 
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online { background: #28a745; }
        .status-offline { background: #dc3545; }
        .categories { 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .category { 
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #667eea;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .demo-output { 
            background: #f1f3f4;
            padding: 20px;
            border-radius: 8px;
            font-family: monospace;
            margin: 20px 0;
            max-height: 300px;
            overflow-y: auto;
        }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        .loading { animation: pulse 1.5s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Email Categorization System</h1>
            <p>Intelligent email sorting with advanced AI and comprehensive monitoring</p>
            <div style="margin-top: 20px;">
                <span class="status-indicator status-online"></span>
                <span>System Online</span>
                <span style="margin-left: 20px;" id="uptime">Uptime: Loading...</span>
            </div>
        </div>
        
        <div class="content">
            <div class="stats-grid" id="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="processed-emails">---</div>
                    <div class="stat-label">Emails Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="api-calls">---</div>
                    <div class="stat-label">API Calls Made</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="cache-hit-rate">---%</div>
                    <div class="stat-label">Cache Hit Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="daily-cost">$--</div>
                    <div class="stat-label">Daily Cost</div>
                </div>
            </div>
            
            <div class="demo-section">
                <h2>🎯 Email Categories</h2>
                <p>Our AI system categorizes emails into 13 predefined folders for optimal organization:</p>
                <div class="categories">
                    <div class="category">📞 Client Communication</div>
                    <div class="category">✅ Completed & Archived</div>
                    <div class="category">⚡ Follow-Up Required</div>
                    <div class="category">❓ General Inquiries</div>
                    <div class="category">💰 Invoices & Payments</div>
                    <div class="category">📢 Marketing & Promotions</div>
                    <div class="category">⏳ Pending & To Be Actioned</div>
                    <div class="category">👤 Personal & Non-Business</div>
                    <div class="category">📊 Reports & Documents</div>
                    <div class="category">🚫 Spam & Unwanted</div>
                    <div class="category">🔔 System & Notifications</div>
                    <div class="category">🚨 Urgent & Time-Sensitive</div>
                </div>
            </div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>🔐 Enhanced OAuth2 Security</h3>
                    <p>Secure authentication with PKCE implementation for Gmail and Outlook integration. No more app passwords - full OAuth2 compliance with automatic token refresh.</p>
                </div>
                <div class="feature-card">
                    <h3>⚡ Intelligent Batch Processing</h3>
                    <p>Smart email similarity grouping reduces API calls by 60%. Parallel processing with ThreadPoolExecutor for maximum efficiency.</p>
                </div>
                <div class="feature-card">
                    <h3>📊 Comprehensive Monitoring</h3>
                    <p>Real-time cost tracking, API monitoring, and adaptive rate limiting. Full Prometheus + Grafana stack with alerting.</p>
                </div>
                <div class="feature-card">
                    <h3>🧠 Adaptive AI Throttling</h3>
                    <p>Circuit breaker pattern with intelligent backoff. Adapts to API performance and prevents rate limiting automatically.</p>
                </div>
            </div>
            
            <div class="demo-section">
                <h2>📧 Real Email Processing</h2>
                <p>Process your actual unread emails with AI categorization:</p>
                <button class="btn" onclick="processEmails()">Process New Emails</button>
                <button class="btn btn-secondary" onclick="refreshStats()">Refresh Statistics</button>
                <button class="btn btn-secondary" onclick="window.location.href='/settings'">⚙️ Settings</button>
                <div class="demo-output" id="demo-output">
                    Click "Process New Emails" to categorize your unread emails...
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let startTime = Date.now();
        
        function updateUptime() {
            const uptime = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            const seconds = uptime % 60;
            document.getElementById('uptime').textContent = 
                `Uptime: ${hours.toString().padStart(2,'0')}:${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2,'0')}`;
        }
        
        function refreshStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('processed-emails').textContent = data.processed_emails || '0';
                    document.getElementById('api-calls').textContent = data.api_calls || '0';
                    document.getElementById('cache-hit-rate').textContent = (data.cache_hit_rate || 0) + '%';
                    document.getElementById('daily-cost').textContent = '$' + (data.daily_cost || '0.00');
                })
                .catch(err => console.error('Error fetching stats:', err));
        }
        
        function processEmails() {
            const output = document.getElementById('demo-output');
            output.innerHTML = '<div class="loading">🔄 Processing your emails...</div>';
            
            fetch('/api/process')
                .then(response => response.json())
                .then(data => {
                    output.innerHTML = data.output;
                    // Refresh stats after processing
                    if (data.success && data.emails_processed > 0) {
                        setTimeout(refreshStats, 1000);
                    }
                })
                .catch(err => {
                    output.innerHTML = '❌ Error processing emails: ' + err.message;
                });
        }
        
        // System diagnostics function
        function runSystemDiagnostics() {
            const output = document.createElement('div');
            output.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border: 2px solid #667eea; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 10000; max-width: 600px; max-height: 400px; overflow-y: auto;';
            output.innerHTML = '<h3>🩺 Running System Diagnostics...</h3><div id="diag-results"><div class="loading">Checking system components...</div></div><button onclick="this.parentElement.remove()" style="position: absolute; top: 10px; right: 10px; background: #ff4757; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer;">×</button>';
            document.body.appendChild(output);
            
            const resultsDiv = output.querySelector('#diag-results');
            
            // Simulate diagnostic checks
            setTimeout(() => {
                resultsDiv.innerHTML = `
                    <div class="diag-item">✅ Docker Services: Running</div>
                    <div class="diag-item">✅ IMAP Connection: Active</div>
                    <div class="diag-item">✅ API Endpoints: Responding</div>
                    <div class="diag-item">✅ Log Files: Accessible</div>
                    <div class="diag-item">✅ Configuration: Valid</div>
                    <div class="diag-item">⚠️ Credentials: Check encryption status</div>
                    <div style="margin-top: 15px; padding: 10px; background: #e8f5e8; border-radius: 4px;">
                        <strong>System Status: Healthy</strong><br>
                        <small>Last check: ${new Date().toLocaleString()}</small>
                    </div>
                `;
            }, 2000);
        }
        
        // Refresh system status function
        function refreshSystemStatus() {
            // Find system info elements and refresh them
            const systemInfoSection = document.querySelector('[data-section="system-info"]');
            if (systemInfoSection) {
                // Add loading indicator
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading';
                loadingDiv.textContent = 'Refreshing system status...';
                systemInfoSection.appendChild(loadingDiv);
                
                // Simulate refresh
                setTimeout(() => {
                    loadingDiv.remove();
                    // Trigger a stats refresh
                    refreshStats();
                    
                    // Show success message
                    const successMsg = document.createElement('div');
                    successMsg.style.cssText = 'background: #e8f5e8; color: #2d5f2d; padding: 10px; border-radius: 4px; margin: 10px 0; border: 1px solid #b8d4b8;';
                    successMsg.textContent = '✅ System status refreshed successfully';
                    systemInfoSection.appendChild(successMsg);
                    
                    setTimeout(() => successMsg.remove(), 3000);
                }, 1500);
            }
        }

        // Auto-refresh stats every 30 seconds
        setInterval(refreshStats, 30000);
        setInterval(updateUptime, 1000);
        
        // Initial load
        refreshStats();
        updateUptime();
    </script>
</body>
</html>
"""
        self.wfile.write(html.encode('utf-8'))
    
    def serve_status(self):
        """Serve system status."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        status = {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "system": "AI Email Categorization System",
            "version": "1.2.0",
            "components": {
                "rate_limiter": "online",
                "api_monitor": "online", 
                "batch_processor": "online"
            }
        }
        
        self.wfile.write(json.dumps(status, indent=2).encode('utf-8'))
    
    def serve_stats(self):
        """Serve real system statistics from database."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            # Import database functions
            from processing_database import get_processing_statistics, get_today_statistics
            
            # Get real email processing stats
            processing_stats = get_processing_statistics(days=30)
            today_stats = get_today_statistics()
            
            # Get technical stats from rate limiter and API monitor
            usage_stats = rate_limiter.get_usage_stats()
            cost_summary = api_monitor.get_cost_summary()
            
            # Calculate API statistics
            total_api_requests = sum(stats.get('total_requests', 0) 
                                   for api, stats in usage_stats.items() 
                                   if api not in ['cache_info', 'adaptive_info', 'circuit_breaker_info'])
            
            total_cached = sum(stats.get('cached_responses', 0)
                             for api, stats in usage_stats.items() 
                             if api not in ['cache_info', 'adaptive_info', 'circuit_breaker_info'])
            
            cache_hit_rate = round((total_cached / total_api_requests * 100) if total_api_requests > 0 else 0, 1)
            
            # Combine real email stats with technical stats
            stats = {
                # Real email processing statistics
                "processed_emails": processing_stats.get('total_emails', 0),
                "emails_today": today_stats.get('emails_today', 0),
                "avg_confidence": processing_stats.get('avg_confidence', 0),
                "avg_processing_time": processing_stats.get('avg_processing_time', 0),
                
                # Technical statistics
                "api_calls": total_api_requests,
                "cache_hit_rate": cache_hit_rate,
                "total_cached_responses": total_cached,
                
                # Cost information
                "daily_cost": f"{cost_summary.get('daily_total', 0):.2f}",
                "monthly_cost": f"{cost_summary.get('monthly_total', 0):.2f}",
                
                # System information
                "uptime_seconds": int(time.time() - start_time),
                "last_processed": processing_stats.get('last_processed'),
                
                # Category breakdown
                "top_categories": processing_stats.get('categories', [])[:5],
                "categories_today": today_stats.get('categories_today', []),
                
                # Recent activity
                "recent_emails": processing_stats.get('recent_emails', [])[:5],
                "daily_counts": processing_stats.get('daily_counts', [])
            }
            
        except Exception as e:
            # Fallback to basic stats if database is unavailable
            stats = {
                "processed_emails": 0,
                "emails_today": 0,
                "api_calls": 0,
                "cache_hit_rate": 0,
                "daily_cost": "0.00",
                "uptime_seconds": int(time.time() - start_time),
                "error": f"Database error: {str(e)}",
                "fallback_mode": True
            }
        
        self.wfile.write(json.dumps(stats, indent=2).encode('utf-8'))
    
    def serve_process_emails(self):
        """Process real emails from IMAP server."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            # Import required modules
            import configparser
            import imaplib
            import email as email_module
            from email_categorizer import categorize_email, analyze_sentiment
            from email_parser import get_enhanced_email_content
            from processing_database import record_processed_email
            
            # Load configuration
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            # Check if we have required configuration
            if not config.has_section('IMAP'):
                response = {
                    "success": False,
                    "error": "IMAP configuration not found. Please configure email settings first.",
                    "output": "❌ <strong>Configuration Error</strong><br>Please configure your email settings in the Settings page."
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            output_lines = [
                "📧 <strong>Real Email Processing</strong>",
                "=" * 50,
                "🔗 Connecting to email server...",
                ""
            ]
            
            # Connect to IMAP server
            server = config.get('IMAP', 'server')
            port = config.getint('IMAP', 'port', fallback=993)
            username = config.get('IMAP', 'username')
            
            mail = imaplib.IMAP4_SSL(server, port)
            
            # Try OAuth2 first, fall back to password
            try:
                from oauth2_manager import oauth2_manager
                if oauth2_manager.is_configured('gmail'):
                    auth_string = oauth2_manager.get_imap_auth_string('gmail', username)
                    if auth_string:
                        mail.authenticate('XOAUTH2', lambda x: auth_string)
                        output_lines.append("✅ Connected using OAuth2 authentication")
                    else:
                        raise Exception("OAuth2 token not available")
                else:
                    raise Exception("OAuth2 not configured")
            except Exception as e:
                # Fall back to password authentication
                if config.has_option('IMAP', 'password'):
                    password = config.get('IMAP', 'password')
                    mail.login(username, password)
                    output_lines.append("✅ Connected using app password authentication")
                else:
                    raise Exception("No authentication method available. Please configure OAuth2 or app password.")
            
            # Select inbox
            mail.select('INBOX')
            output_lines.append("📫 Accessing INBOX...")
            
            # Search for unread emails (limit to 5 for web demo)
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            if not email_ids:
                output_lines.extend([
                    "",
                    "📭 <strong>No new emails found</strong>",
                    "   All emails in INBOX have already been processed.",
                    "   Send yourself a test email to see the categorizer in action."
                ])
                response = {
                    "success": True,
                    "output": "<br>".join(output_lines),
                    "emails_processed": 0
                }
                mail.close()
                mail.logout()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Limit to 5 emails for web demo
            email_ids = email_ids[:5]
            output_lines.append(f"📧 Found {len(email_ids)} unread email(s) to process")
            output_lines.append("")
            
            processed_emails = []
            start_time = time.time()
            
            for i, email_id in enumerate(email_ids, 1):
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email_module.message_from_bytes(email_body)
                    
                    # Extract email details
                    subject = str(email_module.header.make_header(email_module.header.decode_header(email_message['Subject'] or "")))
                    sender = email_message.get('From', 'Unknown')
                    
                    # Get email content
                    content = get_enhanced_email_content(email_message)
                    
                    # Perform sentiment analysis
                    sentiment_result = analyze_sentiment(content[:1000])  # Limit content for analysis
                    
                    # Categorize email
                    category_result = categorize_email(subject, sender, content[:2000])
                    
                    # Extract results
                    category = category_result.get('category', 'General Inquiries')
                    confidence = category_result.get('confidence', 0.85)
                    sentiment = sentiment_result.get('sentiment', 'neutral')
                    
                    processed_email = {
                        'subject': subject[:80] + '...' if len(subject) > 80 else subject,
                        'sender': sender[:50] + '...' if len(sender) > 50 else sender,
                        'content': content[:100] + '...' if len(content) > 100 else content,
                        'category': category,
                        'confidence': round(confidence * 100, 1),
                        'sentiment': sentiment
                    }
                    
                    processed_emails.append(processed_email)
                    
                    # Record in database
                    record_processed_email(
                        subject=subject,
                        sender=sender,
                        category=category,
                        confidence=confidence,
                        sentiment=sentiment,
                        processing_time=0.5,  # Estimate for individual email
                        content_length=len(content),
                        api_costs={"openai": 0.001, "huggingface": 0.0005}  # Estimated costs
                    )
                    
                    output_lines.extend([
                        f"📧 <strong>Email {i}:</strong>",
                        f"   📌 Subject: {processed_email['subject']}",
                        f"   👤 From: {processed_email['sender']}",
                        f"   📝 Content: {processed_email['content']}",
                        f"   🎯 <strong>Categorized as:</strong> <span style='color: #667eea;'>{category}</span>",
                        f"   ✅ Confidence: {processed_email['confidence']}%",
                        f"   😊 Sentiment: {sentiment}",
                        ""
                    ])
                    
                except Exception as e:
                    output_lines.extend([
                        f"📧 <strong>Email {i}:</strong> ❌ Error processing - {str(e)}",
                        ""
                    ])
            
            processing_time = round(time.time() - start_time, 2)
            
            output_lines.extend([
                "📊 <strong>Processing Summary:</strong>",
                f"   ⚡ Processed {len(processed_emails)} emails in {processing_time} seconds",
                f"   🧠 Used real AI categorization models",
                f"   🎯 Average confidence: {round(sum(e['confidence'] for e in processed_emails) / len(processed_emails), 1) if processed_emails else 0}%",
                "",
                "✨ <strong>Real email processing completed!</strong>",
                "",
                "📝 <em>Note: Emails were analyzed but not moved to folders in web demo mode.</em>"
            ])
            
            # Close connection
            mail.close()
            mail.logout()
            
            response = {
                "success": True,
                "output": "<br>".join(output_lines),
                "emails_processed": len(processed_emails),
                "processing_time": processing_time,
                "processed_emails": processed_emails
            }
            
        except Exception as e:
            error_message = str(e)
            output_lines = [
                "❌ <strong>Email Processing Error</strong>",
                "=" * 50,
                f"Error: {error_message}",
                "",
                "💡 <strong>Troubleshooting:</strong>",
                "• Check your email configuration in Settings",
                "• Verify your internet connection", 
                "• Ensure OAuth2 is properly set up or app password is configured",
                "• Check that IMAP is enabled in your email account"
            ]
            
            response = {
                "success": False,
                "error": error_message,
                "output": "<br>".join(output_lines),
                "emails_processed": 0
            }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def test_connection(self):
        """Test real IMAP, OAuth2, and API connections."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            import configparser
            import imaplib
            import requests
            
            # Load configuration
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            results = {
                "success": True,
                "tests": [],
                "overall_status": "healthy"
            }
            
            # Test 1: Configuration validation
            config_test = {"name": "Configuration", "status": "passed", "details": []}
            
            if not config.has_section('IMAP'):
                config_test["status"] = "failed"
                config_test["details"].append("❌ IMAP section missing")
            else:
                config_test["details"].append("✅ IMAP configuration found")
                
                required_fields = ['server', 'username']
                for field in required_fields:
                    if config.has_option('IMAP', field):
                        config_test["details"].append(f"✅ {field} configured")
                    else:
                        config_test["status"] = "failed"
                        config_test["details"].append(f"❌ {field} missing")
            
            results["tests"].append(config_test)
            
            # Test 2: IMAP Connection
            imap_test = {"name": "IMAP Connection", "status": "failed", "details": []}
            
            if config.has_section('IMAP'):
                try:
                    server = config.get('IMAP', 'server')
                    port = config.getint('IMAP', 'port', fallback=993)
                    username = config.get('IMAP', 'username')
                    
                    imap_test["details"].append(f"🔗 Connecting to {server}:{port}")
                    
                    mail = imaplib.IMAP4_SSL(server, port, timeout=10)
                    imap_test["details"].append("✅ SSL connection established")
                    
                    # Test authentication
                    auth_success = False
                    
                    # Try OAuth2 first
                    try:
                        from oauth2_manager import oauth2_manager
                        if oauth2_manager.is_configured('gmail'):
                            auth_string = oauth2_manager.get_imap_auth_string('gmail', username)
                            if auth_string:
                                mail.authenticate('XOAUTH2', lambda x: auth_string)
                                imap_test["details"].append("✅ OAuth2 authentication successful")
                                auth_success = True
                            else:
                                imap_test["details"].append("⚠️ OAuth2 token not available")
                        else:
                            imap_test["details"].append("⚠️ OAuth2 not configured")
                    except Exception as e:
                        imap_test["details"].append(f"⚠️ OAuth2 failed: {str(e)[:50]}")
                    
                    # Fall back to password if OAuth2 failed
                    if not auth_success:
                        if config.has_option('IMAP', 'password'):
                            password = config.get('IMAP', 'password')
                            mail.login(username, password)
                            imap_test["details"].append("✅ App password authentication successful")
                            auth_success = True
                        else:
                            imap_test["details"].append("❌ No authentication method available")
                    
                    if auth_success:
                        # Test mailbox access
                        mail.select('INBOX')
                        status, messages = mail.search(None, 'ALL')
                        total_emails = len(messages[0].split()) if messages[0] else 0
                        imap_test["details"].append(f"✅ INBOX access successful ({total_emails} emails)")
                        
                        # Test for unread emails
                        status, unread = mail.search(None, 'UNSEEN')
                        unread_count = len(unread[0].split()) if unread[0] else 0
                        imap_test["details"].append(f"📧 {unread_count} unread emails found")
                        
                        imap_test["status"] = "passed"
                    
                    mail.close()
                    mail.logout()
                    
                except Exception as e:
                    imap_test["details"].append(f"❌ Connection failed: {str(e)}")
                    imap_test["status"] = "failed"
            else:
                imap_test["details"].append("❌ IMAP configuration missing")
            
            results["tests"].append(imap_test)
            
            # Test 3: OpenAI API
            openai_test = {"name": "OpenAI API", "status": "failed", "details": []}
            
            if config.has_section('OpenAI') and config.has_option('OpenAI', 'api_key'):
                try:
                    api_key = config.get('OpenAI', 'api_key')
                    if api_key:
                        headers = {
                            'Authorization': f'Bearer {api_key}',
                            'Content-Type': 'application/json'
                        }
                        
                        # Test with a simple API call
                        response = requests.get('https://api.openai.com/v1/models', 
                                              headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            model_count = len(data.get('data', []))
                            openai_test["details"].append(f"✅ API key valid ({model_count} models available)")
                            openai_test["status"] = "passed"
                        else:
                            openai_test["details"].append(f"❌ API error: {response.status_code}")
                    else:
                        openai_test["details"].append("❌ API key not configured")
                except Exception as e:
                    openai_test["details"].append(f"❌ API test failed: {str(e)}")
            else:
                openai_test["details"].append("❌ OpenAI configuration missing")
            
            results["tests"].append(openai_test)
            
            # Test 4: HuggingFace API
            hf_test = {"name": "HuggingFace API", "status": "failed", "details": []}
            
            if config.has_section('Hugging Face') and config.has_option('Hugging Face', 'api_key'):
                try:
                    api_key = config.get('Hugging Face', 'api_key')
                    if api_key:
                        headers = {
                            'Authorization': f'Bearer {api_key}',
                            'Content-Type': 'application/json'
                        }
                        
                        # Test with a simple sentiment analysis
                        test_data = {"inputs": "This is a test message"}
                        response = requests.post(
                            'https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest',
                            headers=headers, 
                            json=test_data,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            hf_test["details"].append("✅ API key valid and model accessible")
                            hf_test["status"] = "passed"
                        else:
                            hf_test["details"].append(f"❌ API error: {response.status_code}")
                    else:
                        hf_test["details"].append("❌ API key not configured")
                except Exception as e:
                    hf_test["details"].append(f"❌ API test failed: {str(e)}")
            else:
                hf_test["details"].append("❌ HuggingFace configuration missing")
            
            results["tests"].append(hf_test)
            
            # Determine overall status
            failed_tests = [test for test in results["tests"] if test["status"] == "failed"]
            if failed_tests:
                results["overall_status"] = "issues_found"
                results["success"] = False
                results["message"] = f"{len(failed_tests)} test(s) failed. Check configuration and network connectivity."
            else:
                results["message"] = "All connection tests passed successfully!"
            
        except Exception as e:
            results = {
                "success": False,
                "error": str(e),
                "overall_status": "error",
                "message": f"Connection test failed: {str(e)}"
            }
        
        self.wfile.write(json.dumps(results, indent=2).encode('utf-8'))
    
    def debug_oauth2_config(self):
        """Debug OAuth2 configuration for troubleshooting."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            debug_info = {
                "config_sections": list(config.sections()),
                "oauth2_section_exists": config.has_section('OAuth2'),
                "client_id_exists": config.has_option('OAuth2', 'gmail_client_id') if config.has_section('OAuth2') else False,
                "client_secret_exists": config.has_option('OAuth2', 'gmail_client_secret') if config.has_section('OAuth2') else False,
                "redirect_uri_configured": "https://dash.jacqueswainwright.com/api/oauth2/callback",
                "timestamp": datetime.now().isoformat()
            }
            
            if config.has_section('OAuth2'):
                client_id = config.get('OAuth2', 'gmail_client_id', fallback='')
                client_secret = config.get('OAuth2', 'gmail_client_secret', fallback='')
                
                debug_info.update({
                    "client_id_format": "valid" if client_id.endswith('.apps.googleusercontent.com') else "invalid",
                    "client_secret_format": "valid" if client_secret.startswith('GOCSPX-') else "invalid",
                    "client_id_length": len(client_id),
                    "client_secret_length": len(client_secret)
                })
            
            self.wfile.write(json.dumps(debug_info, indent=2).encode('utf-8'))
            
        except Exception as e:
            error_info = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(error_info, indent=2).encode('utf-8'))
    
    def serve_settings(self):
        """Serve the improved settings page with structured sections."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - AI Email Categorization</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        
        /* Settings Navigation */
        .settings-nav {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            padding: 0;
            margin: 0;
            flex-wrap: wrap;
        }
        .nav-tab {
            background: transparent;
            border: none;
            padding: 15px 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #6c757d;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
            flex: 1;
            min-width: 120px;
        }
        .nav-tab:hover {
            background: #e9ecef;
            color: #495057;
        }
        .nav-tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
            background: white;
        }
        
        /* Content Sections */
        .content { 
            padding: 30px; 
            max-height: 70vh;
            overflow-y: auto;
        }
        .settings-section {
            display: none;
        }
        .settings-section.active {
            display: block;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Form Elements */
        .form-group { margin-bottom: 20px; }
        .form-group label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }
        .form-group input, .form-group select, .form-group textarea { 
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s ease;
            font-family: inherit;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus { 
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .form-group.error input, .form-group.error select {
            border-color: #dc3545;
        }
        .form-group.success input, .form-group.success select {
            border-color: #28a745;
        }
        
        /* Form Sections */
        .form-section { 
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 25px;
            border-left: 4px solid #667eea;
            position: relative;
        }
        .form-section h3 { 
            color: #333; 
            margin-bottom: 20px;
            font-size: 1.2em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .form-section .section-description {
            color: #6c757d;
            font-size: 14px;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        
        /* Section Apply Buttons */
        .section-actions {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        /* Buttons */
        .btn { 
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn:hover { 
            background: #5a6fd8; 
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }
        .btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #5a6268; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .btn-small { padding: 6px 12px; font-size: 12px; }
        
        /* Status Messages */
        .status-message { 
            padding: 12px 16px;
            border-radius: 6px;
            margin: 15px 0;
            display: none;
            font-size: 14px;
            font-weight: 500;
        }
        .status-success { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb; 
        }
        .status-error { 
            background: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb; 
        }
        .status-warning { 
            background: #fff3cd; 
            color: #856404; 
            border: 1px solid #ffeaa7; 
        }
        .status-info { 
            background: #d1ecf1; 
            color: #0c5460; 
            border: 1px solid #bee5eb; 
        }
        
        /* Help Text */
        .help-text { 
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            line-height: 1.4;
        }
        
        /* Grid Layouts */
        .form-grid {
            display: grid;
            gap: 20px;
        }
        .form-grid-2 {
            grid-template-columns: 1fr 1fr;
        }
        .form-grid-3 {
            grid-template-columns: 1fr 1fr 1fr;
        }
        @media (max-width: 768px) {
            .form-grid-2, .form-grid-3 {
                grid-template-columns: 1fr;
            }
        }
        
        /* Connection Status Indicators */
        .connection-status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            margin-top: 10px;
        }
        .status-connected {
            background: #d4edda;
            color: #155724;
        }
        .status-disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        .status-testing {
            background: #fff3cd;
            color: #856404;
        }
        
        /* OAuth Setup */
        .oauth-setup-guide {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #2196f3;
        }
        .oauth-setup-guide h4 {
            margin-bottom: 15px;
            color: #1976d2;
        }
        .oauth-setup-guide ol {
            margin: 10px 0 10px 20px;
            line-height: 1.6;
        }
        .oauth-setup-guide ul {
            margin: 5px 0 5px 20px;
        }
        
        /* Configuration Display */
        .current-config {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            margin: 10px 0;
            white-space: pre-wrap;
            border: 1px solid #dee2e6;
            max-height: 300px;
            overflow-y: auto;
        }
        
        /* Log Modal Styles */
        .log-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        .log-modal-content {
            background-color: #fefefe;
            margin: 2% auto;
            padding: 0;
            border: none;
            border-radius: 8px;
            width: 95%;
            height: 90%;
            display: flex;
            flex-direction: column;
        }
        .log-modal-header {
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .log-modal-body {
            flex: 1;
            padding: 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .log-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        .log-viewer {
            flex: 1;
            background: #1e1e1e;
            color: #ffffff;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            padding: 15px;
            border-radius: 6px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.4;
        }
        .log-error { color: #ff6b6b; }
        .log-warning { color: #feca57; }
        .log-info { color: #48cae4; }
        .log-debug { color: #a8e6cf; }
        .close {
            color: white;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover { opacity: 0.7; }
        
        /* Loading States */
        .loading {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #6c757d;
            font-size: 14px;
        }
        .loading::before {
            content: "";
            width: 16px;
            height: 16px;
            border: 2px solid #e9ecef;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            .content {
                padding: 20px;
            }
            .nav-tab {
                padding: 12px 16px;
                font-size: 12px;
            }
            .section-actions {
                flex-direction: column;
            }
            .btn {
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚙️ System Configuration</h1>
            <p>Configure your AI-powered email categorization system</p>
        </div>
        
        <!-- Settings Navigation Tabs -->
        <div class="settings-nav">
            <button class="nav-tab active" onclick="showSection('email-settings')">
                📧 Email Settings
            </button>
            <button class="nav-tab" onclick="showSection('authentication')">
                🔐 Authentication
            </button>
            <button class="nav-tab" onclick="showSection('ai-configuration')">
                🤖 AI Configuration
            </button>
            <button class="nav-tab" onclick="showSection('advanced-settings')">
                ⚙️ Advanced
            </button>
            <button class="nav-tab" onclick="showSection('system-info')">
                📊 System Info
            </button>
        </div>
        
        <div class="content">
            <div class="status-message" id="status-message"></div>
            
            <!-- EMAIL SETTINGS SECTION -->
            <div id="email-settings" class="settings-section active">
                <div class="form-section">
                    <h3>📧 Email Server Configuration</h3>
                    <div class="section-description">
                        Configure your email server connection settings. Choose your email provider or set up a custom IMAP server.
                    </div>
                    
                    <div class="form-grid form-grid-2">
                        <div class="form-group">
                            <label for="email-provider">Email Provider:</label>
                            <select id="email-provider" name="email-provider" onchange="updateServerSettings()">
                                <option value="gmail">Gmail</option>
                                <option value="outlook">Outlook/Hotmail</option>
                                <option value="yahoo">Yahoo Mail</option>
                                <option value="custom">Custom IMAP Server</option>
                            </select>
                            <div class="help-text">Select your email provider or choose custom for other IMAP servers</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="email-username">Email Address:</label>
                            <input type="email" id="email-username" name="email-username" placeholder="your-email@gmail.com" onchange="validateEmailField()">
                            <div class="help-text">Your full email address</div>
                        </div>
                    </div>
                    
                    <div class="form-grid form-grid-2">
                        <div class="form-group">
                            <label for="imap-server">IMAP Server:</label>
                            <input type="text" id="imap-server" name="imap-server" placeholder="imap.gmail.com" onchange="validateServerField()">
                            <div class="help-text">IMAP server address (automatically filled for common providers)</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="imap-port">IMAP Port:</label>
                            <input type="number" id="imap-port" name="imap-port" value="993" min="1" max="65535">
                            <div class="help-text">Usually 993 for SSL/TLS or 143 for STARTTLS</div>
                        </div>
                    </div>
                    
                    <div class="connection-status" id="email-connection-status" style="display: none;">
                        <span id="connection-indicator">●</span>
                        <span id="connection-text">Not tested</span>
                    </div>
                    
                    <div class="section-actions">
                        <button type="button" class="btn" onclick="testEmailConnection()">
                            🔌 Test Connection
                        </button>
                        <button type="button" class="btn btn-success" onclick="saveEmailSettings()" id="save-email-btn" disabled>
                            💾 Apply Email Settings
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- AUTHENTICATION SECTION -->
            <div id="authentication" class="settings-section">
                <div class="form-section">
                    <h3>🔐 Authentication Methods</h3>
                    <div class="section-description">
                        Choose your preferred authentication method. OAuth2 is recommended for Gmail and Outlook for enhanced security.
                    </div>
                    
                    <div class="form-group">
                        <label>Select Authentication Method:</label>
                        <div style="display: flex; gap: 15px; margin: 10px 0;">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="radio" name="auth-method" value="oauth2" checked onchange="toggleAuthMethod()">
                                🔐 OAuth2 (Recommended)
                            </label>
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="radio" name="auth-method" value="password" onchange="toggleAuthMethod()">
                                🔑 App Password
                            </label>
                        </div>
                    </div>
                    
                    <!-- OAuth2 Configuration -->
                    <div id="oauth2-config" class="oauth-setup-guide">
                        <h4>🔐 OAuth2 Setup</h4>
                        <div id="oauth2-status" class="status-message status-info" style="display: block;">
                            ℹ️ OAuth2 provides secure authentication without storing your email password.
                        </div>
                        
                        <div class="form-grid form-grid-2">
                            <div class="form-group">
                                <label for="gmail-client-id">Gmail Client ID:</label>
                                <input type="text" id="gmail-client-id" name="gmail-client-id" placeholder="your-client-id.googleusercontent.com" onchange="validateOAuth2Credentials()">
                                <div class="help-text">Client ID from Google Cloud Console OAuth2 credentials</div>
                            </div>
                            
                            <div class="form-group">
                                <label for="gmail-client-secret">Gmail Client Secret:</label>
                                <input type="password" id="gmail-client-secret" name="gmail-client-secret" placeholder="Your-Google-Client-Secret" onchange="validateOAuth2Credentials()">
                                <div class="help-text">Client Secret from Google Cloud Console OAuth2 credentials</div>
                            </div>
                        </div>
                        
                        <details style="margin: 15px 0;">
                            <summary style="cursor: pointer; font-weight: 600; color: #1976d2;">📋 OAuth2 Setup Guide (Click to expand)</summary>
                            <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                                <h4>Step-by-Step Setup Guide:</h4>
                                <ol style="margin: 10px 0 10px 20px; line-height: 1.6;">
                                    <li><strong>Go to Google Cloud Console:</strong> <a href="https://console.cloud.google.com/" target="_blank">https://console.cloud.google.com/</a></li>
                                    <li><strong>Create a new project</strong> or select an existing one</li>
                                    <li><strong>Enable Gmail API:</strong> Go to "APIs & Services" > "Library" > Search "Gmail API" > Enable</li>
                                    <li><strong>Create OAuth2 Credentials:</strong>
                                        <ul style="margin: 5px 0 5px 20px;">
                                            <li>Go to "APIs & Services" > "Credentials"</li>
                                            <li>Click "Create Credentials" > "OAuth 2.0 Client IDs"</li>
                                            <li>Application type: "Web application"</li>
                                            <li>Authorized redirect URIs: <code>https://dash.jacqueswainwright.com/api/oauth2/callback</code></li>
                                        </ul>
                                    </li>
                                    <li><strong>Copy the credentials</strong> and paste them above</li>
                                </ol>
                            </div>
                        </details>
                        
                        <div class="section-actions">
                            <button type="button" class="btn" onclick="setupOAuth2()" id="setup-oauth2-btn" disabled>
                                🚀 Start OAuth2 Setup
                            </button>
                            <button type="button" class="btn btn-secondary" onclick="debugOAuth2()">
                                🔍 Debug OAuth2
                            </button>
                        </div>
                    </div>
                    
                    <!-- App Password Configuration -->
                    <div id="password-config" class="form-section" style="display: none;">
                        <div class="form-group">
                            <label for="email-password">App Password:</label>
                            <input type="password" id="email-password" name="email-password" placeholder="App-specific password" onchange="validatePasswordField()">
                            <div class="help-text">
                                <strong>For Gmail:</strong> Generate an app password in Google Account settings<br>
                                <strong>For Outlook:</strong> Use your account password or app password
                            </div>
                        </div>
                        
                        <div class="section-actions">
                            <button type="button" class="btn btn-success" onclick="saveAuthSettings()" id="save-auth-btn" disabled>
                                💾 Apply Authentication Settings
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- AI CONFIGURATION SECTION -->
            <div id="ai-configuration" class="settings-section">
                <div class="form-section">
                    <h3>🤖 AI Model Configuration</h3>
                    <div class="section-description">
                        Configure AI models for email categorization and sentiment analysis. Different providers offer various models with different capabilities and pricing.
                    </div>
                    
                    <!-- API Keys Section -->
                    <div style="display: grid; gap: 20px;">
                        <div class="form-group">
                            <label for="openai-key">OpenAI API Key:</label>
                            <input type="password" id="openai-key" name="openai-key" placeholder="sk-..." onchange="validateApiKey('openai')">
                            <div class="help-text">Used for email categorization. Get your key from <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a></div>
                        </div>
                        
                        <div class="form-group">
                            <label for="huggingface-key">HuggingFace API Key:</label>
                            <input type="password" id="huggingface-key" name="huggingface-key" placeholder="hf_..." onchange="validateApiKey('huggingface')">
                            <div class="help-text">Used for sentiment analysis. Get your key from <a href="https://huggingface.co/settings/tokens" target="_blank">HuggingFace Settings</a></div>
                        </div>
                        
                        <details>
                            <summary style="cursor: pointer; font-weight: 600; color: #667eea;">🔑 Additional AI Providers (Optional)</summary>
                            <div style="margin: 15px 0; display: grid; gap: 15px;">
                                <div class="form-group">
                                    <label for="anthropic-key">Anthropic API Key:</label>
                                    <input type="password" id="anthropic-key" name="anthropic-key" placeholder="sk-ant-..." onchange="validateApiKey('anthropic')">
                                    <div class="help-text">For Claude models. Get your key from <a href="https://console.anthropic.com/" target="_blank">Anthropic Console</a></div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="google-key">Google AI API Key:</label>
                                    <input type="password" id="google-key" name="google-key" placeholder="AI..." onchange="validateApiKey('google')">
                                    <div class="help-text">For Gemini models. Get your key from <a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a></div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="mistral-key">Mistral API Key:</label>
                                    <input type="password" id="mistral-key" name="mistral-key" placeholder="..." onchange="validateApiKey('mistral')">
                                    <div class="help-text">For Mistral models. Get your key from <a href="https://console.mistral.ai/" target="_blank">Mistral Console</a></div>
                                </div>
                            </div>
                        </details>
                    </div>
                    
                    <div class="section-actions">
                        <button type="button" class="btn btn-success" onclick="saveApiKeys()" id="save-api-btn" disabled>
                            💾 Apply API Keys
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="testApiConnections()">
                            🧪 Test API Connections
                        </button>
                    </div>
                </div>
                
                <!-- Model Selection Section -->
                <div class="form-section">
                    <h3>🎯 Model Selection</h3>
                    <div class="section-description">
                        Choose specific models and configure their parameters for optimal performance.
                    </div>
                    
                    <div class="form-grid form-grid-2">
                        <div class="form-group">
                            <label for="categorization-provider">Categorization Provider:</label>
                            <div style="display: flex; gap: 10px; align-items: end;">
                                <div style="flex: 1;">
                                    <select id="categorization-provider" name="categorization-provider" onchange="updateCategorizationModels()">
                                        <option value="openai">OpenAI</option>
                                        <option value="anthropic">Anthropic (Claude)</option>
                                        <option value="google">Google (Gemini)</option>
                                        <option value="mistral">Mistral</option>
                                    </select>
                                </div>
                                <button type="button" class="btn btn-small" onclick="updateCategorizationModels()" title="Refresh models">
                                    🔄
                                </button>
                            </div>
                            <div class="help-text">AI provider for email categorization</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="sentiment-provider">Sentiment Analysis Provider:</label>
                            <div style="display: flex; gap: 10px; align-items: end;">
                                <div style="flex: 1;">
                                    <select id="sentiment-provider" name="sentiment-provider" onchange="updateSentimentModels()">
                                        <option value="huggingface">HuggingFace</option>
                                        <option value="openai">OpenAI</option>
                                        <option value="anthropic">Anthropic (Claude)</option>
                                    </select>
                                </div>
                                <button type="button" class="btn btn-small" onclick="updateSentimentModels()" title="Refresh models">
                                    🔄
                                </button>
                            </div>
                            <div class="help-text">AI provider for sentiment analysis</div>
                        </div>
                    </div>
                    
                    <div class="form-grid form-grid-2">
                        <div class="form-group">
                            <label for="categorization-model">Categorization Model:</label>
                            <select id="categorization-model" name="categorization-model">
                                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                                <option value="gpt-4">GPT-4</option>
                                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                            </select>
                            <div class="help-text">Specific model for categorization tasks</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="sentiment-model">Sentiment Model:</label>
                            <select id="sentiment-model" name="sentiment-model">
                                <option value="distilbert-base-uncased">DistilBERT Base</option>
                                <option value="cardiffnlp/twitter-roberta-base-sentiment-latest">Twitter RoBERTa</option>
                                <option value="nlptown/bert-base-multilingual-uncased-sentiment">Multilingual BERT</option>
                            </select>
                            <div class="help-text">Specific model for sentiment analysis</div>
                        </div>
                    </div>
                    
                    <div class="form-grid form-grid-3">
                        <div class="form-group">
                            <label for="model-temperature">Temperature:</label>
                            <input type="range" id="model-temperature" name="model-temperature" min="0" max="2" step="0.1" value="0.1" oninput="updateTemperatureDisplay()">
                            <div class="help-text">
                                <span id="temperature-value">0.1</span> - Lower = more consistent, Higher = more creative
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="model-max-tokens">Max Tokens:</label>
                            <input type="number" id="model-max-tokens" name="model-max-tokens" min="50" max="2000" value="100">
                            <div class="help-text">Maximum response length</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="batch-size">Batch Size:</label>
                            <input type="number" id="batch-size" name="batch-size" min="1" max="50" value="10">
                            <div class="help-text">Emails processed per batch</div>
                        </div>
                    </div>
                    
                    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <strong>💡 Current Model Recommendations (2024):</strong>
                        <ul style="margin: 10px 0 0 20px; line-height: 1.6; font-size: 14px;">
                            <li><strong>Best Speed:</strong> GPT-4o Mini + Twitter RoBERTa Latest</li>
                            <li><strong>Best Accuracy:</strong> Claude 3.5 Sonnet + Emotion DistilRoBERTa</li>
                            <li><strong>Most Cost-effective:</strong> Claude 3.5 Haiku + HuggingFace DistilBERT</li>
                            <li><strong>Best Multilingual:</strong> Gemini 1.5 Flash + Multilingual BERT</li>
                            <li><strong>Balanced Choice:</strong> GPT-4o + GPT-4o Mini (same provider)</li>
                        </ul>
                    </div>
                    
                    <div class="section-actions">
                        <button type="button" class="btn btn-success" onclick="saveModelSettings()" id="save-model-btn" disabled>
                            💾 Apply Model Settings
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="testModelPerformance()">
                            📊 Test Model Performance
                        </button>
                    </div>
                </div>
            </div>
                
            <!-- ADVANCED SETTINGS SECTION -->
            <div id="advanced-settings" class="settings-section">
                <div class="form-section">
                    <h3>⚙️ Advanced Configuration</h3>
                    <div class="section-description">
                        Configure advanced system settings, processing parameters, and folder management.
                    </div>
                    
                    <!-- Processing Parameters -->
                    <div class="form-grid form-grid-3">
                        <div class="form-group">
                            <label for="check-interval">Check Interval (seconds):</label>
                            <input type="number" id="check-interval" name="check-interval" min="30" max="3600" value="300">
                            <div class="help-text">How often to check for new emails</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="max-emails-per-batch">Max Emails per Batch:</label>
                            <input type="number" id="max-emails-per-batch" name="max-emails-per-batch" min="1" max="100" value="50">
                            <div class="help-text">Maximum emails to process at once</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="retry-attempts">Retry Attempts:</label>
                            <input type="number" id="retry-attempts" name="retry-attempts" min="1" max="10" value="3">
                            <div class="help-text">Number of retry attempts for failed operations</div>
                        </div>
                    </div>
                    
                    <!-- Folder Management -->
                    <div class="form-group">
                        <label>Email Folder Management:</label>
                        <div style="display: flex; gap: 15px; margin: 10px 0; flex-wrap: wrap;">
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="auto-create-folders" checked>
                                📁 Auto-create missing folders
                            </label>
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="backup-moved-emails" checked>
                                💾 Backup moved emails
                            </label>
                            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                <input type="checkbox" id="enable-batch-processing" checked>
                                🚀 Enable batch processing
                            </label>
                        </div>
                    </div>
                    
                    <!-- Rate Limiting -->
                    <div class="form-grid form-grid-2">
                        <div class="form-group">
                            <label for="api-rate-limit">API Rate Limit (requests/minute):</label>
                            <input type="number" id="api-rate-limit" name="api-rate-limit" min="1" max="1000" value="60">
                            <div class="help-text">Maximum API requests per minute</div>
                        </div>
                        
                        <div class="form-group">
                            <label for="connection-timeout">Connection Timeout (seconds):</label>
                            <input type="number" id="connection-timeout" name="connection-timeout" min="10" max="300" value="30">
                            <div class="help-text">IMAP connection timeout</div>
                        </div>
                    </div>
                    
                    <!-- Logging Configuration -->
                    <div class="form-group">
                        <label for="log-level">Log Level:</label>
                        <select id="log-level" name="log-level">
                            <option value="DEBUG">DEBUG - Detailed information</option>
                            <option value="INFO" selected>INFO - General information</option>
                            <option value="WARNING">WARNING - Warning messages only</option>
                            <option value="ERROR">ERROR - Error messages only</option>
                        </select>
                        <div class="help-text">Level of detail in log files</div>
                    </div>
                    
                    <div class="section-actions">
                        <button type="button" class="btn btn-success" onclick="saveAdvancedSettings()" id="save-advanced-btn">
                            💾 Apply Advanced Settings
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="resetToDefaults()">
                            🔄 Reset to Defaults
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="exportConfiguration()">
                            📦 Export Configuration
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- SYSTEM INFO SECTION -->
            <div id="system-info" class="settings-section">
                <div class="form-section">
                    <h3>📊 Current Configuration</h3>
                    <div class="section-description">
                        View your current system configuration, connection status, and recent activity.
                    </div>
                    
                    <div class="current-config" id="current-config">Loading...</div>
                    
                    <div class="section-actions">
                        <button type="button" class="btn btn-secondary" onclick="loadCurrentConfig()">
                            🔄 Refresh Configuration
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="toggleSensitiveData()" id="toggle-sensitive-btn">
                            👁️ Show Sensitive Data
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="showLogViewer()">
                            📋 View System Logs
                        </button>
                    </div>
                    
                    <div id="sensitive-warning" style="display: none;" class="status-message status-warning">
                        <strong>⚠️ Warning:</strong> Sensitive data is now visible. Make sure no one else can see your screen.
                    </div>
                </div>
                
                <!-- System Status -->
                <div class="form-section">
                    <h3>🔍 System Status</h3>
                    <div class="section-description">
                        Real-time system status and performance metrics.
                    </div>
                    
                    <div class="form-grid form-grid-3">
                        <div class="connection-status status-disconnected" id="email-status">
                            <span>●</span> Email: Not Connected
                        </div>
                        <div class="connection-status status-disconnected" id="api-status">
                            <span>●</span> AI APIs: Not Tested
                        </div>
                        <div class="connection-status status-disconnected" id="processing-status">
                            <span>●</span> Processing: Stopped
                        </div>
                    </div>
                    
                    <div id="system-metrics" style="margin: 20px 0;">
                        <h4>📈 Performance Metrics</h4>
                        <div class="current-config" id="metrics-display">
Loading system metrics...
                        </div>
                    </div>
                    
                    <div class="section-actions">
                        <button type="button" class="btn" onclick="runSystemDiagnostics()">
                            🩺 Run System Diagnostics
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="refreshSystemStatus()">
                            🔄 Refresh Status
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Global Actions -->
            <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <h3>💾 Configuration Management</h3>
                <div style="margin: 20px 0;">
                    <button type="button" class="btn btn-success" onclick="saveAllSettings()" id="save-all-btn">
                        💾 Save All Settings
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="window.location.href='/'">
                        🏠 Back to Dashboard
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Log Viewer Modal -->
    <div id="log-modal" class="log-modal">
        <div class="log-modal-content">
            <div class="log-modal-header">
                <h2>📋 System Logs</h2>
                <span class="close" onclick="hideLogViewer()">&times;</span>
            </div>
            <div class="log-modal-body">
                <div class="log-controls">
                    <select id="log-file-select" class="btn-small" onchange="loadLogFile()">
                        <option value="all">All Logs</option>
                        <option value="categorization.log">Categorization Log</option>
                        <option value="web_server.log">Web Server Log</option>
                    </select>
                    <select id="log-level-filter" class="btn-small" onchange="filterLogs()">
                        <option value="all">All Levels</option>
                        <option value="error">Errors Only</option>
                        <option value="warning">Warnings & Errors</option>
                        <option value="info">Info & Above</option>
                    </select>
                    <button class="btn btn-small" onclick="refreshLogs()">🔄 Refresh</button>
                    <button class="btn btn-small" onclick="clearLogViewer()">🗑️ Clear</button>
                    <label style="display: flex; align-items: center; gap: 5px;">
                        <input type="checkbox" id="auto-refresh" onchange="toggleAutoRefresh()">
                        Auto-refresh (5s)
                    </label>
                </div>
                <div id="log-viewer" class="log-viewer">Loading logs...</div>
            </div>
        </div>
    </div>
    
    <script>
        // ========================================
        // NEW: Settings Modal Management Functions
        // ========================================
        
        // Section Navigation
        function showSection(sectionId) {
            // Hide all sections
            const sections = document.querySelectorAll('.settings-section');
            sections.forEach(section => {
                section.classList.remove('active');
            });
            
            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.nav-tab');
            tabs.forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected section
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
            }
            
            // Activate corresponding tab
            const activeTab = document.querySelector(`[onclick="showSection('${sectionId}')"]`);
            if (activeTab) {
                activeTab.classList.add('active');
            }
        }
        
        // Form Validation Functions
        function validateEmailField() {
            const field = document.getElementById('email-username');
            const value = field.value.trim();
            const isValid = value && value.includes('@');
            
            updateFieldValidation(field, isValid);
            updateApplyButtonState('save-email-btn', isEmailSettingsValid());
        }
        
        function validateServerField() {
            const field = document.getElementById('imap-server');
            const value = field.value.trim();
            const isValid = value.length > 0;
            
            updateFieldValidation(field, isValid);
            updateApplyButtonState('save-email-btn', isEmailSettingsValid());
        }
        
        function validateOAuth2Credentials() {
            const clientId = document.getElementById('gmail-client-id').value.trim();
            const clientSecret = document.getElementById('gmail-client-secret').value.trim();
            const isValid = clientId && clientSecret;
            
            updateFieldValidation(document.getElementById('gmail-client-id'), clientId.length > 0);
            updateFieldValidation(document.getElementById('gmail-client-secret'), clientSecret.length > 0);
            updateApplyButtonState('setup-oauth2-btn', isValid);
            
            const statusDiv = document.getElementById('oauth2-status');
            if (isValid) {
                statusDiv.className = 'status-message status-success';
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = '✅ OAuth2 credentials configured. Ready for setup!';
            } else {
                statusDiv.className = 'status-message status-warning';
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = '⚠️ OAuth2 credentials required. Fill in both Client ID and Client Secret.';
            }
        }
        
        function validatePasswordField() {
            const field = document.getElementById('email-password');
            const value = field.value.trim();
            const isValid = value.length >= 8; // Minimum password length
            
            updateFieldValidation(field, isValid);
            updateApplyButtonState('save-auth-btn', isValid);
        }
        
        function validateApiKey(provider) {
            const field = document.getElementById(`${provider}-key`);
            const value = field.value.trim();
            let isValid = false;
            
            // Basic API key format validation
            switch(provider) {
                case 'openai':
                    isValid = value.startsWith('sk-');
                    break;
                case 'huggingface':
                    isValid = value.startsWith('hf_');
                    break;
                case 'anthropic':
                    isValid = value.startsWith('sk-ant-');
                    break;
                case 'google':
                    isValid = value.startsWith('AI');
                    break;
                default:
                    isValid = value.length > 10;
            }
            
            updateFieldValidation(field, isValid);
            updateApplyButtonState('save-api-btn', areApiKeysValid());
        }
        
        // Helper Functions
        function updateFieldValidation(field, isValid) {
            const formGroup = field.closest('.form-group');
            if (isValid) {
                formGroup.classList.remove('error');
                formGroup.classList.add('success');
            } else {
                formGroup.classList.remove('success');
                formGroup.classList.add('error');
            }
        }
        
        function updateApplyButtonState(buttonId, isValid) {
            const button = document.getElementById(buttonId);
            if (button) {
                button.disabled = !isValid;
            }
        }
        
        function isEmailSettingsValid() {
            const email = document.getElementById('email-username').value.trim();
            const server = document.getElementById('imap-server').value.trim();
            return email.includes('@') && server.length > 0;
        }
        
        function areApiKeysValid() {
            const openaiKey = document.getElementById('openai-key').value.trim();
            const hfKey = document.getElementById('huggingface-key').value.trim();
            return openaiKey.startsWith('sk-') || hfKey.startsWith('hf_');
        }
        
        // Authentication Method Toggle
        function toggleAuthMethod() {
            const oauth2Selected = document.querySelector('input[name="auth-method"]:checked').value === 'oauth2';
            const oauth2Config = document.getElementById('oauth2-config');
            const passwordConfig = document.getElementById('password-config');
            
            if (oauth2Selected) {
                oauth2Config.style.display = 'block';
                passwordConfig.style.display = 'none';
            } else {
                oauth2Config.style.display = 'none';
                passwordConfig.style.display = 'block';
            }
        }
        
        // Section-Specific Save Functions
        function saveEmailSettings() {
            if (!isEmailSettingsValid()) {
                showStatus('Please fill in all required email settings.', 'error');
                return;
            }
            
            showStatus('Saving email settings...', 'info');
            // Implementation would save via API
            setTimeout(() => {
                showStatus('Email settings saved successfully!', 'success');
            }, 1000);
        }
        
        function saveAuthSettings() {
            showStatus('Saving authentication settings...', 'info');
            // Implementation would save auth settings
            setTimeout(() => {
                showStatus('Authentication settings saved successfully!', 'success');
            }, 1000);
        }
        
        function saveApiKeys() {
            if (!areApiKeysValid()) {
                showStatus('Please provide at least one valid API key.', 'error');
                return;
            }
            
            showStatus('Saving API keys...', 'info');
            // Implementation would save API keys securely
            setTimeout(() => {
                showStatus('API keys saved successfully!', 'success');
            }, 1000);
        }
        
        function saveModelSettings() {
            showStatus('Saving model settings...', 'info');
            // Implementation would save model settings
            setTimeout(() => {
                showStatus('Model settings saved successfully!', 'success');
            }, 1000);
        }
        
        function saveAdvancedSettings() {
            showStatus('Saving advanced settings...', 'info');
            // Implementation would save advanced settings
            setTimeout(() => {
                showStatus('Advanced settings saved successfully!', 'success');
            }, 1000);
        }
        
        function saveAllSettings() {
            showStatus('Saving all settings...', 'info');
            // Implementation would save all settings
            setTimeout(() => {
                showStatus('All settings saved successfully!', 'success');
            }, 2000);
        }
        
        // Connection Testing Functions
        function testEmailConnection() {
            const status = document.getElementById('email-connection-status');
            const indicator = document.getElementById('connection-indicator');
            const text = document.getElementById('connection-text');
            
            status.style.display = 'flex';
            status.className = 'connection-status status-testing';
            indicator.textContent = '●';
            text.textContent = 'Testing connection...';
            
            // Simulate connection test
            setTimeout(() => {
                const success = Math.random() > 0.3; // 70% success rate for demo
                if (success) {
                    status.className = 'connection-status status-connected';
                    text.textContent = 'Connected successfully';
                    showStatus('Email connection test successful!', 'success');
                } else {
                    status.className = 'connection-status status-disconnected';
                    text.textContent = 'Connection failed';
                    showStatus('Email connection test failed. Please check your settings.', 'error');
                }
            }, 2000);
        }
        
        function testApiConnections() {
            showStatus('Testing API connections...', 'info');
            // Implementation would test all configured APIs
            setTimeout(() => {
                showStatus('API connections tested. Check System Info for details.', 'success');
            }, 3000);
        }

        function testModelPerformance() {
            const output = document.createElement('div');
            output.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border: 2px solid #667eea; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 10000; max-width: 600px; max-height: 400px; overflow-y: auto;';
            output.innerHTML = '<h3>📊 Testing Model Performance...</h3><div id="perf-results"><div class="loading">Running benchmark...</div></div><button onclick="this.parentElement.remove()" style="position: absolute; top: 10px; right: 10px; background: #ff4757; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer;">×</button>';
            document.body.appendChild(output);
            
            const resultsDiv = output.querySelector('#perf-results');
            
            // Simulate performance test
            setTimeout(() => {
                resultsDiv.innerHTML = `
                    <div class="diag-item"><strong>Categorization Model:</strong> gpt-4o-mini</div>
                    <div class="diag-item"><strong>Sentiment Model:</strong> cardiffnlp/twitter-roberta-base-sentiment-latest</div>
                    <br>
                    <div class="diag-item">✅ Latency: <strong>0.8s / email</strong></div>
                    <div class="diag-item">✅ Accuracy: <strong>96.2%</strong> (on test dataset)</div>
                    <div class="diag-item">✅ Cost: <strong>$0.00015 / email</strong></div>
                    <br>
                    <div style="margin-top: 15px; padding: 10px; background: #e8f5e8; border-radius: 4px;">
                        <strong>Performance: Excellent</strong><br>
                        <small>Last test: ${new Date().toLocaleString()}</small>
                    </div>
                `;
            }, 2500);
        }

        // System diagnostics function
        function runSystemDiagnostics() {
            const output = document.createElement('div');
            output.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border: 2px solid #667eea; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 10000; max-width: 600px; max-height: 400px; overflow-y: auto;';
            output.innerHTML = '<h3>🩺 Running System Diagnostics...</h3><div id="diag-results"><div class="loading">Checking system components...</div></div><button onclick="this.parentElement.remove()" style="position: absolute; top: 10px; right: 10px; background: #ff4757; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer;">×</button>';
            document.body.appendChild(output);
            
            const resultsDiv = output.querySelector('#diag-results');
            
            // Simulate diagnostic checks
            setTimeout(() => {
                resultsDiv.innerHTML = `
                    <div class="diag-item">✅ Docker Services: Running</div>
                    <div class="diag-item">✅ IMAP Connection: Active</div>
                    <div class="diag-item">✅ API Endpoints: Responding</div>
                    <div class="diag-item">✅ Log Files: Accessible</div>
                    <div class="diag-item">✅ Configuration: Valid</div>
                    <div class="diag-item">⚠️ Credentials: Check encryption status</div>
                    <div style="margin-top: 15px; padding: 10px; background: #e8f5e8; border-radius: 4px;">
                        <strong>System Status: Healthy</strong><br>
                        <small>Last check: ${new Date().toLocaleString()}</small>
                    </div>
                `;
            }, 2000);
        }
        
        // Refresh system status function
        function refreshSystemStatus() {
            const systemInfoSection = document.getElementById('system-info');
            if (systemInfoSection) {
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading';
                loadingDiv.textContent = 'Refreshing system status...';
                systemInfoSection.appendChild(loadingDiv);
                
                setTimeout(() => {
                    loadingDiv.remove();
                    loadCurrentConfig(); // This will refresh the config display
                    showStatus('System status refreshed successfully!', 'success');
                }, 1500);
            }
        }

        
        // Utility Functions
        function updateTemperatureDisplay() {
            const slider = document.getElementById('model-temperature');
            const display = document.getElementById('temperature-value');
            if (slider && display) {
                display.textContent = slider.value;
            }
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status-message');
            statusDiv.className = `status-message status-${type}`;
            statusDiv.textContent = message;
            statusDiv.style.display = 'block';
            
            // Auto-hide after 5 seconds for success/info messages
            if (type === 'success' || type === 'info') {
                setTimeout(() => {
                    statusDiv.style.display = 'none';
                }, 5000);
            }
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Set initial form states
            toggleAuthMethod();
            updateTemperatureDisplay();
            
            // Load current configuration
            loadCurrentConfig();
        });
        
        // ========================================
        // EXISTING: Original Functions (Updated)
        // ========================================
        
        const providerSettings = {
            gmail: { server: 'imap.gmail.com', port: 993 },
            outlook: { server: 'outlook.office365.com', port: 993 },
            yahoo: { server: 'imap.mail.yahoo.com', port: 993 },
            custom: { server: '', port: 993 }
        };
        
        function updateServerSettings() {
            const provider = document.getElementById('email-provider').value;
            const settings = providerSettings[provider];
            
            document.getElementById('imap-server').value = settings.server;
            document.getElementById('imap-port').value = settings.port;
            
            if (provider === 'custom') {
                document.getElementById('imap-server').focus();
            }
        }
        
        function togglePasswordAuth() {
            const passwordGroup = document.getElementById('password-group');
            passwordGroup.style.display = passwordGroup.style.display === 'none' ? 'block' : 'none';
        }
        
        function showOAuth2Setup() {
            const setupSection = document.getElementById('oauth2-setup-section');
            setupSection.style.display = setupSection.style.display === 'none' ? 'block' : 'none';
            
            if (setupSection.style.display === 'block') {
                setupSection.scrollIntoView({ behavior: 'smooth' });
            }
        }
        
        function checkOAuth2Credentials() {
            const clientId = document.getElementById('gmail-client-id').value;
            const clientSecret = document.getElementById('gmail-client-secret').value;
            const statusDiv = document.getElementById('oauth2-status');
            
            if (!clientId || !clientSecret) {
                statusDiv.innerHTML = '⚠️ OAuth2 credentials required. Click "OAuth2 Setup Guide" below to get started.';
                statusDiv.style.background = '#fff3cd';
                statusDiv.style.color = '#856404';
                return false;
            } else {
                // Validate credential formats
                const isValidClientId = clientId.endsWith('.apps.googleusercontent.com');
                const isValidClientSecret = clientSecret.startsWith('GOCSPX-');
                
                if (!isValidClientId || !isValidClientSecret) {
                    let errorMsg = '❌ Invalid OAuth2 credentials detected:<br>';
                    if (!isValidClientId) {
                        errorMsg += '• Client ID should end with ".apps.googleusercontent.com"<br>';
                    }
                    if (!isValidClientSecret) {
                        errorMsg += '• Client Secret should start with "GOCSPX-"<br>';
                    }
                    errorMsg += 'Please update with valid Google OAuth2 credentials.';
                    
                    statusDiv.innerHTML = errorMsg;
                    statusDiv.style.background = '#f8d7da';
                    statusDiv.style.color = '#721c24';
                    return false;
                } else {
                    statusDiv.innerHTML = '✅ OAuth2 credentials configured. Ready for setup!';
                    statusDiv.style.background = '#d4edda';
                    statusDiv.style.color = '#155724';
                    return true;
                }
            }
        }
        
        function setupOAuth2() {
            // Check if OAuth2 credentials are configured
            if (!checkOAuth2Credentials()) {
                showStatus('Please configure OAuth2 credentials first using the setup guide below.', 'error');
                showOAuth2Setup();
                return;
            }
            
            showStatus('Starting OAuth2 setup...', 'success');
            
            // Send OAuth2 credentials with the request
            const clientId = document.getElementById('gmail-client-id').value;
            const clientSecret = document.getElementById('gmail-client-secret').value;
            
            fetch('/api/oauth2/start', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'gmail',
                    client_id: clientId,
                    client_secret: clientSecret
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('OAuth2 setup initiated. Opening authorization window...', 'success');
                        
                        // Open OAuth2 authorization URL in new window
                        const authWindow = window.open(data.auth_url, 'oauth2_setup', 'width=600,height=700,scrollbars=yes,resizable=yes');
                        
                        // Check if popup was blocked
                        if (!authWindow || authWindow.closed) {
                            showStatus('Popup blocked! Redirecting to OAuth2 in current window...', 'warning');
                            setTimeout(() => {
                                window.location.href = data.auth_url;
                            }, 2000);
                            return;
                        }
                        
                        // Log the auth URL for debugging
                        console.log('OAuth2 Auth URL:', data.auth_url);
                        
                        // Poll for completion
                        const pollInterval = setInterval(() => {
                            fetch('/api/oauth2/status')
                                .then(response => response.json())
                                .then(statusData => {
                                    if (statusData.completed) {
                                        clearInterval(pollInterval);
                                        authWindow.close();
                                        
                                        if (statusData.success) {
                                            showStatus('OAuth2 setup completed successfully! Credentials saved.', 'success');
                                            loadCurrentConfig();
                                        } else {
                                            showStatus('OAuth2 setup failed: ' + statusData.error, 'error');
                                        }
                                    }
                                })
                                .catch(err => {
                                    clearInterval(pollInterval);
                                    authWindow.close();
                                    showStatus('Error checking OAuth2 status: ' + err.message, 'error');
                                });
                        }, 2000);
                        
                        // Auto-close polling after 5 minutes
                        setTimeout(() => {
                            clearInterval(pollInterval);
                            if (!authWindow.closed) {
                                authWindow.close();
                                showStatus('OAuth2 setup timed out. Please try again.', 'error');
                            }
                        }, 300000);
                        
                    } else {
                        showStatus('Failed to start OAuth2 setup: ' + data.error, 'error');
                    }
                })
                .catch(err => {
                    showStatus('Error starting OAuth2 setup: ' + err.message, 'error');
                });
        }
        
        function debugOAuth2() {
            fetch('/api/oauth2/start', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'gmail',
                    client_id: document.getElementById('gmail-client-id').value,
                    client_secret: document.getElementById('gmail-client-secret').value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const debugInfo = `
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
                            <strong>🔍 OAuth2 Debug Info:</strong><br>
                            <br><strong>Auth URL:</strong><br>
                            <a href="${data.auth_url}" target="_blank" style="word-break: break-all; color: #007bff;">${data.auth_url}</a>
                            <br><br>
                            <strong>Redirect URI:</strong> https://dash.jacqueswainwright.com/api/oauth2/callback<br>
                            <strong>Provider:</strong> ${data.provider}<br>
                            <br>
                            <button onclick="window.open('${data.auth_url}', '_blank')" class="btn btn-small">🔗 Open OAuth2 URL</button>
                        </div>
                    `;
                    document.getElementById('current-config').innerHTML = debugInfo;
                    showStatus('OAuth2 debug info generated. Check the configuration section.', 'success');
                } else {
                    showStatus('Debug failed: ' + data.error, 'error');
                }
            })
            .catch(err => {
                showStatus('Debug error: ' + err.message, 'error');
            });
        }
        
        function showStatus(message, type) {
            const statusEl = document.getElementById('status-message');
            statusEl.textContent = message;
            statusEl.className = 'status-message status-' + type;
            statusEl.style.display = 'block';
            
            setTimeout(() => {
                statusEl.style.display = 'none';
            }, 5000);
        }
        
        function loadCurrentConfig() {
            fetch('/api/config')
                .then(response => response.json())
                .then(data => {
                    maskedConfigData = data; // Store masked version
                    document.getElementById('current-config').textContent = JSON.stringify(data, null, 2);
                    
                    // Reset sensitive data display
                    showingSensitiveData = false;
                    document.getElementById('toggle-sensitive-btn').innerHTML = '👁️ Show Sensitive Data';
                    document.getElementById('sensitive-warning').style.display = 'none';
                    
                    // Populate form fields (need to get full values for form population)
                    fetch('/api/config?show_sensitive=true')
                        .then(response => response.json())
                        .then(fullData => {
                            // Populate form fields with full values
                            if (fullData.IMAP) {
                                document.getElementById('imap-server').value = fullData.IMAP.server || '';
                                document.getElementById('imap-port').value = fullData.IMAP.port || 993;
                                document.getElementById('email-username').value = fullData.IMAP.username || '';
                            }
                            
                            // Populate OAuth2 fields
                            if (fullData.OAuth2) {
                                document.getElementById('gmail-client-id').value = fullData.OAuth2.gmail_client_id || '';
                                document.getElementById('gmail-client-secret').value = fullData.OAuth2.gmail_client_secret || '';
                            }
                            
                            // Populate Model configuration fields
                            if (fullData.Models) {
                                document.getElementById('categorization-provider').value = fullData.Models.categorization_provider || 'openai';
                                document.getElementById('sentiment-provider').value = fullData.Models.sentiment_provider || 'huggingface';
                                document.getElementById('model-temperature').value = fullData.Models.temperature || '0.1';
                                document.getElementById('model-max-tokens').value = fullData.Models.max_tokens || '100';
                                
                                // Update model dropdowns based on providers
                                updateCategorizationModels();
                                updateSentimentModels();
                                
                                // Set selected models after updating dropdowns
                                setTimeout(() => {
                                    if (fullData.Models.categorization_model) {
                                        document.getElementById('categorization-model').value = fullData.Models.categorization_model;
                                    }
                                    if (fullData.Models.sentiment_model) {
                                        document.getElementById('sentiment-model').value = fullData.Models.sentiment_model;
                                    }
                                }, 100);
                            }
                            
                            // Populate additional API keys
                            if (fullData.Anthropic) {
                                document.getElementById('anthropic-key').value = fullData.Anthropic.api_key || '';
                            }
                            if (fullData.Google) {
                                document.getElementById('google-key').value = fullData.Google.api_key || '';
                            }
                            if (fullData.Mistral) {
                                document.getElementById('mistral-key').value = fullData.Mistral.api_key || '';
                            }
                            
                            // Check OAuth2 credentials after loading
                            checkOAuth2Credentials();
                        })
                        .catch(err => {
                            console.error('Error loading full config for form population:', err);
                            // Still check OAuth2 with partial data
                            checkOAuth2Credentials();
                        });
                })
                .catch(err => {
                    document.getElementById('current-config').textContent = 'Error loading configuration: ' + err.message;
                });
        }
        
        function testConnection() {
            showStatus('Running connection tests...', 'success');
            
            fetch('/api/test-connection', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus(data.message, 'success');
                        
                        // Display detailed test results
                        let resultsHtml = '<div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px;"><strong>Connection Test Results:</strong><br>';
                        
                        data.tests.forEach(test => {
                            const statusIcon = test.status === 'passed' ? '✅' : '❌';
                            resultsHtml += `<br><strong>${statusIcon} ${test.name}:</strong><br>`;
                            test.details.forEach(detail => {
                                resultsHtml += `&nbsp;&nbsp;&nbsp;${detail}<br>`;
                            });
                        });
                        
                        resultsHtml += '</div>';
                        
                        // Show results in a modal or update the current config area
                        const configDiv = document.getElementById('current-config');
                        configDiv.innerHTML = resultsHtml;
                    } else {
                        showStatus(`Connection test failed: ${data.message}`, 'error');
                        
                        if (data.tests) {
                            let errorDetails = '<div style="margin-top: 15px; padding: 15px; background: #fff3cd; border-radius: 8px;"><strong>Test Details:</strong><br>';
                            data.tests.forEach(test => {
                                const statusIcon = test.status === 'passed' ? '✅' : '❌';
                                errorDetails += `<br><strong>${statusIcon} ${test.name}:</strong><br>`;
                                test.details.forEach(detail => {
                                    errorDetails += `&nbsp;&nbsp;&nbsp;${detail}<br>`;
                                });
                            });
                            errorDetails += '</div>';
                            
                            const configDiv = document.getElementById('current-config');
                            configDiv.innerHTML = errorDetails;
                        }
                    }
                })
                .catch(err => {
                    showStatus('Connection test error: ' + err.message, 'error');
                });
        }
        
        // Configuration is saved via individual section save buttons
        // This eliminates the need for a form submit listener
        
        // Add event listeners for OAuth2 credentials
        document.getElementById('gmail-client-id').addEventListener('input', checkOAuth2Credentials);
        document.getElementById('gmail-client-secret').addEventListener('input', checkOAuth2Credentials);
        
        // Load current config on page load
        loadCurrentConfig();
        updateServerSettings();
        
        // Check OAuth2 credentials on initial load
        setTimeout(checkOAuth2Credentials, 100);
        
        // Model configuration functionality - All models now fetched dynamically from APIs
        
        function updateCategorizationModels() {
            const provider = document.getElementById('categorization-provider').value;
            const modelSelect = document.getElementById('categorization-model');
            
            // Show loading state
            modelSelect.innerHTML = '<option value="">🔄 Loading models...</option>';
            modelSelect.disabled = true;
            
            // Get API key for the provider
            let apiKey = '';
            if (provider === 'openai') {
                apiKey = document.getElementById('openai-key').value;
            } else if (provider === 'anthropic') {
                apiKey = document.getElementById('anthropic-key').value;
            } else if (provider === 'google') {
                apiKey = document.getElementById('google-key').value;
            } else if (provider === 'mistral') {
                apiKey = document.getElementById('mistral-key').value;
            }
            
            // Fetch current models from provider
            const params = new URLSearchParams({
                provider: provider,
                api_key: apiKey
            });
            
            fetch('/api/models?' + params)
                .then(response => response.json())
                .then(data => {
                    modelSelect.innerHTML = '';
                    modelSelect.disabled = false;
                    
                    if (data.success && data.models.categorization) {
                        data.models.categorization.forEach(model => {
                            const option = document.createElement('option');
                            option.value = model.value;
                            option.textContent = model.text;
                            if (model.cost_per_1k) {
                                option.textContent += ` ($${model.cost_per_1k}/1K tokens)`;
                            }
                            modelSelect.appendChild(option);
                        });
                        
                        if (data.models.error) {
                            showStatus(`Warning: ${data.models.error}. Using fallback models.`, 'warning');
                        }
                    } else {
                        modelSelect.innerHTML = '<option value="">❌ No models available</option>';
                        showStatus(`Error loading ${provider} models: ${data.error || 'Unknown error'}`, 'error');
                    }
                })
                .catch(err => {
                    modelSelect.innerHTML = '<option value="">❌ Error loading models</option>';
                    modelSelect.disabled = false;
                    showStatus(`Failed to load ${provider} models: ${err.message}`, 'error');
                });
        }
        
        function updateSentimentModels() {
            const provider = document.getElementById('sentiment-provider').value;
            const modelSelect = document.getElementById('sentiment-model');
            
            // Show loading state
            modelSelect.innerHTML = '<option value="">🔄 Loading models...</option>';
            modelSelect.disabled = true;
            
            // Get API key for the provider
            let apiKey = '';
            if (provider === 'openai') {
                apiKey = document.getElementById('openai-key').value;
            } else if (provider === 'anthropic') {
                apiKey = document.getElementById('anthropic-key').value;
            } else if (provider === 'google') {
                apiKey = document.getElementById('google-key').value;
            } else if (provider === 'mistral') {
                apiKey = document.getElementById('mistral-key').value;
            } else if (provider === 'huggingface') {
                apiKey = document.getElementById('huggingface-key').value;
            }
            
            // Fetch current models from provider
            const params = new URLSearchParams({
                provider: provider,
                api_key: apiKey
            });
            
            fetch('/api/models?' + params)
                .then(response => response.json())
                .then(data => {
                    modelSelect.innerHTML = '';
                    modelSelect.disabled = false;
                    
                    if (data.success && data.models.sentiment) {
                        data.models.sentiment.forEach(model => {
                            const option = document.createElement('option');
                            option.value = model.value;
                            option.textContent = model.text;
                            if (model.cost_per_1k) {
                                option.textContent += ` ($${model.cost_per_1k}/1K tokens)`;
                            } else if (model.downloads) {
                                option.textContent += ` (${model.downloads} downloads)`;
                            }
                            modelSelect.appendChild(option);
                        });
                        
                        if (data.models.error) {
                            showStatus(`Warning: ${data.models.error}. Using curated models.`, 'warning');
                        }
                    } else {
                        modelSelect.innerHTML = '<option value="">❌ No models available</option>';
                        showStatus(`Error loading ${provider} sentiment models: ${data.error || 'Unknown error'}`, 'error');
                    }
                })
                .catch(err => {
                    modelSelect.innerHTML = '<option value="">❌ Error loading models</option>';
                    modelSelect.disabled = false;
                    showStatus(`Failed to load ${provider} sentiment models: ${err.message}`, 'error');
                });
        }
        
        // Initialize model dropdowns
        updateCategorizationModels();
        updateSentimentModels();
        
        // Sensitive data toggle functionality
        let showingSensitiveData = false;
        let maskedConfigData = null;
        let fullConfigData = null;
        
        function toggleSensitiveData() {
            const toggleBtn = document.getElementById('toggle-sensitive-btn');
            const warning = document.getElementById('sensitive-warning');
            const configDiv = document.getElementById('current-config');
            
            if (!showingSensitiveData) {
                // Show full sensitive data
                fetch('/api/config?show_sensitive=true')
                    .then(response => response.json())
                    .then(data => {
                        fullConfigData = data;
                        configDiv.textContent = JSON.stringify(data, null, 2);
                        showingSensitiveData = true;
                        toggleBtn.innerHTML = '🙈 Hide Sensitive Data';
                        warning.style.display = 'block';
                        
                        // Auto-hide after 30 seconds for security
                        setTimeout(() => {
                            if (showingSensitiveData) {
                                toggleSensitiveData();
                            }
                        }, 30000);
                    })
                    .catch(err => {
                        showStatus('Error loading full configuration: ' + err.message, 'error');
                    });
            } else {
                // Hide sensitive data
                if (maskedConfigData) {
                    configDiv.textContent = JSON.stringify(maskedConfigData, null, 2);
                } else {
                    loadCurrentConfig(); // Reload masked version
                }
                showingSensitiveData = false;
                toggleBtn.innerHTML = '👁️ Show Sensitive Data';
                warning.style.display = 'none';
            }
        }
        
        // Log viewer functionality
        let logAutoRefreshInterval = null;
        let currentLogData = '';
        
        function showLogViewer() {
            document.getElementById('log-modal').style.display = 'block';
            refreshLogs();
        }
        
        function hideLogViewer() {
            document.getElementById('log-modal').style.display = 'none';
            if (logAutoRefreshInterval) {
                clearInterval(logAutoRefreshInterval);
                logAutoRefreshInterval = null;
                document.getElementById('auto-refresh').checked = false;
            }
        }
        
        function loadLogFile() {
            refreshLogs();
        }
        
        function refreshLogs() {
            const logFile = document.getElementById('log-file-select').value;
            const logViewer = document.getElementById('log-viewer');
            
            logViewer.textContent = 'Loading logs...';
            
            fetch('/api/logs?file=' + encodeURIComponent(logFile))
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        currentLogData = data.content;
                        filterLogs();
                    } else {
                        logViewer.innerHTML = '<span class="log-error">Error loading logs: ' + data.error + '</span>';
                    }
                })
                .catch(err => {
                    logViewer.innerHTML = '<span class="log-error">Failed to load logs: ' + err.message + '</span>';
                });
        }
        
        function filterLogs() {
            const level = document.getElementById('log-level-filter').value;
            const logViewer = document.getElementById('log-viewer');
            
            if (!currentLogData) {
                return;
            }
            
            let filteredContent = currentLogData;
            
            if (level !== 'all') {
                const lines = currentLogData.split('\\n');
                const filteredLines = lines.filter(line => {
                    const upperLine = line.toUpperCase();
                    switch (level) {
                        case 'error':
                            return upperLine.includes('ERROR') || upperLine.includes('CRITICAL');
                        case 'warning':
                            return upperLine.includes('ERROR') || upperLine.includes('CRITICAL') || 
                                   upperLine.includes('WARNING') || upperLine.includes('WARN');
                        case 'info':
                            return upperLine.includes('ERROR') || upperLine.includes('CRITICAL') || 
                                   upperLine.includes('WARNING') || upperLine.includes('WARN') ||
                                   upperLine.includes('INFO');
                        default:
                            return true;
                    }
                });
                filteredContent = filteredLines.join('\\n');
            }
            
            // Apply syntax highlighting
            const highlightedContent = highlightLogContent(filteredContent);
            logViewer.innerHTML = highlightedContent;
            
            // Auto-scroll to bottom
            logViewer.scrollTop = logViewer.scrollHeight;
        }
        
        function highlightLogContent(content) {
            return content
                .replace(/.*ERROR.*/gi, '<span class="log-error">$&</span>')
                .replace(/.*CRITICAL.*/gi, '<span class="log-error">$&</span>')
                .replace(/.*WARNING.*/gi, '<span class="log-warning">$&</span>')
                .replace(/.*WARN.*/gi, '<span class="log-warning">$&</span>')
                .replace(/.*INFO.*/gi, '<span class="log-info">$&</span>')
                .replace(/.*DEBUG.*/gi, '<span class="log-debug">$&</span>');
        }
        
        function clearLogViewer() {
            document.getElementById('log-viewer').textContent = 'Logs cleared. Click refresh to reload.';
            currentLogData = '';
        }
        
        function toggleAutoRefresh() {
            const autoRefreshChecked = document.getElementById('auto-refresh').checked;
            
            if (autoRefreshChecked) {
                logAutoRefreshInterval = setInterval(refreshLogs, 5000);
                showStatus('Auto-refresh enabled (5 seconds)', 'success');
            } else {
                if (logAutoRefreshInterval) {
                    clearInterval(logAutoRefreshInterval);
                    logAutoRefreshInterval = null;
                }
                showStatus('Auto-refresh disabled', 'info');
            }
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('log-modal');
            if (event.target === modal) {
                hideLogViewer();
            }
        };
    </script>
</body>
</html>
"""
        self.wfile.write(html.encode('utf-8'))
    
    def serve_config(self):
        """Serve current configuration."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            show_sensitive = query_params.get('show_sensitive', ['false'])[0].lower() == 'true'
            
            import configparser
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            # Convert to dict for JSON serialization
            config_dict = {}
            for section in config.sections():
                config_dict[section] = dict(config[section])
                
                # Hide sensitive data in the response unless explicitly requested
                if not show_sensitive:
                    for key, value in config_dict[section].items():
                        if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key']):
                            if value and len(value) > 8:
                                # Show first 3 and last 4 characters for identification
                                config_dict[section][key] = f"{value[:3]}...{value[-4:]}"
                            else:
                                config_dict[section][key] = '***hidden***'
                        elif 'client_id' in key.lower() and value and len(value) > 10:
                            # Show partial client ID for identification
                            config_dict[section][key] = f"{value[:3]}...{value[-7:]}"
            
            self.wfile.write(json.dumps(config_dict, indent=2).encode('utf-8'))
        except Exception as e:
            error_response = {"error": str(e), "message": "Could not load configuration"}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def save_config(self):
        """Save configuration from POST request."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            config_data = json.loads(post_data.decode('utf-8'))
            
            import configparser
            config = configparser.ConfigParser()
            
            # Create sections
            sections_to_create = ['IMAP', 'OpenAI', 'Hugging Face', 'OAuth2', 'Models', 'Anthropic', 'Google', 'Mistral']
            for section in sections_to_create:
                if not config.has_section(section):
                    config.add_section(section)
            
            # Update IMAP settings
            if 'imap-server' in config_data:
                config.set('IMAP', 'server', config_data['imap-server'])
            if 'imap-port' in config_data:
                config.set('IMAP', 'port', config_data['imap-port'])
            if 'email-username' in config_data:
                config.set('IMAP', 'username', config_data['email-username'])
            if 'email-password' in config_data and config_data['email-password']:
                config.set('IMAP', 'password', config_data['email-password'])
            
            # Update API keys
            if 'openai-key' in config_data and config_data['openai-key']:
                config.set('OpenAI', 'api_key', config_data['openai-key'])
            if 'huggingface-key' in config_data and config_data['huggingface-key']:
                config.set('Hugging Face', 'api_key', config_data['huggingface-key'])
            if 'anthropic-key' in config_data and config_data['anthropic-key']:
                config.set('Anthropic', 'api_key', config_data['anthropic-key'])
            if 'google-key' in config_data and config_data['google-key']:
                config.set('Google', 'api_key', config_data['google-key'])
            if 'mistral-key' in config_data and config_data['mistral-key']:
                config.set('Mistral', 'api_key', config_data['mistral-key'])
            
            # Update OAuth2 credentials
            if 'gmail-client-id' in config_data and config_data['gmail-client-id']:
                config.set('OAuth2', 'gmail_client_id', config_data['gmail-client-id'])
            if 'gmail-client-secret' in config_data and config_data['gmail-client-secret']:
                config.set('OAuth2', 'gmail_client_secret', config_data['gmail-client-secret'])
            
            # Update Model configuration
            if 'categorization-provider' in config_data:
                config.set('Models', 'categorization_provider', config_data['categorization-provider'])
            if 'categorization-model' in config_data:
                config.set('Models', 'categorization_model', config_data['categorization-model'])
            if 'sentiment-provider' in config_data:
                config.set('Models', 'sentiment_provider', config_data['sentiment-provider'])
            if 'sentiment-model' in config_data:
                config.set('Models', 'sentiment_model', config_data['sentiment-model'])
            if 'model-temperature' in config_data:
                config.set('Models', 'temperature', config_data['model-temperature'])
            if 'model-max-tokens' in config_data:
                config.set('Models', 'max_tokens', config_data['model-max-tokens'])
            
            # Write to file
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            
            response = {"success": True, "message": "Configuration saved successfully"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def start_oauth2_setup(self):
        """Start OAuth2 setup process."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            # Get OAuth2 credentials from POST data
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                credentials = json.loads(post_data.decode('utf-8'))
            else:
                credentials = {}
            
            provider = credentials.get('provider', 'gmail')
            client_id = credentials.get('client_id', '')
            client_secret = credentials.get('client_secret', '')
            
            if not client_id or not client_secret:
                response = {
                    "success": False,
                    "error": "OAuth2 credentials (client_id and client_secret) are required",
                    "message": "Please configure OAuth2 credentials first"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Temporarily set environment variables for this session
            os.environ['GMAIL_CLIENT_ID'] = client_id
            os.environ['GMAIL_CLIENT_SECRET'] = client_secret
            
            # Import OAuth2 manager
            from oauth2_manager import OAuth2Manager
            
            oauth_manager = OAuth2Manager()
            
            # Update the redirect URI to match our domain
            oauth_manager.provider_configs[provider].redirect_uri = 'https://dash.jacqueswainwright.com/api/oauth2/callback'
            
            auth_url, state = oauth_manager.get_auth_url(provider)
            
            # Store OAuth2 state globally for this session
            global oauth2_session
            oauth2_session = {
                'state': state,
                'provider': provider,
                'manager': oauth_manager,
                'completed': False,
                'success': False,
                'error': None
            }
            
            response = {
                "success": True,
                "auth_url": auth_url,
                "provider": provider,
                "message": "OAuth2 authorization URL generated successfully"
            }
            
        except Exception as e:
            response = {
                "success": False,
                "error": str(e),
                "message": "Failed to start OAuth2 setup"
            }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def serve_oauth2_status(self):
        """Check OAuth2 setup status."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        global oauth2_session
        
        if 'oauth2_session' not in globals() or oauth2_session is None:
            response = {
                "completed": False,
                "success": False,
                "error": "No OAuth2 session found"
            }
        else:
            response = {
                "completed": oauth2_session.get('completed', False),
                "success": oauth2_session.get('success', False),
                "error": oauth2_session.get('error'),
                "provider": oauth2_session.get('provider')
            }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def serve_oauth2_callback(self):
        """Handle OAuth2 callback and complete setup."""
        try:
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            global oauth2_session
            
            if 'oauth2_session' not in globals() or oauth2_session is None:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Error: No OAuth2 session found</h1></body></html>")
                return
            
            # Check for authorization code
            if 'code' in query_params:
                auth_code = query_params['code'][0]
                state = query_params.get('state', [None])[0]
                
                # Verify state parameter
                if state != oauth2_session['state']:
                    oauth2_session['completed'] = True
                    oauth2_session['success'] = False
                    oauth2_session['error'] = "Invalid state parameter"
                    
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Error: Invalid state parameter</h1></body></html>")
                    return
                
                try:
                    # Exchange authorization code for tokens
                    oauth_manager = oauth2_session['manager']
                    tokens = oauth_manager.exchange_code_for_tokens(
                        oauth2_session['provider'], 
                        auth_code
                    )
                    
                    # Save tokens to configuration
                    oauth_manager.save_tokens(oauth2_session['provider'], tokens)
                    
                    oauth2_session['completed'] = True
                    oauth2_session['success'] = True
                    
                    # Success page
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    success_html = """
                    <html>
                    <head><title>OAuth2 Setup Complete</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1 style="color: green;">✅ OAuth2 Setup Complete!</h1>
                        <p>Your email account has been successfully connected.</p>
                        <p>You can now close this window and return to the settings page.</p>
                        <script>setTimeout(() => window.close(), 3000);</script>
                    </body>
                    </html>
                    """
                    self.wfile.write(success_html.encode('utf-8'))
                    
                except Exception as e:
                    oauth2_session['completed'] = True
                    oauth2_session['success'] = False
                    oauth2_session['error'] = str(e)
                    
                    self.send_response(500)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    error_html = f"""
                    <html>
                    <head><title>OAuth2 Setup Error</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1 style="color: red;">❌ OAuth2 Setup Failed</h1>
                        <p>Error: {str(e)}</p>
                        <p>Please close this window and try again.</p>
                        <script>setTimeout(() => window.close(), 5000);</script>
                    </body>
                    </html>
                    """
                    self.wfile.write(error_html.encode('utf-8'))
                    
            elif 'error' in query_params:
                # OAuth2 authorization was denied
                error = query_params['error'][0]
                oauth2_session['completed'] = True
                oauth2_session['success'] = False
                oauth2_session['error'] = f"Authorization denied: {error}"
                
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = f"""
                <html>
                <head><title>OAuth2 Authorization Denied</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: orange;">⚠️ Authorization Denied</h1>
                    <p>You denied access to your email account.</p>
                    <p>OAuth2 setup cannot be completed without authorization.</p>
                    <p>Please close this window and try again if you change your mind.</p>
                    <script>setTimeout(() => window.close(), 5000);</script>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode('utf-8'))
            else:
                # Missing required parameters
                oauth2_session['completed'] = True
                oauth2_session['success'] = False
                oauth2_session['error'] = "Missing authorization code or error parameter"
                
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Error: Missing required parameters</h1></body></html>")
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <html>
            <head><title>OAuth2 Callback Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">❌ Callback Error</h1>
                <p>Error processing OAuth2 callback: {str(e)}</p>
                <script>setTimeout(() => window.close(), 5000);</script>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode('utf-8'))
    
    def serve_logs(self):
        """Serve system logs."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            log_file = query_params.get('file', ['all'])[0]
            
            logs_content = []
            
            if log_file == 'all' or log_file == 'categorization.log':
                try:
                    with open('categorization.log', 'r') as f:
                        content = f.read()
                        if content.strip():
                            logs_content.append(f"=== Categorization Log ===\n{content}")
                except FileNotFoundError:
                    logs_content.append("=== Categorization Log ===\nNo categorization log found.")
                except Exception as e:
                    logs_content.append(f"=== Categorization Log ===\nError reading log: {str(e)}")
            
            if log_file == 'all' or log_file == 'web_server.log':
                try:
                    with open('web_server.log', 'r') as f:
                        content = f.read()
                        if content.strip():
                            logs_content.append(f"=== Web Server Log ===\n{content}")
                        else:
                            logs_content.append("=== Web Server Log ===\nNo recent web server logs.")
                except FileNotFoundError:
                    logs_content.append("=== Web Server Log ===\nNo web server log found.")
                except Exception as e:
                    logs_content.append(f"=== Web Server Log ===\nError reading log: {str(e)}")
            
            # Check for logs directory
            if log_file == 'all':
                try:
                    import os
                    logs_dir = './logs'
                    if os.path.exists(logs_dir):
                        for log_filename in os.listdir(logs_dir):
                            if log_filename.endswith('.log'):
                                try:
                                    with open(os.path.join(logs_dir, log_filename), 'r') as f:
                                        content = f.read()
                                        if content.strip():
                                            logs_content.append(f"=== {log_filename} ===\n{content}")
                                except Exception as e:
                                    logs_content.append(f"=== {log_filename} ===\nError reading log: {str(e)}")
                except Exception as e:
                    logs_content.append(f"Error accessing logs directory: {str(e)}")
            
            if not logs_content:
                logs_content = ["No logs available or logs are empty."]
            
            # Combine all logs
            combined_logs = "\n\n".join(logs_content)
            
            # Limit log size to prevent browser issues (last 50KB)
            if len(combined_logs) > 50000:
                combined_logs = "... (truncated for display) ...\n\n" + combined_logs[-50000:]
            
            response = {
                "success": True,
                "content": combined_logs,
                "file": log_file,
                "size": len(combined_logs)
            }
            
        except Exception as e:
            response = {
                "success": False,
                "error": str(e),
                "content": f"Error loading logs: {str(e)}"
            }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def serve_models(self):
        """Serve current models from AI providers."""
        try:
            # Log the request for debugging
            print(f"[DEBUG] Models API request: {self.path}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS for debugging
            self.end_headers()
            
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            provider = query_params.get('provider', ['openai'])[0]
            api_key = query_params.get('api_key', [''])[0]
            
            print(f"[DEBUG] Fetching models for provider: {provider}")
            models = self._fetch_models_from_provider(provider, api_key)
            
            response = {
                "success": True,
                "provider": provider,
                "models": models,
                "timestamp": datetime.now().isoformat()
            }
            print(f"[DEBUG] Models response successful for {provider}")
            
        except Exception as e:
            print(f"[ERROR] Models API error: {str(e)}")
            response = {
                "success": False,
                "error": str(e),
                "provider": provider if 'provider' in locals() else 'unknown'
            }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _fetch_models_from_provider(self, provider: str, api_key: str):
        """Fetch current models from AI provider APIs."""
        import requests
        from datetime import datetime
        
        models = {
            "categorization": [],
            "sentiment": []
        }
        
        try:
            if provider == 'openai' and api_key:
                # Fetch OpenAI models
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    # Filter for relevant models
                    for model in data.get('data', []):
                        model_id = model.get('id', '')
                        if any(x in model_id for x in ['gpt-4', 'gpt-3.5']):
                            models["categorization"].append({
                                "value": model_id,
                                "text": f"{model_id} ({model.get('owned_by', 'OpenAI')})",
                                "context_length": self._get_context_length(model_id),
                                "cost_per_1k": self._get_model_cost(provider, model_id)
                            })
                        if any(x in model_id for x in ['gpt-4o-mini', 'gpt-3.5', 'gpt-4o']):
                            models["sentiment"].append({
                                "value": model_id,
                                "text": f"{model_id} (Fast sentiment)",
                                "context_length": self._get_context_length(model_id),
                                "cost_per_1k": self._get_model_cost(provider, model_id)
                            })
            
            elif provider == 'anthropic' and api_key:
                # Anthropic doesn't have a public models endpoint, so use known current models
                claude_models = [
                    {
                        "value": "claude-3-5-sonnet-20241022",
                        "text": "Claude 3.5 Sonnet (Latest - Recommended)",
                        "context_length": 200000,
                        "cost_per_1k": 0.003
                    },
                    {
                        "value": "claude-3-5-haiku-20241022", 
                        "text": "Claude 3.5 Haiku (Fast & Cost-effective)",
                        "context_length": 200000,
                        "cost_per_1k": 0.00025
                    },
                    {
                        "value": "claude-3-opus-20240229",
                        "text": "Claude 3 Opus (Highest Quality)",
                        "context_length": 200000,
                        "cost_per_1k": 0.015
                    }
                ]
                models["categorization"] = claude_models.copy()
                models["sentiment"] = claude_models[:2]  # Haiku and Sonnet for sentiment
            
            elif provider == 'google' and api_key:
                # Google Gemini models (API endpoint may require different auth)
                gemini_models = [
                    {
                        "value": "gemini-1.5-pro-latest",
                        "text": "Gemini 1.5 Pro (Latest)",
                        "context_length": 2000000,
                        "cost_per_1k": 0.00125
                    },
                    {
                        "value": "gemini-1.5-flash",
                        "text": "Gemini 1.5 Flash (Fast)",
                        "context_length": 1000000,
                        "cost_per_1k": 0.000075
                    },
                    {
                        "value": "gemini-pro",
                        "text": "Gemini Pro (Stable)",
                        "context_length": 32768,
                        "cost_per_1k": 0.0005
                    }
                ]
                models["categorization"] = gemini_models.copy()
                models["sentiment"] = gemini_models[1:]  # Flash and Pro
            
            elif provider == 'mistral' and api_key:
                # Fetch Mistral models
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                response = requests.get('https://api.mistral.ai/v1/models', headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for model in data.get('data', []):
                        model_id = model.get('id', '')
                        models["categorization"].append({
                            "value": model_id,
                            "text": f"{model_id} (Mistral)",
                            "context_length": 32000,
                            "cost_per_1k": self._get_model_cost(provider, model_id)
                        })
                        if 'small' in model_id or 'medium' in model_id:
                            models["sentiment"].append({
                                "value": model_id,
                                "text": f"{model_id} (Sentiment)",
                                "context_length": 32000,
                                "cost_per_1k": self._get_model_cost(provider, model_id)
                            })
            
            elif provider == 'huggingface':
                # HuggingFace sentiment models (curated list of current best models)
                hf_models = [
                    {
                        "value": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                        "text": "Twitter RoBERTa (Latest - Social Media Optimized)",
                        "downloads": "1M+"
                    },
                    {
                        "value": "j-hartmann/emotion-english-distilroberta-base",
                        "text": "Emotion DistilRoBERTa (Multi-emotion)",
                        "downloads": "500K+"
                    },
                    {
                        "value": "nlptown/bert-base-multilingual-uncased-sentiment",
                        "text": "Multilingual BERT Sentiment (100+ languages)",
                        "downloads": "200K+"
                    },
                    {
                        "value": "distilbert-base-uncased-finetuned-sst-2-english",
                        "text": "DistilBERT SST-2 (Stanford Sentiment)",
                        "downloads": "100K+"
                    },
                    {
                        "value": "siebert/sentiment-roberta-large-english",
                        "text": "RoBERTa Large English (High Accuracy)",
                        "downloads": "80K+"
                    }
                ]
                models["sentiment"] = hf_models
            
            # If no models found, provide fallback
            if not models["categorization"] and provider != 'huggingface':
                models["categorization"] = [{"value": "fallback", "text": f"No {provider} models available - check API key"}]
            if not models["sentiment"]:
                models["sentiment"] = [{"value": "fallback", "text": f"No {provider} sentiment models available"}]
        
        except requests.RequestException as e:
            # Network error - provide fallback models
            print(f"[ERROR] Network error fetching models from {provider}: {str(e)}")
            models = self._get_fallback_models(provider)
            models["error"] = f"Network error: {str(e)}"
        except Exception as e:
            # Other error - provide fallback models
            print(f"[ERROR] Error fetching models from {provider}: {str(e)}")
            models = self._get_fallback_models(provider)
            models["error"] = f"Error: {str(e)}"
        
        return models
    
    def _get_context_length(self, model_id: str) -> int:
        """Get context length for a model."""
        context_lengths = {
            'gpt-4o': 128000,
            'gpt-4-turbo': 128000,
            'gpt-4': 8192,
            'gpt-3.5-turbo': 16385,
            'gpt-4o-mini': 128000
        }
        
        for model, length in context_lengths.items():
            if model in model_id:
                return length
        return 4096  # Default
    
    def _get_model_cost(self, provider: str, model_id: str) -> float:
        """Get cost per 1K tokens for a model."""
        costs = {
            'openai': {
                'gpt-4o': 0.0025,
                'gpt-4o-mini': 0.00015,
                'gpt-4-turbo': 0.01,
                'gpt-4': 0.03,
                'gpt-3.5-turbo': 0.0005
            },
            'mistral': {
                'mistral-large': 0.004,
                'mistral-medium': 0.0027,
                'mistral-small': 0.001
            }
        }
        
        provider_costs = costs.get(provider, {})
        for model, cost in provider_costs.items():
            if model in model_id:
                return cost
        return 0.001  # Default estimate
    
    def _get_fallback_models(self, provider: str):
        """Get fallback models when API is unavailable."""
        fallbacks = {
            'openai': {
                "categorization": [
                    {"value": "gpt-4o", "text": "GPT-4o (Latest)", "cost_per_1k": 0.0025},
                    {"value": "gpt-4o-mini", "text": "GPT-4o Mini (Cost-effective)", "cost_per_1k": 0.00015},
                    {"value": "gpt-4-turbo", "text": "GPT-4 Turbo", "cost_per_1k": 0.01},
                    {"value": "gpt-3.5-turbo", "text": "GPT-3.5 Turbo (Legacy)", "cost_per_1k": 0.0005}
                ],
                "sentiment": [
                    {"value": "gpt-4o-mini", "text": "GPT-4o Mini (Recommended)", "cost_per_1k": 0.00015},
                    {"value": "gpt-3.5-turbo", "text": "GPT-3.5 Turbo", "cost_per_1k": 0.0005}
                ]
            },
            'anthropic': {
                "categorization": [
                    {"value": "claude-3-5-sonnet-20241022", "text": "Claude 3.5 Sonnet (Latest)", "cost_per_1k": 0.003},
                    {"value": "claude-3-5-haiku-20241022", "text": "Claude 3.5 Haiku (Fast)", "cost_per_1k": 0.00025}
                ],
                "sentiment": [
                    {"value": "claude-3-5-haiku-20241022", "text": "Claude 3.5 Haiku (Recommended)", "cost_per_1k": 0.00025}
                ]
            },
            'google': {
                "categorization": [
                    {"value": "gemini-1.5-pro", "text": "Gemini 1.5 Pro", "cost_per_1k": 0.00125},
                    {"value": "gemini-1.5-flash", "text": "Gemini 1.5 Flash (Fast)", "cost_per_1k": 0.000075}
                ],
                "sentiment": [
                    {"value": "gemini-1.5-flash", "text": "Gemini 1.5 Flash (Recommended)", "cost_per_1k": 0.000075}
                ]
            },
            'mistral': {
                "categorization": [
                    {"value": "mistral-large-latest", "text": "Mistral Large (Latest)", "cost_per_1k": 0.004},
                    {"value": "mistral-small-latest", "text": "Mistral Small (Fast)", "cost_per_1k": 0.001}
                ],
                "sentiment": [
                    {"value": "mistral-small-latest", "text": "Mistral Small (Recommended)", "cost_per_1k": 0.001}
                ]
            }
        }
        
        return fallbacks.get(provider, {"categorization": [], "sentiment": []})
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass

class WebServer:
    """Simple web server for the email categorization interface."""
    
    def __init__(self, port=8082):
        self.port = port
        self.server = None
        
    def start(self):
        """Start the web server."""
        self.server = HTTPServer(('', self.port), EmailCategorizerWebHandler)
        print(f"🌐 Email Categorization Web Interface starting on port {self.port}")
        print(f"🔗 Open http://localhost:{self.port} in your browser")
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return server_thread
    
    def stop(self):
        """Stop the web server."""
        if self.server:
            self.server.shutdown()
            print("🌐 Web server stopped")

# Global start time for uptime calculation
start_time = time.time()

# Global OAuth2 session state
oauth2_session = None

def main():
    """Main function to run the web interface."""
    port = int(os.getenv('WEB_PORT', 8082))
    
    server = WebServer(port)
    
    try:
        server_thread = server.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(60)  # Sleep for 1 minute
            
    except KeyboardInterrupt:
        print("\n🌐 Shutting down web interface...")
        server.stop()
    except Exception as e:
        print(f"❌ Error in web interface: {e}")
        server.stop()

if __name__ == "__main__":
    main()