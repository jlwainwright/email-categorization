#!/usr/bin/env python3
"""
Continuous Email Categorization Script
-------------------------------------
This script continuously monitors an IMAP mailbox, reads new emails, and categorizes them
into predefined folders using HuggingFace API for sentiment analysis and OpenAI for 
categorization.
"""

import imaplib
import email
import email.header
import os
import sys
import json
import requests
import configparser
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta

# Import all functions from the main script
from email_categorizer import (
    load_config, connect_to_mail_server, get_email_content, 
    analyze_sentiment, categorize_email, move_email_with_retry, CATEGORIES
)
from api_rate_limiter import rate_limiter
from api_monitor import api_monitor

def monitor_emails(config, check_interval=60):
    """Continuously monitor emails and process them as they arrive."""
    print(f"Starting continuous email monitoring (checking every {check_interval} seconds)...")
    
    cycle_count = 0
    last_report_time = datetime.now()
    
    while True:
        try:
            cycle_count += 1
            current_time = datetime.now()
            print(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for new emails... (Cycle {cycle_count})")
            
            mail = connect_to_mail_server(config)
            mail.select('INBOX')
            
            # Search for unread emails
            result, data = mail.search(None, 'UNSEEN')
            if result != 'OK':
                print("No emails found or error in search")
                mail.logout()
                time.sleep(check_interval)
                continue
            
            email_count = len(data[0].split())
            if email_count == 0:
                print("No new emails found")
            else:
                print(f"Found {email_count} new email(s)")
                
                for num in data[0].split():
                    try:
                        # Fetch the email
                        result, msg_data = mail.fetch(num, '(RFC822)')
                        if result != 'OK':
                            print(f"Error fetching email {num}")
                            continue
                        
                        # Parse the email
                        msg = email.message_from_bytes(msg_data[0][1])
                        email_data = get_email_content(msg)
                        
                        print(f"Processing email: {email_data['subject']}")
                        
                        # Analyze sentiment
                        sentiment = analyze_sentiment(email_data['content'], config)
                        print(f"Sentiment: {sentiment}")
                        
                        # Categorize email
                        category = categorize_email(email_data, sentiment, config)
                        print(f"Category: {category}")
                        
                        # Move email to appropriate folder
                        result, uid_data = mail.fetch(num, '(UID)')
                        if result != 'OK':
                            print(f"Error fetching UID for email {num}")
                            continue
                        
                        # Extract UID from response
                        uid = uid_data[0].decode().split()[2].rstrip(')')
                        
                        # Move the email with retry logic
                        if move_email_with_retry(mail, uid, category, config):
                            print(f"✅ Successfully moved email to {category}")
                            
                            # Enhanced logging
                            if email_data.get('has_html'):
                                print(f"   📧 HTML email processed")
                            if email_data.get('attachments'):
                                print(f"   📎 {len(email_data['attachments'])} attachment(s)")
                        else:
                            print(f"❌ Failed to move email to {category}")
                            
                    except Exception as e:
                        print(f"Error processing email: {e}")
            
            mail.logout()
            
            # Log usage statistics every hour
            if (current_time - last_report_time).total_seconds() >= 3600:  # 1 hour
                print("\n" + "="*50)
                print("HOURLY USAGE REPORT")
                print("="*50)
                rate_limiter.print_usage_report()
                api_monitor.print_alerts()
                api_monitor.log_usage()
                last_report_time = current_time
                print("="*50)
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            api_monitor.log_usage()  # Log usage even on errors
        
        print(f"Waiting {check_interval} seconds before next check...")
        time.sleep(check_interval)

if __name__ == "__main__":
    config = load_config()
    try:
        # Allow check interval to be specified as command line argument
        check_interval = int(sys.argv[1]) if len(sys.argv) > 1 else 60
        print("\n" + "🚀" * 20)
        print("STARTING CONTINUOUS EMAIL CATEGORIZATION")
        print("🚀" * 20)
        print(f"Check interval: {check_interval} seconds")
        print(f"Rate limiting: Enabled")
        print(f"Caching: Enabled")
        print(f"Monitoring: Enabled")
        print("🚀" * 20 + "\n")
        
        monitor_emails(config, check_interval)
    except KeyboardInterrupt:
        print("\n\n" + "🛑" * 20)
        print("EMAIL MONITORING STOPPED BY USER")
        print("🛑" * 20)
        
        # Final usage report
        print("\nFINAL USAGE REPORT:")
        rate_limiter.print_usage_report()
        api_monitor.log_usage()
        
        print("🛑" * 20)
    except Exception as e:
        print(f"Fatal error: {e}")
        api_monitor.log_usage()  # Log final usage
        sys.exit(1)
