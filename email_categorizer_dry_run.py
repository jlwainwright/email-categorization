#!/usr/bin/env python3
"""
Email Categorization Dry Run Script
----------------------------------
This script connects to an IMAP mailbox, reads new emails, and shows what 
categorization would be applied WITHOUT actually moving any emails.
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
import random
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta

# Configuration constants
CONFIG_FILE = 'config.ini'

CATEGORIES = [
    "Client Communication",
    "Completed & Archived",
    "Follow-Up Required", 
    "General Inquiries",
    "Invoices & Payments",
    "Marketing & Promotions", 
    "Pending & To Be Actioned",
    "Personal & Non-Business",
    "Reports & Documents",
    "Spam & Unwanted",
    "System & Notifications",
    "Urgent & Time-Sensitive"
]

def load_config():
    """Load configuration from config.ini file and apply environment overrides"""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # Ensure required sections exist
    if not config.has_section('IMAP'):
        config['IMAP'] = {}
    if not config.has_section('Hugging Face'):
        config['Hugging Face'] = {}
    if not config.has_section('OpenAI'):
        config['OpenAI'] = {}

    # Environment variable overrides
    # IMAP
    server_env = os.getenv('IMAP_SERVER')
    if server_env:
        config['IMAP']['server'] = server_env
    port_env = os.getenv('IMAP_PORT')
    if port_env:
        config['IMAP']['port'] = port_env
    username_env = os.getenv('IMAP_USERNAME')
    if username_env:
        config['IMAP']['username'] = username_env
    password_env = os.getenv('IMAP_PASSWORD')
    if password_env:
        config['IMAP']['password'] = password_env

    # Hugging Face API key
    hf_key = os.getenv('HUGGINGFACE_API_KEY')
    if hf_key:
        config['Hugging Face']['api_key'] = hf_key

    # OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        config['OpenAI']['api_key'] = openai_key

    return config

def get_sentiment_analysis(text):
    """Get sentiment analysis from HuggingFace API"""
    config = load_config()
    api_key = config['Hugging Face']['api_key']
    
    # Truncate text to avoid API limits
    text = text[:1000] if len(text) > 1000 else text
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": text})
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            sentiment_scores = result[0]
            if isinstance(sentiment_scores, list) and len(sentiment_scores) > 0:
                return sentiment_scores[0]
        
        return {"label": "NEUTRAL", "score": 0.5}
        
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return {"label": "NEUTRAL", "score": 0.5}

def categorize_email_with_openai(email_content, sentiment):
    """Categorize email using OpenAI API"""
    config = load_config()
    api_key = config['OpenAI']['api_key']
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    You are an AI assistant that categorizes emails for a business. 
    
    Email Content:
    Subject: {email_content.get('subject', 'No subject')}
    From: {email_content.get('from', 'Unknown sender')}
    Body: {email_content.get('body', 'No body')[:500]}
    
    Sentiment Analysis: {sentiment.get('label', 'NEUTRAL')} (Score: {sentiment.get('score', 0.5)})
    
    Categories available:
    {', '.join(CATEGORIES)}
    
    Please categorize this email into ONE of the above categories. 
    Consider the sender, subject, content, and sentiment.
    
    Respond with ONLY the category name, nothing else.
    """
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an email categorization assistant. Respond with only the category name."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", 
                               headers=headers, json=data)
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            category = result['choices'][0]['message']['content'].strip()
            # Validate category
            if category in CATEGORIES:
                return category
            else:
                # Try to find a partial match
                for cat in CATEGORIES:
                    if cat.lower() in category.lower() or category.lower() in cat.lower():
                        return cat
        
        return "General Inquiries"  # Default fallback
        
    except Exception as e:
        print(f"Error in OpenAI categorization: {e}")
        return "General Inquiries"

def decode_header_value(header_value):
    """Decode email header values"""
    if header_value is None:
        return ""
    
    decoded_parts = email.header.decode_header(header_value)
    decoded_string = ""
    
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            if encoding:
                try:
                    decoded_string += part.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part.decode('utf-8', errors='ignore')
        else:
            decoded_string += str(part)
    
    return decoded_string

def extract_email_content(msg):
    """Extract content from email message"""
    content = {
        'subject': decode_header_value(msg.get('Subject', '')),
        'from': decode_header_value(msg.get('From', '')),
        'to': decode_header_value(msg.get('To', '')),
        'date': msg.get('Date', ''),
        'body': ''
    }
    
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True)
                    if isinstance(body, bytes):
                        content['body'] = body.decode('utf-8', errors='ignore')
                    else:
                        content['body'] = str(body)
                    break
                except Exception as e:
                    print(f"Error decoding email body: {e}")
                    content['body'] = "Error decoding email content"
    else:
        try:
            body = msg.get_payload(decode=True)
            if isinstance(body, bytes):
                content['body'] = body.decode('utf-8', errors='ignore')
            else:
                content['body'] = str(body)
        except Exception as e:
            print(f"Error decoding email body: {e}")
            content['body'] = "Error decoding email content"
    
    return content

