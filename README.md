# AI-Powered Email Categorization System

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![IMAP](https://img.shields.io/badge/Protocol-IMAP-orange.svg)](https://en.wikipedia.org/wiki/Internet_Message_Access_Protocol)

An intelligent email categorization system that automatically sorts emails into predefined folders using AI-powered sentiment analysis and content categorization. The system integrates with IMAP email servers and uses HuggingFace and OpenAI APIs for advanced email processing.

## 🎯 System Overview

This system automatically processes incoming emails and categorizes them into 13 predefined business folders using:
- **HuggingFace DistilBERT** for sentiment analysis
- **OpenAI GPT-3.5-turbo** for intelligent categorization
- **IMAP protocol** for secure email server communication

## 🏗️ System Architecture & Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Email Server  │    │  IMAP Connection │    │  Email Fetcher  │
│ (mail.sunlec    │───▶│   (SSL/TLS)      │───▶│   & Parser      │
│   .solar:993)   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Email Folders  │    │  Email Movement  │    │ Content Extract │
│   (13 Business  │◀───│   via IMAP       │◀───│  (Subject/Body/ │
│   Categories)   │    │                  │    │   Sender/Date)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                                               │
         │                                               ▼
         │              ┌──────────────────┐    ┌─────────────────┐
         │              │   AI Categorizer │    │   HuggingFace   │
         └──────────────│   (OpenAI GPT    │◀───│   Sentiment     │
                        │   -3.5-turbo)    │    │   Analysis      │
                        └──────────────────┘    └─────────────────┘

🔄 Execution Modes:
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Manual Run    │  │  Daemon Mode    │  │  Continuous     │  │  macOS Launch   │
│  (One-time)     │  │  (Background)   │  │  Monitor        │  │     Agent       │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 📂 Predefined Categories

The system automatically sorts emails into these 13 business-focused folders:

| Category | Description | IMAP Folder |
|----------|-------------|-------------|
| **Client Communication** | Direct client correspondence | `INBOX.Client Communication` |
| **Completed & Archived** | Finished projects and archived items | `INBOX.Completed & Archived` |
| **Follow-Up Required** | Emails needing action or response | `INBOX.Follow-Up Required` |
| **General Inquiries** | General questions and information requests | `INBOX.General Inquiries` |
| **Invoices & Payments** | Financial documents and transactions | `INBOX.Invoices & Payments` |
| **Marketing & Promotions** | Promotional content and marketing materials | `INBOX.Marketing & Promotions` |
| **Pending & To Be Actioned** | Items waiting for action | `INBOX.Pending & To Be Actioned` |
| **Personal & Non-Business** | Personal emails and non-work related | `INBOX.Personal & Non-Business` |
| **Reports & Documents** | Reports, documentation, and file attachments | `INBOX.Reports & Documents` |
| **Spam & Unwanted** | Unwanted emails and potential spam | `INBOX.Spam & Unwanted` |
| **System & Notifications** | System alerts and automated notifications | `INBOX.System & Notifications` |
| **Urgent & Time-Sensitive** | High-priority and time-critical emails | `INBOX.Urgent & Time-Sensitive` |

## 🚀 Quick Start

### 🐳 Docker Deployment (Recommended)

**Prerequisites:**
- Docker and Docker Compose installed
- Your API keys (HuggingFace, OpenAI)
- Email server credentials

**Quick Docker Setup:**
```bash
# 1. Clone the repository
git clone https://github.com/jlwainwright/email-categorization.git
cd email-categorization

# 2. Copy and configure settings
cp config.ini.example config.ini
# Edit config.ini with your email and API credentials

# 3. Start the system
docker-compose up -d

# 4. Check logs
docker-compose logs -f email-categorizer

# 5. Test with dry run
docker-compose --profile dryrun up email-categorizer-dryrun
```

**Docker Management Commands:**
```bash
# Start continuous monitoring
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Run one-time categorization
docker-compose --profile manual up email-categorizer-manual

# Run dry run test
docker-compose --profile dryrun up email-categorizer-dryrun

# Start with monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d
```

### 🔧 Native Installation

### 1. Configuration Setup

**Email Server Configuration:**
```ini
[IMAP]
server = mail.sunlec.solar
port = 993
username = mia@sunlec.solar
password = your_password_here
```

**API Keys Configuration:**
```ini
[Hugging Face]
api_key = your_huggingface_api_key

[OpenAI]
api_key = your_openai_api_key
```

### 2. Install Dependencies
```bash
./setup.sh
```

### 3. Verify Folder Structure
```bash
python3 check_folders.py
```

### 4. Test with Dry Run
```bash
# Test with recent emails (safe preview mode)
python3 email_categorizer_dry_run.py ALL 5

# Test with unread emails only
python3 email_categorizer_dry_run.py UNSEEN 3
```

## 💻 Usage & Execution Modes

### 🔍 Dry Run Mode (Recommended First)
Preview what the system would do without moving any emails:

```bash
# Process 5 most recent emails (preview only)
python3 email_categorizer_dry_run.py ALL 5

# Process unread emails only (preview only)
python3 email_categorizer_dry_run.py UNSEEN

# Process recent emails (preview only)
python3 email_categorizer_dry_run.py RECENT 3
```

**Dry Run Output Example:**
```
📨 Processing Email 1/3
--------------------------------------------------
📋 Subject: RE: Project Update - Solar Installation
👤 From: client@example.com
📅 Date: Mon, 30 Jun 2025 09:06:47 +0200
📝 Body Preview: Hi Mia, Can we arrange the inspection...

🧠 Analyzing sentiment...
😊 Sentiment: NEUTRAL (Score: 0.50)

🎯 Categorizing email...
📁 Category: Client Communication

🔍 DRY RUN: Email would be moved to folder: INBOX.Client Communication
```

### 🔧 Production Modes

#### Option 1: Manual Execution (One-time)
```bash
./run_categorizer.sh
```
Processes all unread emails once and exits.

#### Option 2: Daemon Mode (Background Process)
```bash
# Start daemon
./daemon.sh start

# Check status
./daemon.sh status

# Stop daemon
./daemon.sh stop

# Restart daemon
./daemon.sh restart
```

#### Option 3: Continuous Monitoring
```bash
# Default 60-second intervals
python3 email_categorizer_continuous.py

# Custom 5-minute intervals
python3 email_categorizer_continuous.py 300
```

#### Option 4: macOS Launch Agent (Auto-start)
```bash
# Setup launch agent
./setup_launch_agent.sh

# Load and start
launchctl load ~/Library/LaunchAgents/com.sunlec.emailcategorizer.plist

# Check status
launchctl list | grep com.sunlec.emailcategorizer
```

#### Option 5: Cron Job (Scheduled)
```bash
# Edit crontab
crontab -e

# Run every 10 minutes
*/10 * * * * /path/to/email-categorization/run_categorizer.sh

# Run every hour
0 * * * * /path/to/email-categorization/run_categorizer.sh
```

### 🧪 Native Usage Helpers

```bash
# Install dependencies on managed environments (PEP 668)
make install-local

# Check IMAP folders safely (uses config.ini or env vars)
make check-folders-native

# Run a safe dry run against UNSEEN emails (uses config.ini or env vars)
make dryrun-native
```

### 🔐 Environment Variable Overrides

You can provide credentials via environment variables instead of `config.ini`:

```bash
export IMAP_SERVER="imap.example.com"
export IMAP_PORT=993
export IMAP_USERNAME="user@example.com"
export IMAP_PASSWORD="app-password"
export HUGGINGFACE_API_KEY="hf_xxx"
export OPENAI_API_KEY="sk-xxx"

# Then run
python3 check_folders.py
python3 email_categorizer_dry_run.py UNSEEN 3
```

These overrides apply to both `check_folders.py` and `email_categorizer_dry_run.py`.

## 🐳 Docker Deployment Guide

### Container Architecture

The system provides multiple deployment options through Docker:

| Service | Purpose | Profile | Default |
|---------|---------|---------|---------|
| **email-categorizer** | Continuous monitoring (5min intervals) | default | ✅ Auto-start |
| **email-categorizer-manual** | One-time execution | manual | Manual only |
| **email-categorizer-dryrun** | Safe testing mode | dryrun | Manual only |
| **prometheus** | Metrics collection | monitoring | Manual only |
| **grafana** | Monitoring dashboard | monitoring | Manual only |

### Docker Configuration

**Environment Variables:**
```bash
# Set in docker-compose.yml or .env file
TZ=Africa/Johannesburg          # Timezone
CHECK_INTERVAL=300              # Check interval in seconds
CATEGORIZER_MODE=continuous     # Mode: continuous, manual, dryrun
PYTHONUNBUFFERED=1             # Python output buffering
```

**Volume Mounts:**
```yaml
volumes:
  - ./config.ini:/app/config.ini:ro     # Read-only configuration
  - ./logs:/app/logs                    # Persistent log storage
  - categorizer-data:/app/data          # Application data
```

**Resource Limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'      # Maximum 1 CPU core
      memory: 512M     # Maximum 512MB RAM
    reservations:
      cpus: '0.25'     # Minimum 0.25 CPU
      memory: 128M     # Minimum 128MB RAM
```

### Production Deployment

**Option 1: Simple Continuous Mode**
```bash
# Start background email processing
docker-compose up -d

# Monitor progress
docker-compose logs -f email-categorizer
```

**Option 2: Scheduled Manual Runs**
```bash
# Create cron job for periodic execution
# Add to crontab: */30 * * * * cd /path/to/email-categorization && docker-compose --profile manual up email-categorizer-manual
```

**Option 3: Full Monitoring Stack**
```bash
# Start with Prometheus + Grafana monitoring
docker-compose --profile monitoring up -d

# Access Grafana dashboard
open http://localhost:3000
# Login: admin / emailcat_admin
```

### Container Management

**Health Checks:**
```bash
# Check container health
docker-compose ps

# View health status
docker inspect email-categorizer-main --format='{{.State.Health.Status}}'

# Manual health check
docker-compose exec email-categorizer python3 -c "import sys; sys.exit(0)"
```

**Log Management:**
```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs email-categorizer

# View last 100 lines
docker-compose logs --tail=100

# Follow logs with timestamps
docker-compose logs -f -t
```

**Troubleshooting:**
```bash
# Enter container for debugging
docker-compose exec email-categorizer bash

# Run manual categorization inside container
docker-compose exec email-categorizer python3 email_categorizer.py

# Check configuration
docker-compose exec email-categorizer cat config.ini

# Test IMAP connection
docker-compose exec email-categorizer python3 check_folders.py
```

### Security Considerations

**Container Security:**
- ✅ **Non-root user**: Runs as `emailcat` user (not root)
- ✅ **Read-only config**: Configuration mounted read-only
- ✅ **Minimal base image**: Uses Python slim image
- ✅ **No sensitive data**: API keys in mounted config only

**Network Security:**
```yaml
networks:
  emailcat-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16  # Isolated network
```

**Best Practices:**
- Mount `config.ini` as read-only volume
- Use Docker secrets for sensitive data in production
- Regular container updates: `docker-compose pull && docker-compose up -d`
- Monitor resource usage and set appropriate limits

### Performance Optimization

**Multi-stage Build:**
- Builder stage compiles dependencies
- Production stage only includes runtime
- ~50% smaller final image size

**Caching Strategy:**
```dockerfile
# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install -r requirements.txt
# Then copy application code
COPY . .
```

**Resource Monitoring:**
```bash
# Monitor resource usage
docker stats email-categorizer-main

# View container resource limits
docker inspect email-categorizer-main | grep -A 10 "Resources"
```

## 🔧 Technical Details

### Core Components

| Component | Description | Technology |
|-----------|-------------|------------|
| **email_categorizer.py** | Main categorization engine | Python 3.7+ |
| **email_categorizer_continuous.py** | Continuous monitoring wrapper | Python + Threading |
| **email_categorizer_dry_run.py** | Safe preview mode | Python + IMAP |
| **check_folders.py** | Folder verification utility | Python + IMAP |
| **config.ini** | Configuration file | INI format |

### API Integration

**HuggingFace Sentiment Analysis:**
- Model: `distilbert-base-uncased-finetuned-sst-2-english`
- Input limit: 1000 characters
- Output: Sentiment label (POSITIVE/NEGATIVE/NEUTRAL) + confidence score

**OpenAI Email Categorization:**
- Model: `gpt-3.5-turbo`
- Temperature: 0.1 (consistent results)
- Max tokens: 50
- Structured prompts with category validation

### Email Processing Pipeline

1. **Connection**: Secure IMAP4_SSL connection to mail server
2. **Authentication**: Login with username/password
3. **Email Retrieval**: Fetch unread emails from INBOX
4. **Content Extraction**: Parse multipart MIME messages
5. **Sentiment Analysis**: Analyze email content sentiment
6. **Categorization**: Determine appropriate folder using AI
7. **Email Movement**: Move email via IMAP COPY/STORE operations
8. **Logging**: Record all operations and errors

### Error Handling & Reliability

- **Connection Retry**: Graceful handling of network issues
- **API Fallbacks**: Default to "General Inquiries" on API failures
- **Encoding Support**: Handles various email encodings (UTF-8, Latin-1, etc.)
- **Malformed Email**: Graceful handling of corrupted email data
- **Rate Limiting**: Built-in delays to respect API limits

## 📊 Monitoring & Logging

### Log Files

| Log File | Purpose | Location |
|----------|---------|----------|
| `categorization.log` | Manual run history | Current directory |
| `categorizer.log` | Launch agent output | Current directory |
| `categorizer_error.log` | Launch agent errors | Current directory |

### Health Checks

```bash
# Check daemon status
./daemon.sh status

# Check launch agent
launchctl list | grep com.sunlec.emailcategorizer

# View recent logs
tail -f categorization.log

# Check IMAP connection
python3 check_folders.py
```

## 🔒 Security Considerations

### Data Security
- **Email Content**: Sent to external APIs (HuggingFace, OpenAI)
- **Credentials**: Stored in plaintext `config.ini`
- **Transport**: IMAP uses SSL/TLS encryption
- **API Keys**: Stored locally, not transmitted unnecessarily

### Recommendations
- Use app-specific passwords for email accounts
- Regularly rotate API keys
- Monitor API usage and costs
- Consider encrypting the config file
- Review logs for suspicious activity

## 🛠️ Troubleshooting

### Common Issues

**Authentication Failed:**
```bash
Error: b'[AUTHENTICATIONFAILED] Invalid credentials'
```
- **Solution**: Use app-specific password for email account
- **Gmail**: Enable 2FA and generate App Password
- **Other providers**: Check IMAP settings and credentials

**Missing Folders:**
```bash
Error: Folder 'INBOX.Client Communication' not found
```
- **Solution**: Create missing folders in email client
- **Check**: Run `python3 check_folders.py` to verify all folders exist

**API Rate Limits:**
```bash
Error: Rate limit exceeded for OpenAI API
```
- **Solution**: Increase intervals between runs
- **Monitor**: Check API usage in provider dashboards

**Connection Timeouts:**
```bash
Error: IMAP connection timeout
```
- **Solution**: Check network connectivity and server settings
- **Verify**: Test with email client (Outlook, Mail app)

### Debug Mode

Enable detailed logging by modifying the scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔧 Customization

### Adding New Categories

1. **Edit Categories List:**
```python
CATEGORIES = [
    "Client Communication",
    "New Category Name",  # Add here
    # ... existing categories
]
```

2. **Create Email Folder**: Create corresponding folder in email client

3. **Update Documentation**: Add to README and folder verification

### Adjusting AI Behavior

**Sentiment Analysis Sensitivity:**
```python
# Truncate text length for faster processing
text = text[:500]  # Reduce from 1000 to 500 characters
```

**Categorization Temperature:**
```python
data = {
    "temperature": 0.05,  # More consistent (was 0.1)
    # or
    "temperature": 0.3,   # More creative (was 0.1)
}
```

### Custom Email Filters

Modify the search criteria in the main script:
```python
# Current: Only unread emails
result, data = mail.search(None, 'UNSEEN')

# Custom: Emails from last 7 days
result, data = mail.search(None, 'SINCE', '01-Jan-2025')

# Custom: Emails with specific subject
result, data = mail.search(None, 'SUBJECT', 'Invoice')
```

## 📋 Requirements

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: macOS, Linux, Windows
- **Network**: Internet connection for API calls
- **Email**: IMAP-enabled email account

### Python Dependencies
```
requests>=2.25.1
configparser>=5.0.0
imaplib (built-in)
email (built-in)
ssl (built-in)
```

### API Requirements
- **HuggingFace Account**: Free tier available
- **OpenAI Account**: Pay-per-use pricing
- **IMAP Email Account**: Gmail, Outlook, or custom server

## 🚦 Performance & Limitations

### Processing Speed
- **Email Processing**: ~2-3 seconds per email
- **API Latency**: 1-2 seconds per API call
- **IMAP Operations**: < 1 second per email move

### Rate Limits
- **HuggingFace**: 1000 requests/month (free tier)
- **OpenAI**: Varies by account tier
- **IMAP**: Server-dependent

### Scalability
- **Recommended**: < 100 emails per batch
- **Maximum**: Limited by API quotas
- **Optimization**: Batch processing available

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review log files for error details
3. Verify API keys and email configuration
4. Test with dry run mode first

## 🔄 Changelog

### v1.2.0 (Current)
- ✅ Added dry run mode for safe testing
- ✅ Fixed IMAP server configuration (mail.sunlec.solar)
- ✅ Added flexible email filtering (ALL/UNSEEN/RECENT)
- ✅ Enhanced folder verification system
- ✅ Improved error handling and logging

### v1.1.0
- ✅ Added continuous monitoring mode
- ✅ macOS Launch Agent support
- ✅ Daemon mode for background processing
- ✅ Enhanced email parsing and encoding support

### v1.0.0
- ✅ Initial release with basic email categorization
- ✅ HuggingFace sentiment analysis integration
- ✅ OpenAI GPT-3.5-turbo categorization
- ✅ IMAP email server support