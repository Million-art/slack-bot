# Slack Data Manager Bot

A professional Slack bot for managing Google Sheets, CSV, and Excel files with comprehensive error handling and user management.

## Features

- **Multi-format Support**: Google Sheets, CSV, and Excel files
- **Interactive UI**: Buttons, modals, and slash commands
- **File Management**: Read, write, and create new files
- **Security**: User authentication, rate limiting, and audit logging
- **Error Handling**: Comprehensive error management with user feedback
- **Scalable**: Simple and efficient data processing

## Architecture

```
slack-bot/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── cache.py
│   │   ├── logger.py
│   │   └── rate_limiter.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── google_service.py
│   │   ├── slack_service.py
│   │   └── file_service.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── command_handler.py
│   │   ├── interactivity_handler.py
│   │   └── event_handler.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── formatters.py
│   │   └── helpers.py

├── tests/
├── logs/
├── credentials/
├── requirements.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Slack Configuration
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_BOT_TOKEN=xoxb-your-bot-token
ALLOWED_USER_IDS=U1234567890,U0987654321

# Google Configuration
GOOGLE_SHEET_ID=your_default_sheet_id
GOOGLE_CREDENTIALS_FILE=credentials/service-account.json



# Logging
LOG_LEVEL=INFO
```

### 2. Google Service Account

1. Create a Google Cloud Project
2. Enable Google Sheets and Drive APIs
3. Create a service account
4. Download credentials to `credentials/service-account.json`
5. Share your Google Sheets with the service account email

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

#### Development
```bash
python run.py
```

#### Production
```bash
python run.py
```

#### Using Docker
```bash
docker-compose up -d
```



#### With Docker
```bash
docker-compose up -d
```

## Usage

### Slash Commands

- `/start` - Show main menu
- `/getdata source=sheet range=A1:B10` - Get sheet data
- `/getdata source=csv file=data.csv range=A1:B10` - Get CSV data
- `/getdata source=excel file=report.xlsx sheet=Sheet1 range=A1:B10` - Get Excel data
- `/writedata source=sheet row=1 col=A value=Hello` - Write to sheet
- `/writedata source=csv file=data.csv row=1 col=A value=Hello` - Write to CSV
- `/writedata source=excel file=report.xlsx sheet=Sheet1 row=1 col=A value=Hello` - Write to Excel

### Interactive Features

- **Get Data**: Retrieve data from any supported format
- **Write Data**: Update cells in existing files
- **Create New File**: Generate new files with templates
- **Refresh**: Update displayed data
- **Export**: Download data in different formats

## Security Features

- **User Authentication**: Whitelist-based access control
- **Request Verification**: Slack signature validation
- **Rate Limiting**: API call throttling
- **Input Sanitization**: XSS and injection protection
- **Audit Logging**: Complete operation tracking
- **Error Handling**: Graceful failure management

## Monitoring

- **Structured Logging**: JSON-formatted logs
- **Health Checks**: Application status monitoring
- **Performance Metrics**: Response time tracking

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
flake8 app/
black app/
```

### Database Migrations
```bash
# Simple in-memory cache (no external dependencies)
```

## Deployment

### Docker Deployment
```bash
docker build -t slack-data-bot .
docker run -p 5000:5000 --env-file .env slack-data-bot
```

### Kubernetes Deployment
```yaml
# See k8s/ directory for manifests
```

## Support

For issues and feature requests, please create an issue in the repository.

## License

MIT License - see LICENSE file for details. 