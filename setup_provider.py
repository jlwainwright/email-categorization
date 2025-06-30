#!/usr/bin/env python3
"""
Email Provider Setup Wizard
---------------------------
Interactive setup wizard for configuring email providers.
"""

import os
import sys
import configparser
from email_providers import provider_manager, detect_email_provider
from credential_manager import CredentialManager

class ProviderSetupWizard:
    """Interactive setup wizard for email providers."""
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.credential_manager = CredentialManager()
    
    def run_setup(self):
        """Run the complete setup wizard."""
        print("🔧" * 20)
        print("EMAIL PROVIDER SETUP WIZARD")
        print("🔧" * 20)
        print()
        
        # Step 1: Email address
        email = self._get_email_address()
        
        # Step 2: Detect or select provider
        provider_id = self._detect_and_confirm_provider(email)
        
        # Step 3: Get provider configuration
        provider_config = provider_manager.get_provider_config(provider_id)
        
        # Step 4: Display setup instructions
        self._show_setup_instructions(provider_id, email)
        
        # Step 5: Get credentials
        server, port, password = self._get_provider_credentials(provider_config, email)
        
        # Step 6: Test connection
        if self._test_connection(provider_id, email, password, server, port):
            # Step 7: Save configuration
            self._save_configuration(provider_config, email, password, server, port)
            print("\n✅ Setup completed successfully!")
            print("You can now run the email categorizer.")
        else:
            print("\n❌ Setup failed. Please check your credentials and try again.")
    
    def _get_email_address(self):
        """Get email address from user."""
        while True:
            email = input("Enter your email address: ").strip()
            if '@' in email and '.' in email.split('@')[1]:
                return email
            print("Please enter a valid email address.")
    
    def _detect_and_confirm_provider(self, email):
        """Detect provider and confirm with user."""
        detected_provider = detect_email_provider(email)
        provider_config = provider_manager.get_provider_config(detected_provider)
        
        print(f"\n📧 Detected email provider: {provider_config.name}")
        
        if detected_provider == 'generic':
            print("⚠️  Generic provider detected. You may need to provide custom settings.")
            return self._select_provider_manually()
        
        confirm = input(f"Is this correct? (Y/n): ").strip().lower()
        if confirm in ['', 'y', 'yes']:
            return detected_provider
        else:
            return self._select_provider_manually()
    
    def _select_provider_manually(self):
        """Let user manually select provider."""
        print("\nSupported providers:")
        providers = provider_manager.list_supported_providers()
        
        for i, provider in enumerate(providers, 1):
            print(f"{i}. {provider['name']}")
        print(f"{len(providers) + 1}. Custom/Generic IMAP")
        
        while True:
            try:
                choice = int(input(f"\nSelect provider (1-{len(providers) + 1}): "))
                if 1 <= choice <= len(providers):
                    return providers[choice - 1]['id']
                elif choice == len(providers) + 1:
                    return 'generic'
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
    
    def _show_setup_instructions(self, provider_id, email):
        """Show provider-specific setup instructions."""
        instructions = provider_manager.get_setup_instructions(provider_id)
        
        print(f"\n📋 Setup Instructions for {instructions['provider']}:")
        print("=" * 50)
        
        if provider_id == 'generic':
            print("You'll need to provide custom IMAP server settings.")
        else:
            print(f"IMAP Server: {instructions['imap_server']}")
            print(f"IMAP Port: {instructions['imap_port']}")
            print(f"SSL Required: {instructions['ssl_required']}")
            print(f"Authentication: {instructions['authentication']}")
        
        if instructions.get('notes'):
            print("\n⚠️  Important Notes:")
            for note in instructions['notes']:
                print(f"   • {note}")
        
        print("\n" + "=" * 50)
    
    def _get_provider_credentials(self, provider_config, email):
        """Get credentials and server settings from user."""
        # Server settings
        if provider_config.name == "Generic IMAP":
            server = input("Enter IMAP server: ").strip()
            port = input(f"Enter IMAP port (default {provider_config.imap_port}): ").strip()
            port = int(port) if port else provider_config.imap_port
        else:
            server = provider_config.imap_server
            port = provider_config.imap_port
        
        # Password
        print(f"\nPassword for {email}:")
        
        if provider_config.quirks.get('app_password_required'):
            print("⚠️  This provider requires an app-specific password.")
            print("   Do not use your regular account password.")
            password = input("Enter app-specific password: ").strip()
        else:
            password = input("Enter password: ").strip()
        
        return server, port, password
    
    def _test_connection(self, provider_id, email, password, server, port):
        """Test the connection with provided credentials."""
        print(f"\n🔄 Testing connection to {server}...")
        
        success, message = provider_manager.test_connection(
            provider_id, email, password, server, port
        )
        
        if success:
            print("✅ Connection test successful!")
            return True
        else:
            print(f"❌ Connection test failed: {message}")
            
            # Offer troubleshooting
            self._show_troubleshooting_tips(provider_id)
            return False
    
    def _show_troubleshooting_tips(self, provider_id):
        """Show troubleshooting tips for connection failures."""
        print("\n🔧 Troubleshooting Tips:")
        
        provider_config = provider_manager.get_provider_config(provider_id)
        
        if provider_config.quirks.get('app_password_required'):
            print("   • Make sure you're using an app-specific password, not your regular password")
            print("   • Check that app passwords are enabled in your account settings")
        
        if provider_id == 'gmail':
            print("   • Enable 'Less secure app access' or use app passwords")
            print("   • Check that 2-factor authentication is properly configured")
        
        elif provider_id == 'outlook':
            print("   • Ensure IMAP is enabled in your Outlook.com settings")
            print("   • Try using OAuth2 if available")
        
        elif provider_id == 'yahoo':
            print("   • Generate an app password in Yahoo Account Security")
            print("   • Make sure IMAP access is enabled")
        
        print("   • Check your internet connection and firewall settings")
        print("   • Verify the email address and password are correct")
    
    def _save_configuration(self, provider_config, email, password, server, port):
        """Save configuration to file."""
        print("\n💾 Saving configuration...")
        
        # Create configuration
        self.config['IMAP'] = {
            'server': server,
            'port': str(port),
            'username': email,
            'password': password
        }
        
        # Add placeholder sections for APIs
        if not self.config.has_section('Hugging Face'):
            self.config['Hugging Face'] = {
                'api_key': 'your-huggingface-api-key-here'
            }
        
        if not self.config.has_section('OpenAI'):
            self.config['OpenAI'] = {
                'api_key': 'your-openai-api-key-here'
            }
        
        # Save to file
        with open('config.ini', 'w') as f:
            self.config.write(f)
        
        print("✅ Configuration saved to config.ini")
        
        # Encrypt configuration
        encrypt_choice = input("\n🔒 Encrypt configuration for security? (Y/n): ").strip().lower()
        if encrypt_choice in ['', 'y', 'yes']:
            success = self.credential_manager.migrate_from_plaintext()
            if success:
                print("✅ Configuration encrypted successfully!")
            else:
                print("⚠️  Encryption failed, but plaintext config is available.")
        
        # Show next steps
        self._show_next_steps()
    
    def _show_next_steps(self):
        """Show next steps after setup."""
        print("\n🚀 Next Steps:")
        print("=" * 30)
        print("1. Add your HuggingFace API key to the configuration")
        print("2. Add your OpenAI API key to the configuration")
        print("3. Create the required email folders in your email client")
        print("4. Run the email categorizer: python3 email_categorizer.py")
        print()
        print("📂 Required email folders:")
        for category in [
            "Client Communication", "Completed & Archived", "Follow-Up Required",
            "General Inquiries", "Invoices & Payments", "Marketing & Promotions",
            "Pending & To Be Actioned", "Personal & Non-Business", "Reports & Documents",
            "Spam & Unwanted", "System & Notifications", "Urgent & Time-Sensitive"
        ]:
            print(f"   • {category}")

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--provider-info':
        # Show provider information
        print("Supported Email Providers:")
        print("=" * 50)
        for provider in provider_manager.list_supported_providers():
            print(f"• {provider['name']}")
            print(f"  Server: {provider['server']}")
            print(f"  OAuth2: {'Yes' if provider['oauth2_supported'] else 'No'}")
            print(f"  App Password: {'Required' if provider['app_password_required'] else 'Not required'}")
            print()
    else:
        # Run setup wizard
        wizard = ProviderSetupWizard()
        try:
            wizard.run_setup()
        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user.")
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")

if __name__ == "__main__":
    main()