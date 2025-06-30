#!/usr/bin/env python3
"""
Email Provider Compatibility Layer
----------------------------------
Handles provider-specific configurations, authentication methods,
and IMAP quirks for various email services.
"""

import imaplib
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass
class ProviderConfig:
    """Configuration for an email provider."""
    name: str
    imap_server: str
    imap_port: int
    smtp_server: str = ""
    smtp_port: int = 587
    use_ssl: bool = True
    use_starttls: bool = False
    folder_prefix: str = ""
    folder_separator: str = "/"
    auth_methods: List[str] = None
    oauth2_enabled: bool = False
    oauth2_scope: str = ""
    special_folders: Dict[str, str] = None
    quirks: Dict[str, any] = None

class EmailProviderManager:
    """Manages email provider configurations and compatibility."""
    
    def __init__(self):
        self.providers = self._initialize_providers()
    
    def _initialize_providers(self) -> Dict[str, ProviderConfig]:
        """Initialize configurations for major email providers."""
        providers = {}
        
        # Gmail
        providers['gmail'] = ProviderConfig(
            name="Gmail",
            imap_server="imap.gmail.com",
            imap_port=993,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_ssl=True,
            folder_prefix="",
            folder_separator="/",
            auth_methods=["password", "oauth2"],
            oauth2_enabled=True,
            oauth2_scope="https://www.googleapis.com/auth/gmail.readonly",
            special_folders={
                "inbox": "INBOX",
                "sent": "[Gmail]/Sent Mail",
                "drafts": "[Gmail]/Drafts",
                "trash": "[Gmail]/Trash",
                "spam": "[Gmail]/Spam",
                "important": "[Gmail]/Important"
            },
            quirks={
                "all_mail_folder": "[Gmail]/All Mail",
                "supports_labels": True,
                "case_sensitive_folders": False,
                "auto_expunge": False
            }
        )
        
        # Outlook.com / Hotmail
        providers['outlook'] = ProviderConfig(
            name="Outlook.com",
            imap_server="outlook.office365.com",
            imap_port=993,
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            use_ssl=True,
            folder_prefix="",
            folder_separator="/",
            auth_methods=["password", "oauth2"],
            oauth2_enabled=True,
            oauth2_scope="https://outlook.office.com/IMAP.AccessAsUser.All",
            special_folders={
                "inbox": "INBOX",
                "sent": "Sent Items",
                "drafts": "Drafts",
                "trash": "Deleted Items",
                "junk": "Junk Email"
            },
            quirks={
                "folder_encoding": "utf-7",
                "supports_idle": True,
                "case_sensitive_folders": False,
                "requires_auth_plain": True
            }
        )
        
        # Yahoo Mail
        providers['yahoo'] = ProviderConfig(
            name="Yahoo Mail",
            imap_server="imap.mail.yahoo.com",
            imap_port=993,
            smtp_server="smtp.mail.yahoo.com",
            smtp_port=587,
            use_ssl=True,
            folder_prefix="",
            folder_separator="/",
            auth_methods=["password"],
            oauth2_enabled=False,
            special_folders={
                "inbox": "INBOX",
                "sent": "Sent",
                "drafts": "Draft",
                "trash": "Trash",
                "spam": "Bulk Mail"
            },
            quirks={
                "app_password_required": True,
                "supports_idle": False,
                "case_sensitive_folders": True,
                "max_connections": 1
            }
        )
        
        # Apple iCloud
        providers['icloud'] = ProviderConfig(
            name="iCloud Mail",
            imap_server="imap.mail.me.com",
            imap_port=993,
            smtp_server="smtp.mail.me.com",
            smtp_port=587,
            use_ssl=True,
            folder_prefix="",
            folder_separator="/",
            auth_methods=["password"],
            oauth2_enabled=False,
            special_folders={
                "inbox": "INBOX",
                "sent": "Sent Messages",
                "drafts": "Drafts",
                "trash": "Deleted Messages",
                "junk": "Junk"
            },
            quirks={
                "app_password_required": True,
                "supports_idle": True,
                "case_sensitive_folders": False,
                "folder_encoding": "utf-7"
            }
        )
        
        # ProtonMail Bridge
        providers['protonmail'] = ProviderConfig(
            name="ProtonMail Bridge",
            imap_server="127.0.0.1",
            imap_port=1143,
            smtp_server="127.0.0.1",
            smtp_port=1025,
            use_ssl=False,
            use_starttls=True,
            folder_prefix="",
            folder_separator="/",
            auth_methods=["password"],
            oauth2_enabled=False,
            special_folders={
                "inbox": "INBOX",
                "sent": "Sent",
                "drafts": "Drafts",
                "trash": "Trash",
                "spam": "Spam"
            },
            quirks={
                "local_bridge_required": True,
                "supports_idle": False,
                "case_sensitive_folders": False,
                "bridge_auth": True
            }
        )
        
        # Generic IMAP (fallback)
        providers['generic'] = ProviderConfig(
            name="Generic IMAP",
            imap_server="",
            imap_port=993,
            smtp_server="",
            smtp_port=587,
            use_ssl=True,
            folder_prefix="",
            folder_separator="/",
            auth_methods=["password"],
            oauth2_enabled=False,
            special_folders={
                "inbox": "INBOX",
                "sent": "Sent",
                "drafts": "Drafts",
                "trash": "Trash"
            },
            quirks={}
        )
        
        return providers
    
    def detect_provider(self, email_address: str, imap_server: str = None) -> str:
        """Detect email provider from email address or server."""
        email_address = email_address.lower()
        
        # Extract domain from email
        if '@' in email_address:
            domain = email_address.split('@')[1]
        else:
            domain = email_address
        
        # Domain-based detection
        if domain in ['gmail.com', 'googlemail.com']:
            return 'gmail'
        elif domain in ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']:
            return 'outlook'
        elif domain in ['yahoo.com', 'yahoo.co.uk', 'yahoo.ca', 'ymail.com']:
            return 'yahoo'
        elif domain in ['icloud.com', 'me.com', 'mac.com']:
            return 'icloud'
        elif domain in ['protonmail.com', 'protonmail.ch', 'pm.me']:
            return 'protonmail'
        
        # Server-based detection (if provided)
        if imap_server:
            imap_server = imap_server.lower()
            for provider_id, config in self.providers.items():
                if config.imap_server.lower() in imap_server:
                    return provider_id
        
        return 'generic'
    
    def get_provider_config(self, provider_id: str) -> ProviderConfig:
        """Get configuration for a specific provider."""
        return self.providers.get(provider_id, self.providers['generic'])
    
    def get_folder_path(self, provider_id: str, folder_name: str) -> str:
        """Get the correct folder path for a provider."""
        config = self.get_provider_config(provider_id)
        
        # Check special folders first
        if folder_name.lower() in config.special_folders:
            return config.special_folders[folder_name.lower()]
        
        # Apply folder prefix if needed
        if config.folder_prefix:
            return f"{config.folder_prefix}{config.folder_separator}{folder_name}"
        
        return folder_name
    
    def normalize_folder_name(self, provider_id: str, folder_name: str) -> str:
        """Normalize folder name according to provider conventions."""
        config = self.get_provider_config(provider_id)
        
        # Handle case sensitivity
        if not config.quirks.get('case_sensitive_folders', True):
            folder_name = folder_name.lower()
        
        # Handle folder encoding
        if config.quirks.get('folder_encoding') == 'utf-7':
            try:
                # Convert to UTF-7 if needed
                folder_name = folder_name.encode('utf-7').decode('ascii')
            except:
                pass
        
        return folder_name
    
    def create_connection(self, provider_id: str, server: str = None, port: int = None) -> imaplib.IMAP4_SSL:
        """Create IMAP connection with provider-specific settings."""
        config = self.get_provider_config(provider_id)
        
        # Use provided server/port or defaults
        imap_server = server or config.imap_server
        imap_port = port or config.imap_port
        
        if not imap_server:
            raise ValueError(f"No IMAP server configured for provider {provider_id}")
        
        try:
            if config.use_ssl:
                mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            else:
                mail = imaplib.IMAP4(imap_server, imap_port)
                if config.use_starttls:
                    mail.starttls()
            
            # Apply provider-specific connection settings
            if config.quirks.get('requires_auth_plain'):
                # Some providers require AUTH=PLAIN
                pass  # This would be handled in authentication
            
            return mail
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {imap_server}:{imap_port} - {e}")
    
    def test_connection(self, provider_id: str, username: str, password: str, 
                       server: str = None, port: int = None) -> Tuple[bool, str]:
        """Test connection to email provider."""
        try:
            mail = self.create_connection(provider_id, server, port)
            
            # Test login
            mail.login(username, password)
            
            # Test basic operations
            mail.select('INBOX')
            result, data = mail.search(None, 'ALL')
            
            mail.logout()
            
            return True, "Connection successful"
            
        except Exception as e:
            return False, str(e)
    
    def get_setup_instructions(self, provider_id: str) -> Dict[str, str]:
        """Get setup instructions for a provider."""
        config = self.get_provider_config(provider_id)
        
        instructions = {
            'provider': config.name,
            'imap_server': config.imap_server,
            'imap_port': str(config.imap_port),
            'smtp_server': config.smtp_server,
            'smtp_port': str(config.smtp_port),
            'ssl_required': 'Yes' if config.use_ssl else 'No',
            'authentication': ', '.join(config.auth_methods or ['password'])
        }
        
        # Add provider-specific notes
        notes = []
        
        if config.quirks.get('app_password_required'):
            notes.append("App-specific password required (not your regular password)")
        
        if config.quirks.get('local_bridge_required'):
            notes.append("Local bridge application must be running")
        
        if config.oauth2_enabled:
            notes.append("OAuth2 authentication supported for enhanced security")
        
        if config.quirks.get('max_connections'):
            notes.append(f"Maximum {config.quirks['max_connections']} concurrent connection(s)")
        
        instructions['notes'] = notes
        
        return instructions
    
    def list_supported_providers(self) -> List[Dict[str, str]]:
        """List all supported email providers."""
        providers_list = []
        
        for provider_id, config in self.providers.items():
            if provider_id == 'generic':
                continue
                
            providers_list.append({
                'id': provider_id,
                'name': config.name,
                'server': config.imap_server,
                'oauth2_supported': config.oauth2_enabled,
                'app_password_required': config.quirks.get('app_password_required', False)
            })
        
        return providers_list

