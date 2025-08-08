#!/usr/bin/env python3
"""
Email Categorization Script
---------------------------
This script connects to an IMAP mailbox, reads new emails, and categorizes them
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
from credential_manager import load_config_secure
from api_rate_limiter import throttled_huggingface_request, throttled_openai_request, rate_limiter
from email_parser import get_enhanced_email_content
from email_providers import provider_manager, detect_email_provider
from batch_processor import process_emails_in_batches, batch_processor
import time
import random
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta

# Configuration constants
CONFIG_FILE = 'config.ini'

# Connection retry configuration
MAX_RETRY_ATTEMPTS = 3
BASE_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 60  # seconds
CONNECTION_TIMEOUT = 30  # seconds

CATEGORIES = [
    "Client Communication",
    "Client_Communication",
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
    """Load configuration securely (encrypted preferred, fallback to plaintext)."""
    try:
        # Try to load encrypted config first
        config = load_config_secure(CONFIG_FILE, 'config.encrypted')
        if config is None:
            print("Error: Failed to load configuration.")
            print("If you have a plaintext config, encrypt it with:")
            print("python3 credential_manager.py --encrypt")
            sys.exit(1)
        # Apply environment overrides
        if not config.has_section('IMAP'):
            config['IMAP'] = {}
        if not config.has_section('Hugging Face'):
            config['Hugging Face'] = {}
        if not config.has_section('OpenAI'):
            config['OpenAI'] = {}

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

        hf_key = os.getenv('HUGGINGFACE_API_KEY')
        if hf_key:
            config['Hugging Face']['api_key'] = hf_key
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            config['OpenAI']['api_key'] = openai_key

        return config
    except ImportError:
        # Fallback to plaintext if cryptography not available
        print("Warning: Cryptography library not available, using plaintext config")
        if not os.path.exists(CONFIG_FILE):
            print(f"Error: Config file {CONFIG_FILE} not found.")
            sys.exit(1)
        
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        # Apply environment overrides
        if not config.has_section('IMAP'):
            config['IMAP'] = {}
        if not config.has_section('Hugging Face'):
            config['Hugging Face'] = {}
        if not config.has_section('OpenAI'):
            config['OpenAI'] = {}

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

        hf_key = os.getenv('HUGGINGFACE_API_KEY')
        if hf_key:
            config['Hugging Face']['api_key'] = hf_key
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            config['OpenAI']['api_key'] = openai_key

        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

def connect_to_mail_server(config):
    """Connect to the mail server using the provided configuration with retry logic and provider support."""
    last_exception = None
    
    # Detect email provider
    username = config['IMAP']['username']
    server = config['IMAP']['server']
    provider_id = detect_email_provider(username, server)
    provider_config = provider_manager.get_provider_config(provider_id)
    
    print(f"Detected email provider: {provider_config.name} ({provider_id})")
    
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            print(f"Attempting to connect to mail server (attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS})...")
            
            # Create provider-specific connection
            try:
                mail = provider_manager.create_connection(
                    provider_id, 
                    config['IMAP']['server'], 
                    int(config['IMAP']['port'])
                )
            except Exception as e:
                # Fallback to basic connection
                print(f"Provider connection failed, using basic IMAP: {e}")
                mail = imaplib.IMAP4_SSL(config['IMAP']['server'], int(config['IMAP']['port']))
            
            # Set timeout
            if hasattr(mail, 'sock') and mail.sock:
                mail.sock.settimeout(CONNECTION_TIMEOUT)
            
            # Login with provider-specific handling
            mail.login(config['IMAP']['username'], config['IMAP']['password'])
            
            # Connection health check
            mail.noop()
            
            print(f"Successfully connected to {provider_config.name}")
            
            # Log provider-specific information
            if provider_config.quirks.get('app_password_required'):
                print("ℹ️  Using app-specific password authentication")
            if provider_config.oauth2_enabled:
                print("ℹ️  OAuth2 authentication available for this provider")
            
            return mail
            
        except Exception as e:
            last_exception = e
            print(f"Connection attempt {attempt + 1} failed: {e}")
            
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                # Exponential backoff with jitter
                delay = min(BASE_RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                jitter = random.uniform(0.1, 0.5) * delay
                total_delay = delay + jitter
                
                print(f"Retrying in {total_delay:.2f} seconds...")
                time.sleep(total_delay)
            else:
                print(f"All connection attempts failed. Last error: {e}")
    
    print(f"Error: Unable to connect to mail server after {MAX_RETRY_ATTEMPTS} attempts")
    if last_exception:
        print(f"Final error: {last_exception}")
    sys.exit(1)

def get_email_content(msg):
    """Extract email content from the email message (enhanced version)."""
    try:
        # Use enhanced parser
        enhanced_result = get_enhanced_email_content(msg)
        
        # Return in original format for backward compatibility
        return {
            'subject': enhanced_result.get('subject', ''),
            'from': enhanced_result.get('from', ''), 
            'content': enhanced_result.get('content', ''),
            # Additional fields for advanced processing
            'html_content': enhanced_result.get('html_content', ''),
            'text_content': enhanced_result.get('text_content', ''),
            'has_html': enhanced_result.get('has_html', False),
            'attachments': enhanced_result.get('attachments', []),
            'encoding_issues': enhanced_result.get('encoding_issues', False)
        }
    except Exception as e:
        print(f"Error in enhanced email parsing, falling back to basic parsing: {e}")
        
        # Fallback to basic parsing
        content = ""
        subject = ""
        from_email = ""
        
        try:
            # Get subject
            subject_header = email.header.decode_header(msg['Subject'])
            if subject_header[0][1] is None:
                subject = str(subject_header[0][0])
            else:
                subject = subject_header[0][0].decode(subject_header[0][1])
        except:
            subject = str(msg.get('Subject', ''))
        
        try:
            # Get sender
            from_header = email.header.decode_header(msg['From'])
            if from_header[0][1] is None:
                from_email = str(from_header[0][0])
            else:
                from_email = from_header[0][0].decode(from_header[0][1])
        except:
            from_email = str(msg.get('From', ''))
        
        # Get body (basic extraction)
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if "attachment" not in content_disposition:
                        if content_type == "text/plain":
                            try:
                                body = part.get_payload(decode=True)
                                if body:
                                    charset = part.get_content_charset() or 'utf-8'
                                    content += body.decode(charset, 'replace')
                            except Exception as e:
                                print(f"Error extracting text content: {e}")
            else:
                # Not multipart - get content directly
                try:
                    body = msg.get_payload(decode=True)
                    if body:
                        charset = msg.get_content_charset() or 'utf-8'
                        content += body.decode(charset, 'replace')
                except Exception as e:
                    print(f"Error extracting non-multipart content: {e}")
        except:
            pass
        
        # If no content was extracted, use subject as backup
        if not content.strip():
            content = subject
        
        return {
            'subject': subject,
            'from': from_email,
            'content': content,
            'html_content': '',
            'text_content': content,
            'has_html': False,
            'attachments': [],
            'encoding_issues': True
        }

def analyze_sentiment(text, config):
    """Analyze sentiment of the text using Hugging Face API with rate limiting."""
    try:
        # Truncate text if it's too long
        max_len = 1000  # Arbitrary limit to avoid huge API calls
        if len(text) > max_len:
            text = text[:max_len]
        
        api_url = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"
        headers = {"Authorization": f"Bearer {config['Hugging Face']['api_key']}"}
        
        def make_request():
            return requests.post(api_url, headers=headers, json={"inputs": text})
        
        # Use rate limiter
        api_response = throttled_huggingface_request(text, make_request)
        response = api_response.data
        
        if api_response.cached:
            print("Using cached sentiment analysis result")
        
        if hasattr(response, 'status_code') and response.status_code != 200:
            print(f"Error from Hugging Face API: {response.text}")
            return "NEUTRAL"
        
        # Handle cached responses (already parsed)
        if isinstance(response, str):
            return response
        
        # Parse fresh API response
        if hasattr(response, 'json'):
            result = response.json()
        else:
            result = response
        
        # The structure might be an array with label and score
        if isinstance(result, list) and len(result) > 0:
            # Return the predicted label (e.g., "POSITIVE", "NEGATIVE")
            sentiment = result[0].get('label', 'NEUTRAL')
            return sentiment
        
        return "NEUTRAL"
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return "NEUTRAL"

def categorize_email(email_data, sentiment, config):
    """Categorize email using OpenAI API with rate limiting."""
    try:
        # Create system message with categorization instructions
        system_message = """You are an email categorization expert. Analyze the email content and categorize it into exactly ONE of the following categories:

