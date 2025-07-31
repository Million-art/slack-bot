# Slack Data Manager Bot

A comprehensive Slack bot for managing Google Sheets, Excel files, and CSV files stored on Google Drive. This bot provides Create, Read, and Update operations for spreadsheet data directly within Slack.

## Features

### File Management
- **Google Sheets**: Full CRUD operations with real-time updates
- **Excel Files (.xlsx)**: Read, update, and create new Excel files
- **CSV Files**: Read, update, and create new CSV files
- **File Listing**: Browse available files by type
- **File Creation**: Create new files with templates

### Data Operations
- **Read Data**: View spreadsheet data with formatted display
- **Update Cells**: Modify individual cells with row/column targeting
- **Refresh Data**: Real-time data refresh from source files
- **Header Protection**: Automatic warnings for Excel/CSV headers

### User Experience
- **Interactive Modals**: User-friendly forms for data entry
- **Real-time Updates**: Immediate feedback on operations
- **Error Handling**: Comprehensive error messages and solutions
- **Rate Limiting**: Built-in protection against API abuse

## Prerequisites

### Required Software
- Python 3.8 or higher
- Google Cloud Platform account
- Slack workspace with admin permissions

### Python Dependencies
```
flask
slack-bolt
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
pandas
openpyxl
python-dotenv
```

## Installation

### 1. Clone the Repository
```bash
git clone (https://github.com/Million-art/slack-bot.git)
cd slack-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Google Cloud Platform

#### Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

#### Create Service Account
1. Navigate to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Download the JSON credentials file
4. Place the file in the project root as `credentials.json`

#### Set Up OAuth2 (Optional)
1. Go to "APIs & Services" > "Credentials"
2. Create OAuth 2.0 Client ID
3. Download the client configuration file
4. Place as `oauth_credentials.json`

### 4. Configure Slack App

#### Create Slack App
1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" > "From scratch"
3. Configure the following:
   - **App Name**: Data Manager Bot
   - **Workspace**: Select your workspace

#### Configure OAuth & Permissions
Add the following Bot Token Scopes:
- `chat:write`
- `chat:write.public`
- `commands`
- `files:read`
- `im:history`
- `im:read`
- `im:write`

#### Configure Interactivity & Shortcuts
1. Go to "Interactivity & Shortcuts"
2. Set Request URL to: `https://your-domain.com/slack/interactions/command`
3. Enable Interactivity

#### Configure Slash Commands
Create the following slash command:
- **Command**: `/start`
- **Request URL**: `https://your-domain.com/api/command`
- **Short Description**: Manage Google Sheets, Excel, and CSV files

### 5. Environment Configuration

Create a `.env` file in the project root:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# Google Configuration
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_OAUTH_CREDENTIALS_FILE=oauth_credentials.json
GOOGLE_FOLDER_ID=your-google-drive-folder-id

# Application Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

## Usage

### Starting the Application

#### Development Mode
```bash
python run.py
```

#### Production Mode
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Slack Commands

#### Main Command
```
/datamanager
```
Opens the main menu with options to:
- List available files
- Create new files
- View file data
- Update file data

#### Available Actions

**File Management**
- List Google Sheets
- List Excel Files
- List CSV Files
- Create new files

**Data Operations**
- View file data
- Update cell values
- Refresh data
- Open update modal

### File Type Support

#### Google Sheets
- **Read**: View sheet data with headers
- **Update**: Modify individual cells
- **Create**: New sheets with templates
- **Headers**: Editable (no restrictions)

#### Excel Files (.xlsx)
- **Read**: View Excel data with headers
- **Update**: Modify individual cells
- **Create**: New Excel files with templates
- **Headers**: Protected (warning displayed)
- **Row Indexing**: Starts from row 2 (header is row 1)

#### CSV Files
- **Read**: View CSV data with headers
- **Update**: Modify individual cells
- **Create**: New CSV files with templates
- **Headers**: Protected (warning displayed)
- **Row Indexing**: Starts from row 2 (header is row 1)

## Architecture

