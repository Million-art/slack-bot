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
slack-sdk
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
pandas
openpyxl
python-dotenv
gunicorn
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
3. Give it a name like "slack-bot-service-account"
4. Grant the following roles:
   - **Editor** (for full access to Drive and Sheets)
   - **Service Account Token Creator** (if using OAuth2)
5. Click "Create and Continue"
6. Click "Done"
7. Click on the created service account
8. Go to "Keys" tab
9. Click "Add Key" > "Create new key" > "JSON"
10. Download the JSON file

#### Set Up OAuth2 (Recommended for Production)
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `http://localhost:5000/oauth2callback` (for local development)
   - `https://your-railway-app.railway.app/oauth2callback` (for production)
5. Download the client configuration file

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
2. Enable Interactivity
3. Set Request URL to: `https://your-railway-app.railway.app/api/interactions/command`

#### Configure Slash Commands
1. Go to "Slash Commands"
2. Create command:
   - **Command**: `/start`
   - **Request URL**: `https://your-railway-app.railway.app/api/command`
   - **Short Description**: Start the data manager bot

### 5. Environment Configuration

#### Local Development
Create a `.env` file in the project root:
```env
# Slack Configuration
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_BOT_TOKEN=xoxb-your_bot_token

# Google Configuration
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"}

GOOGLE_OAUTH_CREDENTIALS={"web":{"client_id":"your-oauth-client-id.apps.googleusercontent.com","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"your-client-secret","redirect_uris":["http://localhost:5000/oauth2callback","https://your-railway-app.railway.app/oauth2callback"]}}

# Optional Configuration
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
ALLOWED_USER_IDS=user1,user2,user3
FLASK_DEBUG=True
```

#### Railway Production Deployment
Set these environment variables in Railway dashboard:

**Required Variables:**
- `SLACK_SIGNING_SECRET`: Your Slack app signing secret
- `SLACK_BOT_TOKEN`: Your Slack bot token (starts with `xoxb-`)
- `GOOGLE_CREDENTIALS`: Full JSON content of your service account key (as a single line)
- `GOOGLE_OAUTH_CREDENTIALS`: Full JSON content of your OAuth2 client configuration (as a single line)

**Optional Variables:**
- `GOOGLE_DRIVE_FOLDER_ID`: Specific folder ID to restrict access
- `ALLOWED_USER_IDS`: Comma-separated list of Slack user IDs
- `PORT`: Railway sets this automatically
- `FLASK_DEBUG`: Set to `False` for production

## Railway Deployment

### 1. Prepare Your Repository
Ensure your repository contains:
- `requirements.txt` ✅
- `Procfile` ✅
- `runtime.txt` ✅
- All application files ✅