1. Client Communication
2. Client_Communication
3. Completed & Archived
4. Follow-Up Required
5. General Inquiries
6. Invoices & Payments
7. Marketing & Promotions
8. Pending & To Be Actioned
9. Personal & Non-Business
10. Reports & Documents
11. Spam & Unwanted
12. System & Notifications
13. Urgent & Time-Sensitive

Your task is to analyze the following email data and output ONLY the category as a JSON object with a single field "category" containing the exact category name from the list above."""
        
        # Create user message with email data and sentiment
        user_message = f"""EMAIL FROM: {email_data['from']}
EMAIL SUBJECT: {email_data['subject']}
EMAIL CONTENT: {email_data['content'][:1000]}  # Truncate content
SENTIMENT: {sentiment}

Output only a JSON with the category, for example:
{{"category": "Client Communication"}}"""
        
        # Create cache key from email content
        cache_content = f"{email_data['from']}|{email_data['subject']}|{email_data['content'][:500]}|{sentiment}"
        
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config['OpenAI']['api_key']}",
            "Content-Type": "application/json"
        }
        
        # Create API request
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.1
        }
        
        def make_request():
            return requests.post(api_url, headers=headers, json=data)
        
        # Use rate limiter
        api_response = throttled_openai_request(cache_content, make_request)
        response = api_response.data
        
        if api_response.cached:
            print("Using cached categorization result")
            # Cached response is already parsed
            if isinstance(response, str):
                return response
        
        if hasattr(response, 'status_code') and response.status_code != 200:
            print(f"Error from OpenAI API: {response.text}")
            return "General Inquiries"  # Default if API fails
        
        # Parse response
        if hasattr(response, 'json'):
            result = response.json()
        else:
            result = response
        
        # Extract the category from the response
        if isinstance(result, dict):
            assistant_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            assistant_response = str(result)
        
        # Try to parse the JSON response
        try:
            category_data = json.loads(assistant_response)
            category = category_data.get('category', 'General Inquiries')
            # Verify category is in our list
            if category not in CATEGORIES:
                print(f"Warning: Category '{category}' not in predefined categories, defaulting to General Inquiries")
                return "General Inquiries"
            return category
        except json.JSONDecodeError:
            print(f"Error parsing OpenAI response: {assistant_response}")
            return "General Inquiries"
        
    except Exception as e:
        print(f"Error categorizing email: {e}")
        return "General Inquiries"

def move_email_with_retry(mail, uid, target_folder, config):
    """Move an email to the target folder with retry logic and provider-specific handling."""
    # Detect provider for folder path handling
    username = config['IMAP']['username']
    server = config['IMAP']['server']
    provider_id = detect_email_provider(username, server)
    provider_config = provider_manager.get_provider_config(provider_id)
    
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            # Try provider-specific folder paths
            folder_variations = [
                target_folder,
                provider_manager.get_folder_path(provider_id, target_folder),
                provider_manager.normalize_folder_name(provider_id, target_folder)
            ]
            
            # Add common fallback variations
            folder_variations.extend([
                f'INBOX/{target_folder}',
                f'INBOX.{target_folder}',
                target_folder.replace(' ', '_'),
                target_folder.replace('&', '_')
            ])
            
            # Remove duplicates while preserving order
            unique_folders = []
            for folder in folder_variations:
                if folder not in unique_folders:
                    unique_folders.append(folder)
            
            success = False
            last_error = None
            
            # Try each folder variation
            for folder_path in unique_folders:
                try:
                    result = mail.uid('COPY', uid, folder_path)
                    
                    if result[0] == 'OK':
                        # Mark the source email for deletion
                        mail.uid('STORE', uid, '+FLAGS', '\\Deleted')
                        
                        # Handle provider-specific expunge behavior
                        if not provider_config.quirks.get('auto_expunge', True):
                            mail.expunge()
                        
                        print(f"📁 Email moved to: {folder_path}")
                        success = True
                        break
                    else:
                        last_error = result
                        
                except Exception as folder_error:
                    last_error = folder_error
                    continue
            
            if success:
                return True
            
            print(f"Error moving email (attempt {attempt + 1}): {last_error}")
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                time.sleep(BASE_RETRY_DELAY * (attempt + 1))
                continue
            return False
                
        except (imaplib.IMAP4.abort, imaplib.IMAP4.error, ConnectionResetError, BrokenPipeError) as e:
            print(f"Connection error moving email (attempt {attempt + 1}): {e}")
            
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                try:
                    # Try to reconnect
                    mail.close()
                    mail.logout()
                except:
                    pass
                
                # Reconnect
                mail = connect_to_mail_server(config)
                mail.select('INBOX')
                
                delay = BASE_RETRY_DELAY * (2 ** attempt)
                time.sleep(delay)
            else:
                return False
        except Exception as e:
            print(f"Error moving email (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                time.sleep(BASE_RETRY_DELAY * (attempt + 1))
            else:
                return False
    
    return False

def move_email(mail, uid, target_folder):
    """Legacy move email function for backward compatibility."""
    try:
        # Different email servers might require different folder prefixes
        # Try common variations if the direct move fails
        result = mail.uid('COPY', uid, target_folder)
        
        if result[0] == 'NO':
            # Try with INBOX. prefix
            result = mail.uid('COPY', uid, f'INBOX/{target_folder}')
        
        if result[0] == 'OK':
            # Mark the source email for deletion
            mail.uid('STORE', uid, '+FLAGS', '\\Deleted')
            # Expunge to actually remove it
            mail.expunge()
            return True
        else:
            print(f"Error moving email: {result}")
            return False
    except Exception as e:
        print(f"Error moving email: {e}")
        return False

def safe_imap_operation(mail, operation_func, *args, **kwargs):
    """Safely execute IMAP operations with retry logic."""
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            # Connection health check
            mail.noop()
            return operation_func(*args, **kwargs)
        except (imaplib.IMAP4.abort, imaplib.IMAP4.error, ConnectionResetError, BrokenPipeError) as e:
            print(f"IMAP operation failed (attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS}): {e}")
            
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                # Try to reconnect
                try:
                    mail.close()
                    mail.logout()
                except:
                    pass
                
                # Exponential backoff
                delay = min(BASE_RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                print(f"Reconnecting in {delay} seconds...")
                time.sleep(delay)
                
                # This would need to be handled at a higher level
                # since we need the config to reconnect
                raise ConnectionError(f"IMAP connection lost, reconnection needed")
            else:
                raise e
    
    raise Exception(f"IMAP operation failed after {MAX_RETRY_ATTEMPTS} attempts")

def process_emails(config, use_batch_processing=True, batch_size=10):
    """Main function to process emails with connection retry logic and optional batch processing."""
    mail = None
    
    try:
        mail = connect_to_mail_server(config)
        mail.select('INBOX')
        
        # Search for unread emails with retry logic
        try:
            result, data = safe_imap_operation(mail, mail.search, None, 'UNSEEN')
        except ConnectionError:
            # Reconnect and retry
            print("Reconnecting to mail server...")
            mail = connect_to_mail_server(config)
            mail.select('INBOX')
            result, data = mail.search(None, 'UNSEEN')
        
        if result != 'OK':
            print("No emails found or error in search")
            if mail:
                mail.logout()
            return
        
        email_nums = data[0].split()
        if not email_nums:
            print("No new emails found")
            if mail:
                mail.logout()
            return
        
        print(f"Found {len(email_nums)} unread email(s)")
        
        # Decide processing method based on email count and configuration
        if use_batch_processing and len(email_nums) >= 3:
            print(f"🚀 Using batch processing (batch size: {batch_size})")
            success = _process_emails_batch_mode(mail, email_nums, config, batch_size)
        else:
            print("🔄 Using sequential processing")
            success = _process_emails_sequential_mode(mail, email_nums, config)
        
        if not success:
            print("❌ Email processing completed with errors")
        else:
            print("✅ All emails processed successfully")

        # Note: persistence is handled in web interface demo; CLI pipeline can be extended similarly.
            
    except Exception as e:
        print(f"Error in email processing: {e}")
    finally:
        if mail:
            try:
                mail.logout()
            except:
                pass

def _process_emails_batch_mode(mail, email_nums, config, batch_size):
    """Process emails using batch processing mode."""
    try:
        # Fetch all emails first
        emails_data = []
        
        print("📥 Fetching emails for batch processing...")
        for i, num in enumerate(email_nums):
            try:
                # Fetch the email
                try:
                    result, msg_data = safe_imap_operation(mail, mail.fetch, num, '(RFC822)')
                except ConnectionError:
                    # Reconnect and retry
                    print("Reconnecting to mail server...")
                    mail = connect_to_mail_server(config)
                    mail.select('INBOX')
                    result, msg_data = mail.fetch(num, '(RFC822)')
                
                if result != 'OK':
                    print(f"❌ Error fetching email {num}")
                    continue
                
                # Parse the email
                msg = email.message_from_bytes(msg_data[0][1])
                email_data = get_email_content(msg)
                
                # Add email number for later reference
                email_data['email_num'] = num
                emails_data.append(email_data)
                
                print(f"   📧 Fetched ({i+1}/{len(email_nums)}): {email_data['subject'][:50]}...")
                
            except Exception as e:
                print(f"❌ Error fetching email {num}: {e}")
                continue
        
        if not emails_data:
            print("❌ No emails successfully fetched for batch processing")
            return False
        
        # Process emails in batches
        batch_results = process_emails_in_batches(
            emails_data, analyze_sentiment, categorize_email, config, batch_size
        )
        
        # Move emails based on batch results
        success_count = 0
        error_count = 0
        
        print("📤 Moving emails to categorized folders...")
        for result in batch_results:
            try:
                email_data = result['email']
                category = result['category']
                email_num = email_data['email_num']
                
                # Get UID for moving
                try:
                    result_uid, uid_data = safe_imap_operation(mail, mail.fetch, email_num, '(UID)')
                except ConnectionError:
                    # Reconnect and retry
                    print("Reconnecting to mail server...")
                    mail = connect_to_mail_server(config)
                    mail.select('INBOX')
                    result_uid, uid_data = mail.fetch(email_num, '(UID)')
                
                if result_uid != 'OK':
                    print(f"❌ Error fetching UID for email {email_num}")
                    error_count += 1
                    continue
                
                # Extract UID from response
                uid = uid_data[0].decode().split()[2].rstrip(')')
                
                # Move the email
                if move_email_with_retry(mail, uid, category, config):
                    success_count += 1
                    
                    # Enhanced logging
                    cached_info = " [Cached]" if result.get('cached_result') else ""
                    sentiment = result.get('sentiment', 'Unknown')
                    print(f"   ✅ {email_data['subject'][:40]}... → {category} ({sentiment}){cached_info}")
                else:
                    error_count += 1
                    print(f"   ❌ Failed to move: {email_data['subject'][:40]}...")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error moving email: {e}")
        
        print(f"\n📊 Batch processing results: {success_count} success, {error_count} errors")
        
        # Show batch processing stats
        stats = batch_processor.get_processing_stats()
        if stats['total_api_calls_saved'] > 0:
            print(f"💰 API calls saved: {stats['total_api_calls_saved']}")
        
        return error_count == 0
        
    except Exception as e:
        print(f"❌ Error in batch processing mode: {e}")
        return False

def _process_emails_sequential_mode(mail, email_nums, config):
    """Process emails using sequential processing mode (original method)."""
    try:
    
        success_count = 0
        error_count = 0
        
        for i, num in enumerate(email_nums):
            try:
                print(f"\n🔄 Processing email ({i+1}/{len(email_nums)})")
                
                # Fetch the email with retry logic
                try:
                    result, msg_data = safe_imap_operation(mail, mail.fetch, num, '(RFC822)')
                except ConnectionError:
                    # Reconnect and retry
                    print("Reconnecting to mail server...")
                    mail = connect_to_mail_server(config)
                    mail.select('INBOX')
                    result, msg_data = mail.fetch(num, '(RFC822)')
                
                if result != 'OK':
                    print(f"❌ Error fetching email {num}")
                    error_count += 1
                    continue
                
                # Parse the email
                msg = email.message_from_bytes(msg_data[0][1])
                email_data = get_email_content(msg)
                
                print(f"📧 {email_data['subject'][:60]}...")
                
                # Log additional parsing information
                info_parts = []
                if email_data.get('has_html'):
                    info_parts.append("HTML")
                if email_data.get('attachments'):
                    info_parts.append(f"{len(email_data['attachments'])} attachments")
                if email_data.get('encoding_issues'):
                    info_parts.append("encoding issues")
                
                if info_parts:
                    print(f"   ℹ️  {', '.join(info_parts)}")
                
                # Analyze sentiment (use enhanced content)
                # For HTML emails, prefer text content for sentiment analysis
                sentiment_text = email_data.get('text_content') or email_data.get('content')
                sentiment = analyze_sentiment(sentiment_text, config)
                
                # Categorize email (include additional context)
                enhanced_email_data = {
                    'from': email_data['from'],
                    'subject': email_data['subject'],
                    'content': email_data['content'],
                    'has_html': email_data.get('has_html', False),
                    'attachments_count': len(email_data.get('attachments', [])),
                    'text_content': email_data.get('text_content', ''),
                    'html_content': email_data.get('html_content', '')
                }
                
                category = categorize_email(enhanced_email_data, sentiment, config)
                
                # Move email to appropriate folder with retry logic
                try:
                    result, uid_data = safe_imap_operation(mail, mail.fetch, num, '(UID)')
                except ConnectionError:
                    # Reconnect and retry
                    print("Reconnecting to mail server...")
                    mail = connect_to_mail_server(config)
                    mail.select('INBOX')
                    result, uid_data = mail.fetch(num, '(UID)')
                
                if result != 'OK':
                    print(f"❌ Error fetching UID for email {num}")
                    error_count += 1
                    continue
                
                # Extract UID from response
                uid = uid_data[0].decode().split()[2].rstrip(')')
                
                # Move the email
                if move_email_with_retry(mail, uid, category, config):
                    success_count += 1
                    print(f"   ✅ → {category} ({sentiment})")
                else:
                    error_count += 1
                    print(f"   ❌ Failed to move to {category}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error processing email: {e}")
                
                # Try to extract basic info for debugging
                try:
                    if 'msg_data' in locals():
                        msg = email.message_from_bytes(msg_data[0][1])
                        subject = msg.get('Subject', 'Unknown Subject')[:50]
                        from_addr = msg.get('From', 'Unknown Sender')[:50]
                        print(f"   📧 Failed email: '{subject}' from '{from_addr}'")
                except:
                    print(f"   📧 Failed to extract basic email info for debugging")
        
        print(f"\n📊 Sequential processing results: {success_count} success, {error_count} errors")
        return error_count == 0
        
    except Exception as e:
        print(f"❌ Error in sequential processing mode: {e}")
        return False

def test_imap_connection(config):
    """Test IMAP connection for the web interface."""
    try:
        print("🔍 Testing IMAP connection...")
        
        # Connect to the mail server
        mail = connect_to_mail_server(config)
        if not mail:
            return {'status': 'error', 'message': 'Failed to connect to IMAP server'}
        
        # Test selecting INBOX
        mail.select('INBOX')
        
        # Test a simple search to verify access
        result, data = mail.search(None, 'ALL')
        if result != 'OK':
            mail.logout()
            return {'status': 'error', 'message': 'Failed to access INBOX'}
        
        # Count emails for info
        email_count = len(data[0].split()) if data[0] else 0
        
        # Close connection
        mail.logout()
        
        return {
            'status': 'success',
            'message': f'Successfully connected to IMAP server. Found {email_count} emails in INBOX.',
            'email_count': email_count
        }
        
    except Exception as e:
        return {'status': 'error', 'message': f'Connection test failed: {str(e)}'}

if __name__ == "__main__":
    config = load_config()
    process_emails(config)
    
    # Print API usage statistics
    rate_limiter.print_usage_report()
    print("Email categorization completed.")
