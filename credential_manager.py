#!/usr/bin/env python3
"""
Credential Manager
------------------
Secure credential storage and retrieval using encryption.
Handles API keys and email passwords with Fernet encryption.
"""

import os
import sys
import getpass
import base64
import configparser
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CredentialManager:
    """Manages encrypted credential storage and retrieval."""
    
    def __init__(self, config_file='config.ini', encrypted_file='config.encrypted'):
        self.config_file = config_file
        self.encrypted_file = encrypted_file
        self.salt_file = '.salt'
        self._fernet = None
        
    def _get_or_create_salt(self):
        """Get existing salt or create a new one."""
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return salt
    
    def _derive_key(self, password, salt):
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _get_master_password(self, confirm=False):
        """Get master password from user input."""
        if confirm:
            while True:
                password1 = getpass.getpass("Enter master password: ")
                password2 = getpass.getpass("Confirm master password: ")
                if password1 == password2:
                    if len(password1) < 8:
                        print("Password must be at least 8 characters long.")
                        continue
                    return password1
                else:
                    print("Passwords do not match. Please try again.")
        else:
            return getpass.getpass("Enter master password: ")
    
    def _initialize_encryption(self, password):
        """Initialize Fernet encryption with the given password."""
        salt = self._get_or_create_salt()
        key = self._derive_key(password, salt)
        self._fernet = Fernet(key)
    
    def encrypt_config(self, master_password=None):
        """Encrypt an existing plaintext config file."""
        if not os.path.exists(self.config_file):
            print(f"Error: Config file {self.config_file} not found.")
            return False
        
        if os.path.exists(self.encrypted_file):
            response = input(f"Encrypted config {self.encrypted_file} already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("Encryption cancelled.")
                return False
        
        # Get master password
        if master_password is None:
            print("Creating encrypted configuration...")
            master_password = self._get_master_password(confirm=True)
        
        try:
            # Initialize encryption
            self._initialize_encryption(master_password)
            
            # Read plaintext config
            with open(self.config_file, 'r') as f:
                plaintext_data = f.read()
            
            # Encrypt data
            encrypted_data = self._fernet.encrypt(plaintext_data.encode())
            
            # Write encrypted file
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"Configuration encrypted successfully to {self.encrypted_file}")
            
            # Ask if user wants to delete plaintext file
            response = input(f"Delete plaintext config file {self.config_file}? (y/N): ")
            if response.lower() == 'y':
                os.remove(self.config_file)
                print(f"Plaintext config {self.config_file} deleted.")
            else:
                print(f"Plaintext config {self.config_file} preserved.")
            
            return True
            
        except Exception as e:
            print(f"Error encrypting config: {e}")
            return False
    
    def decrypt_config(self, master_password=None):
        """Decrypt the encrypted config file and return a ConfigParser object."""
        if not os.path.exists(self.encrypted_file):
            # Fall back to plaintext config if encrypted doesn't exist
            if os.path.exists(self.config_file):
                print("Using plaintext configuration (consider encrypting with --encrypt)")
                config = configparser.ConfigParser()
                config.read(self.config_file)
                return config
            else:
                print(f"Error: No config file found ({self.config_file} or {self.encrypted_file})")
                return None
        
        # Get master password
        if master_password is None:
            master_password = self._get_master_password()
        
        try:
            # Initialize encryption
            self._initialize_encryption(master_password)
            
            # Read encrypted file
            with open(self.encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            decrypted_data = self._fernet.decrypt(encrypted_data)
            plaintext = decrypted_data.decode()
            
            # Parse as ConfigParser
            config = configparser.ConfigParser()
            config.read_string(plaintext)
            
            return config
            
        except Exception as e:
            print(f"Error decrypting config: {e}")
            print("This could be due to:")
            print("- Incorrect master password")
            print("- Corrupted encrypted file")
            print("- Missing salt file")
            return None
    
    def update_credential(self, section, key, value, master_password=None):
        """Update a specific credential in the encrypted config."""
        # Decrypt current config
        config = self.decrypt_config(master_password)
        if config is None:
            return False
        
        # Update the value
        if section not in config:
            config.add_section(section)
        config.set(section, key, value)
        
        # Convert back to string
        from io import StringIO
        output = StringIO()
        config.write(output)
        updated_config = output.getvalue()
        
        try:
            # Re-encrypt with same password
            if self._fernet is None:
                if master_password is None:
                    master_password = self._get_master_password()
                self._initialize_encryption(master_password)
            
            encrypted_data = self._fernet.encrypt(updated_config.encode())
            
            # Write back to encrypted file
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"Updated {section}.{key} in encrypted configuration")
            return True
            
        except Exception as e:
            print(f"Error updating credential: {e}")
            return False
    
    def migrate_from_plaintext(self):
        """Interactive migration from plaintext to encrypted config."""
        if not os.path.exists(self.config_file):
            print(f"No plaintext config file found at {self.config_file}")
            return False
        
        if os.path.exists(self.encrypted_file):
            print(f"Encrypted config already exists at {self.encrypted_file}")
            return False
        
        print("=== Credential Migration ===")
        print("This will encrypt your configuration file to protect sensitive data.")
        print("You will need to enter a master password to access the encrypted config.")
        print()
        
        response = input("Proceed with migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return False
        
        return self.encrypt_config()
    
    def change_master_password(self):
        """Change the master password for encrypted config."""
        if not os.path.exists(self.encrypted_file):
            print("No encrypted config file found.")
            return False
        
        print("=== Change Master Password ===")
        
        # Decrypt with current password
        current_password = self._get_master_password()
        config = self.decrypt_config(current_password)
        if config is None:
            print("Failed to decrypt with current password.")
            return False
        
        # Get new password
        print("Enter new master password:")
        new_password = self._get_master_password(confirm=True)
        
        # Convert config to string
        from io import StringIO
        output = StringIO()
        config.write(output)
        config_string = output.getvalue()
        
        try:
            # Create new salt and encrypt with new password
            if os.path.exists(self.salt_file):
                os.remove(self.salt_file)
            
            self._initialize_encryption(new_password)
            encrypted_data = self._fernet.encrypt(config_string.encode())
            
            # Write encrypted file
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            print("Master password changed successfully.")
            return True
            
        except Exception as e:
            print(f"Error changing master password: {e}")
            return False

def load_config_secure(config_file='config.ini', encrypted_file='config.encrypted'):
    """Load configuration securely (encrypted if available, fallback to plaintext)."""
    cm = CredentialManager(config_file, encrypted_file)
    return cm.decrypt_config()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Credential Manager for Email Categorization")
    parser.add_argument('--encrypt', action='store_true', help='Encrypt existing plaintext config')
    parser.add_argument('--migrate', action='store_true', help='Interactive migration from plaintext')
    parser.add_argument('--change-password', action='store_true', help='Change master password')
    parser.add_argument('--update', nargs=3, metavar=('SECTION', 'KEY', 'VALUE'), 
                       help='Update a credential (section key value)')
    
    args = parser.parse_args()
    
    cm = CredentialManager()
    
    if args.encrypt:
        cm.encrypt_config()
    elif args.migrate:
        cm.migrate_from_plaintext()
    elif args.change_password:
        cm.change_master_password()
    elif args.update:
        section, key, value = args.update
        cm.update_credential(section, key, value)
    else:
        # Test decryption
        config = cm.decrypt_config()
        if config:
            print("Configuration loaded successfully.")
            for section in config.sections():
                print(f"[{section}]")
                for key in config[section]:
                    # Mask sensitive values
                    value = config[section][key]
                    if 'password' in key.lower() or 'key' in key.lower():
                        masked = '*' * (len(value) - 4) + value[-4:] if len(value) > 4 else '****'
                        print(f"  {key} = {masked}")
                    else:
                        print(f"  {key} = {value}")
        else:
            print("Failed to load configuration.")