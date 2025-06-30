# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is an AI-powered email categorization system that automatically sorts emails into predefined folders using sentiment analysis and content categorization. The system integrates with IMAP email servers (Gmail configured) and uses HuggingFace API for sentiment analysis and OpenAI GPT-3.5-turbo for email categorization.

## Core Architecture

### Main Components
- **email_categorizer.py**: Core categorization engine with IMAP integration
- **email_categorizer_continuous.py**: Continuous monitoring wrapper around the core engine
- **config.ini**: Configuration file containing API keys and email server settings
- **Shell scripts**: Various execution modes (manual, daemon, cron, launch agent)

### Data Flow
1. Connect to IMAP server and fetch unread emails
2. Extract email content (subject, sender, body) with encoding handling
3. Analyze sentiment using HuggingFace DistilBERT model
4. Categorize email using OpenAI GPT-3.5-turbo with structured prompts
5. Move email to appropriate folder via IMAP commands

### Predefined Categories
The system categorizes emails into 13 predefined folders:
- Client Communication / Client_Communication
- Completed & Archived
- Follow-Up Required
- General Inquiries
- Invoices & Payments
- Marketing & Promotions
- Pending & To Be Actioned
- Personal & Non-Business
- Reports & Documents
- Spam & Unwanted
- System & Notifications
- Urgent & Time-Sensitive

## Development Commands

### Setup and Installation
```bash
# Install dependencies
./setup.sh

# Verify configuration
cat config.ini
```

### Running the System
```bash
# One-time execution
./run_categorizer.sh

# Continuous monitoring (60 second intervals)
python3 email_categorizer_continuous.py

# Custom monitoring interval (e.g., 300 seconds)
python3 email_categorizer_continuous.py 300

# Daemon management
./daemon.sh start|stop|restart|status

# Setup macOS launch agent
./setup_launch_agent.sh
launchctl load ~/Library/LaunchAgents/com.sunlec.emailcategorizer.plist
```

### Testing and Debugging
```bash
# Check logs
tail -f categorization.log
tail -f categorizer.log
tail -f categorizer_error.log

# Test single email processing
python3 email_categorizer.py

# Monitor daemon status
./daemon.sh status
```

## Key Technical Considerations

### Email Processing
- Uses IMAP4_SSL for secure connection
- Handles multipart MIME messages and various encodings
- Implements graceful error handling for malformed emails
- Extracts content from text/plain parts while avoiding attachments

### API Integration
- HuggingFace API limited to 1000 characters for sentiment analysis
- OpenAI API uses structured prompts with JSON response format
- Temperature set to 0.1 for consistent categorization results
- Implements fallback to "General Inquiries" for API failures

### Email Movement
- Uses IMAP COPY and STORE operations for moving emails
- Handles different folder prefix patterns (direct, INBOX/ prefix)
- Implements proper email deletion with EXPUNGE

### Error Handling
- Comprehensive try-catch blocks throughout the pipeline
- Graceful degradation when APIs are unavailable
- Connection retry logic not implemented (manual restart required)

## Configuration Requirements

### Email Server Setup
- IMAP server must support SSL (Gmail configured by default)
- All 13 predefined folders must exist in the email account
- Account must have proper authentication (App Password for Gmail)

### API Keys Required
- HuggingFace API key for sentiment analysis
- OpenAI API key for email categorization
- Keys stored in config.ini (not version controlled)

## Security Considerations
- API keys and email credentials stored in plaintext config file
- No encryption for stored credentials
- IMAP connection uses SSL/TLS
- Email content sent to external APIs (HuggingFace, OpenAI)

## Monitoring and Logging
- Basic logging to categorization.log for manual runs
- Separate logs for launch agent (categorizer.log, categorizer_error.log)
- Process monitoring through daemon.sh script
- No built-in alerting or health checks