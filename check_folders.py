#!/usr/bin/env python3
import imaplib
import ssl
import configparser

def check_imap_folders():
    # Read configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    server = config['IMAP']['server']
    port = int(config['IMAP']['port'])
    username = config['IMAP']['username']
    password = config['IMAP']['password']
    
    # Required folders for email categorization
    required_folders = [
        'Client Communication',
        'Client_Communication',
        'Completed & Archived',
        'Follow-Up Required',
        'General Inquiries',
        'Invoices & Payments',
        'Marketing & Promotions',
        'Pending & To Be Actioned',
        'Personal & Non-Business',
        'Reports & Documents',
        'Spam & Unwanted',
        'System & Notifications',
        'Urgent & Time-Sensitive'
    ]
    
    try:
        # Connect to IMAP server
        print(f"Connecting to {server}:{port}...")
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(username, password)
        print(f"Successfully logged in as {username}")
        
        # List all folders
        print("\nListing all folders:")
        result, folders = mail.list()
        
        if result == 'OK':
            existing_folders = []
            for folder in folders:
                folder_name = folder.decode('utf-8')
                print(f"  {folder_name}")
                # Extract folder name from IMAP response
                # Format is typically: (\\HasNoChildren) "/" "FolderName"
                parts = folder_name.split('"')
                if len(parts) >= 3:
                    clean_name = parts[-2]
                    existing_folders.append(clean_name)
        
        print(f"\nChecking for required folders:")
        missing_folders = []
        
        for req_folder in required_folders:
            found = False
            for existing in existing_folders:
                if req_folder in existing or existing.endswith(req_folder):
                    print(f"  ✓ Found: {req_folder} (matches: {existing})")
                    found = True
                    break
            
            if not found:
                print(f"  ✗ Missing: {req_folder}")
                missing_folders.append(req_folder)
        
        if missing_folders:
            print(f"\nMissing folders ({len(missing_folders)}):")
            for folder in missing_folders:
                print(f"  - {folder}")
        else:
            print("\n✓ All required folders found!")
        
        mail.logout()
        
    except Exception as e:
        print(f"Error connecting to IMAP server: {e}")

if __name__ == "__main__":
    check_imap_folders()