# Global provider manager
provider_manager = EmailProviderManager()

def detect_email_provider(email_address: str, imap_server: str = None) -> str:
    """Detect email provider from address or server."""
    return provider_manager.detect_provider(email_address, imap_server)

def get_provider_config(provider_id: str) -> ProviderConfig:
    """Get provider configuration."""
    return provider_manager.get_provider_config(provider_id)

def create_provider_connection(provider_id: str, server: str = None, port: int = None) -> imaplib.IMAP4_SSL:
    """Create provider-specific IMAP connection."""
    return provider_manager.create_connection(provider_id, server, port)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Email Provider Compatibility Tool")
    parser.add_argument('--list', action='store_true', help='List supported providers')
    parser.add_argument('--detect', help='Detect provider for email address')
    parser.add_argument('--test', nargs=2, metavar=('EMAIL', 'PASSWORD'), help='Test connection')
    parser.add_argument('--setup', help='Show setup instructions for provider')
    
    args = parser.parse_args()
    
    if args.list:
        print("Supported Email Providers:")
        print("=" * 50)
        for provider in provider_manager.list_supported_providers():
            print(f"• {provider['name']} ({provider['id']})")
            print(f"  Server: {provider['server']}")
            print(f"  OAuth2: {'Yes' if provider['oauth2_supported'] else 'No'}")
            print(f"  App Password: {'Required' if provider['app_password_required'] else 'Not required'}")
            print()
    
    elif args.detect:
        provider_id = detect_email_provider(args.detect)
        config = get_provider_config(provider_id)
        print(f"Detected provider: {config.name} ({provider_id})")
    
    elif args.test:
        email, password = args.test
        provider_id = detect_email_provider(email)
        success, message = provider_manager.test_connection(provider_id, email, password)
        print(f"Connection test: {'✅ Success' if success else '❌ Failed'}")
        print(f"Message: {message}")
    
    elif args.setup:
        instructions = provider_manager.get_setup_instructions(args.setup)
        print(f"Setup Instructions for {instructions['provider']}:")
        print("=" * 50)
        print(f"IMAP Server: {instructions['imap_server']}")
        print(f"IMAP Port: {instructions['imap_port']}")
        print(f"SMTP Server: {instructions['smtp_server']}")
        print(f"SMTP Port: {instructions['smtp_port']}")
        print(f"SSL Required: {instructions['ssl_required']}")
        print(f"Authentication: {instructions['authentication']}")
        
        if instructions['notes']:
            print("\nImportant Notes:")
            for note in instructions['notes']:
                print(f"• {note}")
    
    else:
        parser.print_help()