#!/usr/bin/env python3
"""
Setup Encryption Script
-----------------------
Interactive setup for encrypting email categorization credentials.
"""

import os
import sys
from credential_manager import CredentialManager

def main():
    """Interactive encryption setup."""
    print("=" * 60)
    print("EMAIL CATEGORIZATION - CREDENTIAL ENCRYPTION SETUP")
    print("=" * 60)
    print()
    
    cm = CredentialManager()
    
    # Check current state
    has_plaintext = os.path.exists('config.ini')
    has_encrypted = os.path.exists('config.encrypted')
    
    if has_encrypted and not has_plaintext:
        print("✅ Encrypted configuration already set up.")
        print("   Your credentials are stored securely.")
        print()
        print("Available commands:")
        print("  python3 credential_manager.py --change-password")
        print("  python3 credential_manager.py --update SECTION KEY VALUE")
        return
    
    if has_encrypted and has_plaintext:
        print("⚠️  Both plaintext and encrypted configs exist.")
        print("   Plaintext: config.ini")
        print("   Encrypted: config.encrypted")
        print()
        response = input("Remove plaintext config.ini? (y/N): ")
        if response.lower() == 'y':
            os.remove('config.ini')
            print("✅ Plaintext config removed. Using encrypted config.")
        else:
            print("⚠️  Both configs will remain. Encrypted takes precedence.")
        return
    
    if has_plaintext and not has_encrypted:
        print("📋 Found plaintext configuration file: config.ini")
        print("   This contains sensitive credentials in plain text.")
        print()
        print("🔒 Setting up encryption will:")
        print("   • Encrypt all credentials with a master password")
        print("   • Use industry-standard AES encryption (Fernet)")
        print("   • Protect against unauthorized access")
        print("   • Allow secure credential updates")
        print()
        
        response = input("Encrypt your configuration? (Y/n): ")
        if response.lower() in ['', 'y', 'yes']:
            success = cm.migrate_from_plaintext()
            if success:
                print()
                print("✅ Configuration encrypted successfully!")
                print("   Your credentials are now secure.")
                print()
                print("💡 Useful commands:")
                print("   python3 credential_manager.py --change-password")
                print("   python3 credential_manager.py --update SECTION KEY VALUE")
                print()
                print("🚀 You can now run the email categorizer:")
                print("   python3 email_categorizer.py")
            else:
                print("❌ Encryption setup failed.")
                sys.exit(1)
        else:
            print("Setup cancelled. Credentials remain in plaintext.")
    
    if not has_plaintext and not has_encrypted:
        print("❌ No configuration file found.")
        print("   Please create config.ini with your credentials first.")
        print()
        print("Example config.ini:")
        print("""
[IMAP]
server = imap.gmail.com
port = 993
username = your-email@gmail.com
password = your-app-password

[Hugging Face]
api_key = your-huggingface-api-key

[OpenAI]
api_key = your-openai-api-key
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)