def dry_run_categorization(email_filter='UNSEEN', max_emails=10):
    """Perform dry run categorization - show what would happen without moving emails
    
    Args:
        email_filter: 'UNSEEN' (unread), 'ALL' (all emails), 'RECENT' (recent), or custom IMAP search
        max_emails: Maximum number of emails to process
    """
    config = load_config()
    
    server = config['IMAP']['server']
    port = int(config['IMAP']['port'])
    username = config['IMAP']['username']
    password = config['IMAP']['password']
    
    try:
        print(f"🔗 Connecting to {server}:{port}...")
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(username, password)
        print(f"✅ Successfully logged in as {username}")
        
        # Select INBOX
        mail.select('INBOX')
        
        # Search for emails based on filter
        print(f"🔍 Searching for emails with filter: {email_filter}")
        result, data = mail.search(None, email_filter)
        
        if result != 'OK':
            print("❌ Error searching for emails")
            return
        
        email_ids = data[0].split()
        
        if not email_ids:
            print(f"📭 No emails found matching filter: {email_filter}")
            mail.logout()
            return
        
        # Limit number of emails to process
        if len(email_ids) > max_emails:
            email_ids = email_ids[-max_emails:]  # Get most recent emails
            print(f"📧 Found {len(data[0].split())} emails, processing most recent {max_emails}")
        else:
            print(f"📧 Found {len(email_ids)} email(s) matching filter")
        
        print("=" * 80)
        
        for i, email_id in enumerate(email_ids, 1):
            try:
                print(f"\n📨 Processing Email {i}/{len(email_ids)}")
                print("-" * 50)
                
                # Fetch email
                result, data = mail.fetch(email_id, '(RFC822)')
                if result != 'OK':
                    print(f"❌ Error fetching email {email_id}")
                    continue
                
                # Parse email
                msg = email.message_from_bytes(data[0][1])
                email_content = extract_email_content(msg)
                
                # Display email info
                print(f"📋 Subject: {email_content['subject'][:100]}...")
                print(f"👤 From: {email_content['from']}")
                print(f"📅 Date: {email_content['date']}")
                print(f"📝 Body Preview: {email_content['body'][:200]}...")
                
                # Get sentiment analysis
                print(f"\n🧠 Analyzing sentiment...")
                sentiment = get_sentiment_analysis(email_content['body'])
                print(f"😊 Sentiment: {sentiment['label']} (Score: {sentiment['score']:.2f})")
                
                # Categorize email
                print(f"\n🎯 Categorizing email...")
                category = categorize_email_with_openai(email_content, sentiment)
                print(f"📁 Category: {category}")
                
                print(f"\n🔍 DRY RUN: Email would be moved to folder: INBOX.{category}")
                
                # Add delay to avoid rate limiting
                if i < len(email_ids):
                    print("⏱️  Waiting 2 seconds...")
                    time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing email {email_id}: {e}")
                continue
        
        print("\n" + "=" * 80)
        print("✅ Dry run completed!")
        print("💡 No emails were actually moved. This was just a preview.")
        
        mail.logout()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    print("🚀 Starting Email Categorization Dry Run")
    print("=" * 80)
    
    # Parse command line arguments
    email_filter = 'UNSEEN'  # Default to unread emails
    max_emails = 5  # Default to 5 emails
    
    if len(sys.argv) > 1:
        filter_arg = sys.argv[1].upper()
        if filter_arg in ['ALL', 'UNSEEN', 'RECENT']:
            email_filter = filter_arg
        else:
            print(f"❌ Invalid filter: {sys.argv[1]}")
            print("📋 Available filters: ALL, UNSEEN, RECENT")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            max_emails = int(sys.argv[2])
        except ValueError:
            print(f"❌ Invalid max_emails: {sys.argv[2]} (must be a number)")
            sys.exit(1)
    
    print(f"📋 Filter: {email_filter} | Max emails: {max_emails}")
    print("💡 Usage: python3 email_categorizer_dry_run.py [ALL|UNSEEN|RECENT] [max_emails]")
    print("💡 Examples:")
    print("💡   python3 email_categorizer_dry_run.py ALL 10    # Process 10 most recent emails")
    print("💡   python3 email_categorizer_dry_run.py UNSEEN 5  # Process 5 unread emails")
    print("💡   python3 email_categorizer_dry_run.py RECENT    # Process 5 recent emails")
    print("=" * 80)
    
    dry_run_categorization(email_filter, max_emails)