### 2. Deploy to Railway
1. Go to [Railway](https://railway.app/)
2. Click "New Project" > "Deploy from GitHub repo"
3. Connect your GitHub account
4. Select your repository
5. Railway will automatically detect the Python app

### 3. Configure Environment Variables
1. In your Railway project dashboard, go to "Variables"
2. Add all required environment variables (see above)
3. **Important**: For `GOOGLE_CREDENTIALS` and `GOOGLE_OAUTH_CREDENTIALS`, paste the entire JSON content as a single line

### 4. Update Slack App URLs
1. Go to your Slack app settings
2. Update the Request URLs to use your Railway domain:
   - Interactivity: `https://your-app.railway.app/api/interactions/command`
   - Slash Commands: `https://your-app.railway.app/api/command`

### 5. Install the App
1. Go to "OAuth & Permissions" in your Slack app
2. Click "Install to Workspace"
3. Copy the Bot User OAuth Token (starts with `xoxb-`)
4. Add it to Railway environment variables

## Usage

### Starting the Bot
1. **Local Development**: `python run.py`
2. **Production**: Railway automatically starts the app

### Using the Bot
1. In Slack, type `/start` to open the main menu
2. Choose from available options:
   - **Google Sheets**: List, create, read, update sheets
   - **Excel Files**: List, create, read, update Excel files
   - **CSV Files**: List, create, read, update CSV files

### File Operations
- **List Files**: Browse available files by type
- **Create File**: Create new files with templates
- **Get Data**: View formatted spreadsheet data
- **Update Cell**: Modify specific cells with row/column targeting
- **Refresh Data**: Get latest data from source files

## Architecture

### Core Components
- **Flask App**: Web framework for handling HTTP requests
- **Slack SDK**: Official Slack API client
- **Google APIs**: Sheets and Drive API integration
- **Pandas**: Data manipulation for Excel/CSV files
- **Gunicorn**: WSGI server for production deployment

### File Structure
```
slack-bot/
├── app/
│   ├── core/           # Core functionality (auth, logging, etc.)
│   ├── handlers/       # Request handlers
│   ├── services/       # Business logic (Google, Slack APIs)
│   └── utils/          # Utility functions
├── requirements.txt    # Python dependencies
├── Procfile          # Railway deployment configuration
├── runtime.txt       # Python version specification
└── README.md         # This file
```

## Security

### Authentication
- **Slack Verification**: All requests are verified using Slack's signing secret
- **Google OAuth2**: Secure authentication with Google APIs
- **User Authorization**: Optional user ID restrictions

### Data Protection
- **Environment Variables**: Sensitive data stored securely
- **Rate Limiting**: Built-in protection against abuse
- **Error Handling**: No sensitive data in error messages

## Troubleshooting

### Common Issues

#### Google API Errors
**Error**: "Invalid JWT Signature"
- **Solution**: Ensure `GOOGLE_CREDENTIALS` contains the complete JSON content
- **Check**: Verify the service account has proper permissions

**Error**: "API connection failed"
- **Solution**: Enable Google Sheets API and Google Drive API in Google Cloud Console
- **Check**: Verify the service account has Editor role

#### Slack Integration Issues
**Error**: "dispatch_failed"
- **Solution**: Check that `SLACK_BOT_TOKEN` is correct and the app is installed
- **Check**: Verify the bot has required scopes

**Error**: "invalid_arguments"
- **Solution**: Ensure Request URLs are correctly set in Slack app settings
- **Check**: Verify the Railway app is running and accessible

#### Railway Deployment Issues
**Error**: "ModuleNotFoundError: No module named 'dotenv'"
- **Solution**: All dependencies are in `requirements.txt` and should install automatically
- **Check**: Verify `requirements.txt` is in the repository root

**Error**: "Google credentials issue: No Google credentials found"
- **Solution**: Set `GOOGLE_CREDENTIALS` environment variable in Railway
- **Check**: Ensure the JSON content is pasted as a single line

**Error**: "Invalid JWT Signature" on Railway
- **Solution**: The JSON content in environment variables must be properly escaped
- **Check**: Use Railway's web interface to set variables, not command line

### Environment Variable Format for Railway
For Railway deployment, environment variables should be set as follows:

**GOOGLE_CREDENTIALS** (single line):
```
{"type":"service_account","project_id":"your-project","private_key_id":"abc123","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n","client_email":"your-service@your-project.iam.gserviceaccount.com","client_id":"123456789","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/your-service%40your-project.iam.gserviceaccount.com"}
```

**GOOGLE_OAUTH_CREDENTIALS** (single line):
```
{"web":{"client_id":"your-client-id.apps.googleusercontent.com","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"your-client-secret","redirect_uris":["http://localhost:5000/oauth2callback","https://your-app.railway.app/oauth2callback"]}}
```

### Development vs Production
- **Local**: Uses `.env` file and file-based credentials
- **Production**: Uses Railway environment variables and OAuth2 token caching
- **Testing**: Use Railway's built-in logging to debug issues

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Railway logs for detailed error messages
3. Verify all environment variables are correctly set
4. Ensure Google Cloud APIs are enabled and properly configured

## License

This project is licensed under the MIT License. 
