#!/usr/bin/env python3
"""
Enhanced Email Parser
---------------------
Advanced email content parsing with support for complex MIME structures,
HTML content extraction, various encodings, and content sanitization.
"""

import email
import email.header
import quopri
import base64
import html
import re
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Tuple
import chardet

class EmailContentExtractor:
    """Advanced email content extraction with enhanced parsing capabilities."""
    
    def __init__(self):
        # Patterns for cleaning content
        self.tracking_patterns = [
            r'<img[^>]*?src=["\']https?://[^"\']*?track[^"\']*?["\'][^>]*?>',  # Tracking pixels
            r'<img[^>]*?width=["\']1["\'][^>]*?height=["\']1["\'][^>]*?>',     # 1x1 tracking images
            r'https?://[^\s]*?utm_[^\s]*',                                    # UTM tracking links
            r'https?://[^\s]*?fbclid=[^\s]*',                                 # Facebook tracking
            r'https?://[^\s]*?gclid=[^\s]*',                                  # Google tracking
        ]
        
        # Patterns for content cleanup
        self.cleanup_patterns = [
            r'\s+',                           # Multiple whitespace
            r'\n\s*\n\s*\n',                 # Multiple line breaks
            r'^\s+|\s+$',                    # Leading/trailing whitespace
        ]
        
        # HTML tags to preserve for structure
        self.preserve_tags = ['p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol']
    
    def _detect_encoding(self, raw_bytes: bytes, declared_encoding: str = None) -> str:
        """Detect the actual encoding of email content."""
        # Try declared encoding first
        if declared_encoding:
            try:
                raw_bytes.decode(declared_encoding)
                return declared_encoding.lower()
            except (UnicodeDecodeError, LookupError):
                pass
        
        # Use chardet for detection
        try:
            detected = chardet.detect(raw_bytes)
            if detected and detected['confidence'] > 0.7:
                return detected['encoding'].lower()
        except Exception:
            pass
        
        # Fallback encodings in order of preference
        fallback_encodings = ['utf-8', 'iso-8859-1', 'windows-1252', 'ascii']
        
        for encoding in fallback_encodings:
            try:
                raw_bytes.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        
        # Last resort - decode with errors='replace'
        return 'utf-8'
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header with proper encoding handling."""
        if not header_value:
            return ""
        
        try:
            decoded_parts = email.header.decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        try:
                            decoded_string += part.decode(encoding)
                        except (UnicodeDecodeError, LookupError):
                            # Try to detect encoding
                            detected_encoding = self._detect_encoding(part, encoding)
                            decoded_string += part.decode(detected_encoding, errors='replace')
                    else:
                        # Try to detect encoding
                        detected_encoding = self._detect_encoding(part)
                        decoded_string += part.decode(detected_encoding, errors='replace')
                else:
                    decoded_string += str(part)
            
            return decoded_string.strip()
        except Exception as e:
            print(f"Error decoding header: {e}")
            return str(header_value)
    
    def _decode_content(self, part) -> str:
        """Decode email part content with proper encoding and transfer encoding handling."""
        try:
            # Get the payload
            payload = part.get_payload(decode=False)
            
            if isinstance(payload, list):
                # Multipart - shouldn't happen at this level
                return ""
            
            if not payload:
                return ""
            
            # Handle transfer encoding
            transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
            
            if transfer_encoding == 'base64':
                try:
                    payload = base64.b64decode(payload)
                except Exception as e:
                    print(f"Error decoding base64: {e}")
                    return ""
            elif transfer_encoding == 'quoted-printable':
                try:
                    if isinstance(payload, str):
                        payload = payload.encode('ascii')
                    payload = quopri.decodestring(payload)
                except Exception as e:
                    print(f"Error decoding quoted-printable: {e}")
                    return ""
            elif isinstance(payload, str):
                payload = payload.encode('utf-8')
            
            # Handle character encoding
            charset = part.get_content_charset()
            if not charset:
                charset = part.get_charset()
            
            if isinstance(payload, bytes):
                detected_encoding = self._detect_encoding(payload, charset)
                try:
                    return payload.decode(detected_encoding, errors='replace')
                except Exception as e:
                    print(f"Error decoding content: {e}")
                    return payload.decode('utf-8', errors='replace')
            else:
                return str(payload)
                
        except Exception as e:
            print(f"Error in _decode_content: {e}")
            return ""
    
    def _extract_html_content(self, html_content: str) -> str:
        """Extract text content from HTML with structure preservation."""
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()
            
            # Remove tracking pixels and images
            for pattern in self.tracking_patterns:
                for match in soup.find_all(string=re.compile(pattern, re.IGNORECASE)):
                    if match.parent:
                        match.parent.decompose()
            
            # Remove tracking images
            for img in soup.find_all('img'):
                src = img.get('src', '')
                width = img.get('width', '')
                height = img.get('height', '')
                
                # Remove tracking pixels (1x1 images or tracking URLs)
                if (width == '1' and height == '1') or any(track in src.lower() for track in ['track', 'pixel', 'beacon']):
                    img.decompose()
                    continue
                
                # Replace remaining images with alt text or placeholder
                alt_text = img.get('alt', '[Image]')
                img.replace_with(f"[{alt_text}]")
            
            # Convert links to text with URL
            for link in soup.find_all('a'):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Skip tracking links
                if any(track in href.lower() for track in ['utm_', 'fbclid', 'gclid', 'track']):
                    link.replace_with(text if text else '[Link]')
                elif href and text and href != text:
                    link.replace_with(f"{text} ({href})")
                elif text:
                    link.replace_with(text)
                else:
                    link.replace_with('[Link]')
            
            # Add line breaks for block elements
            for tag in soup.find_all(['p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if tag.name == 'br':
                    tag.replace_with('\n')
                else:
                    # Add newlines around block elements
                    tag.insert_before('\n')
                    tag.insert_after('\n')
            
            # Add line breaks for list items
            for li in soup.find_all('li'):
                li.insert_before('\n• ')
                li.insert_after('\n')
            
            # Get text content
            text = soup.get_text()
            
            # Clean up the text
            text = self._clean_text_content(text)
            
            return text
            
        except Exception as e:
            print(f"Error extracting HTML content: {e}")
            # Fallback - strip all HTML tags
            return re.sub(r'<[^>]+>', ' ', html_content)
    
    def _clean_text_content(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Unescape HTML entities
        text = html.unescape(text)
        
        # Apply cleanup patterns
        # Multiple whitespace -> single space
        text = re.sub(r'\s+', ' ', text)
        
        # Multiple line breaks -> double line break
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Clean up bullet points
        text = re.sub(r'\n\s*•\s*\n', '\n• ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _extract_attachments_info(self, msg) -> List[Dict[str, str]]:
        """Extract information about email attachments."""
        attachments = []
        
        for part in msg.walk():
            content_disposition = part.get("Content-Disposition", "")
            
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    filename = self._decode_header(filename)
                else:
                    filename = "unnamed_attachment"
                
                content_type = part.get_content_type()
                content_size = len(part.get_payload(decode=True) or b"")
                
                attachments.append({
                    'filename': filename,
                    'content_type': content_type,
                    'size': content_size
                })
        
        return attachments
    
    def extract_email_content(self, msg) -> Dict[str, any]:
        """
        Extract comprehensive email content from email message.
        
        Returns:
            Dict containing subject, from, to, content, html_content, attachments, etc.
        """
        result = {
            'subject': '',
            'from': '',
            'to': '',
            'cc': '',
            'date': '',
            'content': '',
            'html_content': '',
            'text_content': '',
            'attachments': [],
            'has_html': False,
            'encoding_issues': False
        }
        
        try:
            # Extract headers
            result['subject'] = self._decode_header(msg.get('Subject', ''))
            result['from'] = self._decode_header(msg.get('From', ''))
            result['to'] = self._decode_header(msg.get('To', ''))
            result['cc'] = self._decode_header(msg.get('Cc', ''))
            result['date'] = self._decode_header(msg.get('Date', ''))
            
            # Extract attachments info
            result['attachments'] = self._extract_attachments_info(msg)
            
            # Extract content
            text_parts = []
            html_parts = []
            
            if msg.is_multipart():
                # Handle multipart messages
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get("Content-Disposition", "")
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    try:
                        if content_type == "text/plain":
                            content = self._decode_content(part)
                            if content.strip():
                                text_parts.append(content)
                        
                        elif content_type == "text/html":
                            html_content = self._decode_content(part)
                            if html_content.strip():
                                html_parts.append(html_content)
                                result['has_html'] = True
                        
                    except Exception as e:
                        print(f"Error processing part {content_type}: {e}")
                        result['encoding_issues'] = True
            
            else:
                # Handle non-multipart messages
                content_type = msg.get_content_type()
                
                try:
                    if content_type == "text/plain":
                        content = self._decode_content(msg)
                        if content.strip():
                            text_parts.append(content)
                    
                    elif content_type == "text/html":
                        html_content = self._decode_content(msg)
                        if html_content.strip():
                            html_parts.append(html_content)
                            result['has_html'] = True
                    
                except Exception as e:
                    print(f"Error processing message content: {e}")
                    result['encoding_issues'] = True
            
            # Combine and clean content
            if html_parts:
                # Extract text from HTML
                combined_html = '\n\n'.join(html_parts)
                result['html_content'] = combined_html
                
                # Extract clean text from HTML
                extracted_text = self._extract_html_content(combined_html)
                
                # Combine with plain text parts
                all_text = text_parts + [extracted_text] if extracted_text else text_parts
                result['content'] = self._clean_text_content('\n\n'.join(all_text))
                result['text_content'] = '\n\n'.join(text_parts) if text_parts else ""
            
            elif text_parts:
                # Plain text only
                result['content'] = self._clean_text_content('\n\n'.join(text_parts))
                result['text_content'] = result['content']
            
            else:
                # No content found - use subject as fallback
                result['content'] = result['subject']
                result['text_content'] = result['subject']
            
            # Ensure we have some content
            if not result['content'].strip():
                if result['subject']:
                    result['content'] = result['subject']
                else:
                    result['content'] = "[No content available]"
            
        except Exception as e:
            print(f"Error in extract_email_content: {e}")
            result['encoding_issues'] = True
            
            # Fallback extraction
            result['subject'] = str(msg.get('Subject', ''))
            result['from'] = str(msg.get('From', ''))
            result['content'] = result['subject'] if result['subject'] else "[Error extracting content]"
        
        return result

# Global extractor instance
email_extractor = EmailContentExtractor()

def get_enhanced_email_content(msg) -> Dict[str, any]:
    """
    Enhanced email content extraction function.
    Drop-in replacement for the original get_email_content function.
    """
    return email_extractor.extract_email_content(msg)

if __name__ == "__main__":
    # Test the enhanced parser
    print("Testing Enhanced Email Parser...")
    
    # Create a test email
    test_msg = MIMEMultipart('alternative')
    test_msg['Subject'] = 'Test Email with HTML and Attachments'
    test_msg['From'] = 'sender@example.com'
    test_msg['To'] = 'recipient@example.com'
    
    # Add plain text part
    text_part = MIMEText('This is the plain text content of the email.', 'plain')
    test_msg.attach(text_part)
    
    # Add HTML part
    html_content = '''
    <html>
        <body>
            <h1>HTML Email Content</h1>
            <p>This is <b>bold</b> text with a <a href="https://example.com">link</a>.</p>
            <img src="https://tracker.com/pixel.gif" width="1" height="1" alt="">
            <p>More content here.</p>
        </body>
    </html>
    '''
    html_part = MIMEText(html_content, 'html')
    test_msg.attach(html_part)
    
    # Test extraction
    result = get_enhanced_email_content(test_msg)
    
    print("Extraction Results:")
    print(f"Subject: {result['subject']}")
    print(f"From: {result['from']}")
    print(f"Has HTML: {result['has_html']}")
    print(f"Content: {result['content']}")
    print(f"Attachments: {len(result['attachments'])}")