### Project Structure
```
slack-bot/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── cache.py
│   │   └── rate_limiter.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── command_handler.py
│   └── services/
│       ├── __init__.py
│       ├── google_service.py
│       └── slack_service.py
├── requirements.txt
├── run.py
├── credentials.json
├── oauth_credentials.json
└── .env
```

### Core Components

#### Google Service (`app/services/google_service.py`)
- Handles Google Sheets API interactions
- Manages Google Drive file operations
- Processes Excel and CSV files using pandas
- Implements file type detection and routing

#### Slack Service (`app/services/slack_service.py`)
- Manages Slack API interactions
- Builds interactive message blocks
- Handles modal creation and responses
- Formats data for display

#### Command Handler (`app/handlers/command_handler.py`)
- Processes Slack slash commands
- Handles interactive button clicks
- Manages modal submissions
- Routes operations to appropriate services

### Data Flow

1. **User Interaction**: User sends slash command or clicks button
2. **Request Processing**: Command handler validates and routes request
3. **Service Layer**: Google service performs file operations
4. **Response Formatting**: Slack service formats response
5. **User Feedback**: Formatted response sent to user

## Configuration

### Rate Limiting
- **Default**: 100 requests per hour per user
- **Configurable**: Via environment variables
- **Protection**: Prevents API abuse

### Caching
- **In-memory**: Fast response times
- **Session-based**: User-specific data
- **Configurable**: Cache duration and size

### Error Handling
- **Comprehensive**: All operations wrapped in try-catch
- **User-friendly**: Clear error messages
- **Logging**: Detailed logs for debugging
- **Recovery**: Automatic retry mechanisms

## Security

### Authentication
- **Slack Verification**: Request signature validation
- **Google OAuth**: Secure API access
- **Service Account**: Fallback authentication

### Data Protection
- **Environment Variables**: Sensitive data protection
- **Input Validation**: All user inputs sanitized
- **Rate Limiting**: Protection against abuse
- **Error Sanitization**: No sensitive data in error messages

## Troubleshooting

### Common Issues

#### Google API Errors
**Problem**: "Google credentials issue"
**Solution**: 
1. Verify credentials.json file exists
2. Check service account permissions
3. Ensure APIs are enabled in Google Cloud Console

#### Slack Integration Issues
**Problem**: "Slack verification failed"
**Solution**:
1. Verify SLACK_SIGNING_SECRET in .env
2. Check Request URL configuration
3. Ensure bot token has correct scopes

#### File Access Issues
**Problem**: "File not found" or "Permission denied"
**Solution**:
1. Share Google Drive folder with service account
2. Verify file permissions
3. Check GOOGLE_FOLDER_ID configuration

#### Excel File Errors
**Problem**: "openpyxl does not support file format"
**Solution**:
1. Open file in Microsoft Excel
2. Save as .xlsx format
3. Re-upload to Google Drive

### Debug Mode
Enable debug logging by setting:
```env
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

## Development

### Adding New Features

#### New File Type Support
1. Add file type detection in `google_service.py`
2. Implement read/write methods
3. Add UI components in `slack_service.py`
4. Update command handler routing

#### New Commands
1. Add command handler function
2. Register route in `command_handler.py`
3. Add UI components in `slack_service.py`
4. Update main menu integration

### Testing
```bash
# Run syntax check
python -m py_compile app/handlers/command_handler.py

# Test imports
python -c "import app.services.google_service; import app.services.slack_service"

# Run application
python run.py
```

## Deployment

### Production Checklist
- [ ] Set FLASK_ENV=production
- [ ] Configure proper SECRET_KEY
- [ ] Set up HTTPS endpoints
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Test all file types
- [ ] Verify rate limiting
- [ ] Check error handling

### Environment Variables
```env
# Required
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_FOLDER_ID=your-folder-id

# Optional
FLASK_ENV=production
SECRET_KEY=your-secret-key
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
LOG_LEVEL=INFO
```

## Support

### Getting Help
1. Check the troubleshooting section
2. Review application logs
3. Verify configuration settings
4. Test with different file types

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request


## Changelog

### Version 1.0.0
- Initial release
- Google Sheets CRUD operations
- Excel file support with pandas
- CSV file support
- Interactive Slack interface
- Rate limiting and caching
- Comprehensive error handling 
