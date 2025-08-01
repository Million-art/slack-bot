"""
Google Services for Sheets, Drive, and Excel file operations.
"""

import os
import tempfile
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import DefaultCredentialsError
import pickle
import csv

# Import pandas for Excel reading
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.error("pandas not available - Excel reading will not work")

logger = logging.getLogger(__name__)

# OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

class GoogleService:
    """Service for Google Sheets, Drive, Excel, and CSV operations."""
    
    def __init__(self):
        """Initialize Google service with credentials."""
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.oauth_credentials_file = os.getenv('GOOGLE_OAUTH_CREDENTIALS_FILE', 'oauth_credentials.json')
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        self.drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        # Initialize Google API clients
        self._init_google_clients()
    
    def _get_credentials_from_env(self):
        """Get service account credentials from environment variable."""
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        if not credentials_json:
            logger.warning("GOOGLE_CREDENTIALS environment variable not found")
            return None
            
        try:
            # Parse JSON from environment variable
            credentials_dict = json.loads(credentials_json)
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in credentials_dict]
            
            if missing_fields:
                logger.error(f"Missing required fields in credentials: {', '.join(missing_fields)}")
                return None
            
            # Validate that it's a service account
            if credentials_dict.get('type') != 'service_account':
                logger.error("Credentials are not for a service account")
                return None
            
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict, 
                scopes=SCOPES
            )
            
            logger.info(f"Successfully loaded credentials for service account: {credentials.service_account_email}")
            return credentials
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GOOGLE_CREDENTIALS JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create credentials from environment: {e}")
            return None
    
    def _get_oauth_credentials_from_env(self):
        """Get OAuth credentials from environment variable."""
        oauth_json = os.getenv('GOOGLE_OAUTH_CREDENTIALS')
        if oauth_json:
            try:
                oauth_dict = json.loads(oauth_json)
                return oauth_dict
            except Exception as e:
                logger.error(f"Failed to parse GOOGLE_OAUTH_CREDENTIALS from environment: {e}")
                return None
        return None
    
    def _get_oauth_credentials(self):
        """Get OAuth2 credentials with automatic token refresh."""
        creds = None
        
        # Check if we have a token file
        token_file = 'token.pickle'
        if os.path.exists(token_file):
            try:
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded OAuth2 token from file")
            except Exception as e:
                logger.warning(f"Failed to load OAuth2 token: {e}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed OAuth2 token")
                except Exception as e:
                    logger.warning(f"Failed to refresh OAuth2 token: {e}")
                    creds = None
            
            if not creds:
                # Try to get OAuth credentials from environment first
                oauth_dict = self._get_oauth_credentials_from_env()
                if oauth_dict:
                    try:
                        flow = InstalledAppFlow.from_client_secrets_dict(oauth_dict, SCOPES)
                        creds = flow.run_local_server(port=0)
                        logger.info("Created new OAuth2 credentials from environment")
                    except Exception as e:
                        logger.error(f"Failed to create OAuth2 credentials from environment: {e}")
                        creds = None
                
                if not creds:
                    logger.info("OAuth credentials not found in environment, falling back to service account")
                    return None
            
            # Save the credentials for next run
            if creds:
                try:
                    with open(token_file, 'wb') as token:
                        pickle.dump(creds, token)
                    logger.info("Saved OAuth2 token to file")
                except Exception as e:
                    logger.warning(f"Failed to save OAuth2 token: {e}")
        
        return creds
    
    def check_credentials(self) -> Dict[str, Any]:
        """
        Check if Google credentials are properly configured.
        
        Returns:
            Dict[str, Any]: Status and details about credentials
        """
        try:
            # Try to get credentials from environment first
            credentials = self._get_credentials_from_env()
            if credentials:
                # Test API connection with environment credentials
                try:
                    test_service = build('drive', 'v3', credentials=credentials)
                    test_service.files().list(pageSize=1).execute()
                    
                    # Get project info from credentials
                    project_id = credentials.service_account_email.split('@')[1].split('.')[0] if credentials.service_account_email else 'Unknown'
                    
                    return {
                        'status': 'valid',
                        'message': "Google credentials from environment are properly configured and working.",
                        'project_id': project_id,
                        'client_email': credentials.service_account_email or 'Unknown'
                    }
                except Exception as e:
                    return {
                        'status': 'api_error',
                        'error': f"API connection failed with environment credentials: {str(e)}",
                        'solution': "Please check your Google Cloud API permissions and service account setup.",
                        'setup_steps': [
                            "1. Verify the GOOGLE_CREDENTIALS environment variable is set correctly",
                            "2. Ensure the service account has proper API permissions",
                            "3. Check that Google Sheets and Drive APIs are enabled"
                        ]
                    }
            
            # No environment credentials found
            return {
                'status': 'missing_credentials',
                'error': "No Google credentials found in environment",
                'solution': "Please set GOOGLE_CREDENTIALS environment variable with your JSON content.",
                'setup_steps': [
                    "1. Set GOOGLE_CREDENTIALS environment variable with your JSON content",
                    "2. Ensure Google Sheets API and Google Drive API are enabled",
                    "3. Verify the service account has proper permissions"
                ]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Error checking credentials: {str(e)}",
                'solution': "Please verify your Google credentials configuration.",
                'setup_steps': [
                    "1. Check the GOOGLE_CREDENTIALS environment variable format",
                    "2. Ensure the JSON content is valid and complete",
                    "3. Verify the service account has proper permissions"
                ]
            }
    
    def _init_google_clients(self):
        """Initialize Google API clients."""
        try:
            # Try OAuth2 first
            oauth_creds = self._get_oauth_credentials()
            if oauth_creds:
                # Use OAuth2 credentials
                self.sheets_service = build('sheets', 'v4', credentials=oauth_creds)
                self.drive_service = build('drive', 'v3', credentials=oauth_creds)
                logger.info("Google API clients initialized with OAuth2")
                return
            
            # Fall back to service account
            logger.info("OAuth2 not available, using service account")
            
            # Check credentials first
            cred_status = self.check_credentials()
            if cred_status['status'] != 'valid':
                raise Exception(f"Google credentials issue: {cred_status['error']}")
            
            # Define scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file'
            ]
            
            # Get credentials from environment
            credentials = self._get_credentials_from_env()
            
            if not credentials:
                raise Exception("No valid Google credentials found in environment. Please set GOOGLE_CREDENTIALS environment variable.")
            
            # Build API clients
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            
            logger.info("Google API clients initialized with service account")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google API clients: {e}")
            raise
    
    def read_sheet_data(self, sheet_id: str = None, range_name: str = "A1:Z10") -> List[List[str]]:
        """
        Read data from Google Sheets.
        
        Args:
            sheet_id (str, optional): Sheet ID, uses default if not provided
            range_name (str): Range to read (e.g., "A1:B10")
            
        Returns:
            List[List[str]]: Sheet data
        """
        try:
            sheet_id = sheet_id or self.sheet_id
            if not sheet_id:
                raise ValueError("Sheet ID is required")
            
            # Validate range format
            self._validate_range(range_name)
            
            # Get data from sheet
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id, 
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.info(f"Read {len(values)} rows from sheet {sheet_id}")
            
            return values
            
        except Exception as e:
            logger.error(f"Error reading sheet data: {e}")
            raise
    
    def write_sheet_data(self, sheet_id: str = None, range_name: str = None, 
                        values: List[List[str]] = None, value: str = None) -> bool:
        """
        Write data to Google Sheets.
        
        Args:
            sheet_id (str, optional): Sheet ID, uses default if not provided
            range_name (str): Range to write to (e.g., "A1")
            values (List[List[str]], optional): 2D array of values
            value (str, optional): Single value to write
            
        Returns:
            bool: True if successful
        """
        try:
            sheet_id = sheet_id or self.sheet_id
            if not sheet_id:
                raise ValueError("Sheet ID is required")
            
            if not range_name:
                raise ValueError("Range is required")
            
            # Validate range format
            self._validate_range(range_name)
            
            # Prepare data
            if value is not None:
                data = [[value]]
            elif values is not None:
                data = values
            else:
                raise ValueError("Either value or values must be provided")
            
            # Write data
            body = {'values': data}
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Wrote data to sheet {sheet_id} at range {range_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing sheet data: {e}")
            raise
    
    def write_excel_data(self, file_id: str, row: int, col: str, value: str) -> bool:
        """
        Write data to Excel file.
        
        Args:
            file_id (str): Excel file ID
            row (int): Row number (1-based)
            col (str): Column letter (A, B, C, etc.)
            value (str): Value to write
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Starting Excel write: file_id={file_id}, row={row}, col={col}, value={value}")
            
            if not PANDAS_AVAILABLE:
                raise ValueError("pandas is not available - cannot write Excel files")
            
            # Download current file
            logger.info(f"Downloading Excel file: {file_id}")
            local_path = self._download_drive_file(file_id)
            logger.info(f"Downloaded to: {local_path}")
            
            # Read current data with proper handling of empty cells
            logger.info(f"Reading Excel file with pandas")
            df = pd.read_excel(local_path, keep_default_na=False, na_values=[''])
            logger.info(f"Read DataFrame with shape: {df.shape}")
            
            # Convert column letter to index
            col_idx = ord(col.upper()) - ord('A')
            logger.info(f"Converting column {col} to index {col_idx}")
            
            # Update the cell (pandas uses 0-based indexing)
            logger.info(f"Updating cell at row {row-1}, col {col_idx} with value '{value}'")
            
            # Ensure DataFrame has enough rows and columns
            logger.info(f"Ensuring DataFrame has sufficient size")
            max_rows_needed = max(row, len(df))
            max_cols_needed = max(col_idx + 1, len(df.columns))
            
            # Extend DataFrame if needed
            if len(df) < max_rows_needed:
                logger.info(f"Extending DataFrame rows from {len(df)} to {max_rows_needed}")
                # Create new rows with proper data types
                new_rows_data = []
                for i in range(len(df), max_rows_needed):
                    new_row = [''] * len(df.columns)
                    new_rows_data.append(new_row)
                
                new_df = pd.DataFrame(new_rows_data, columns=df.columns)
                df = pd.concat([df, new_df], ignore_index=True)
            
            if len(df.columns) < max_cols_needed:
                logger.info(f"Extending DataFrame columns from {len(df.columns)} to {max_cols_needed}")
                for i in range(len(df.columns), max_cols_needed):
                    col_name = f'Column_{chr(65 + i)}'  # A, B, C, etc.
                    df[col_name] = ''
            
            # Update the cell
            df.iloc[row - 1, col_idx] = value
            logger.info(f"Successfully updated cell - final shape: {df.shape}")
            
            # Clean up NaN values and ensure proper data types
            df = df.fillna('')
            logger.info(f"Cleaned up NaN values")
            
            # Write back to file
            logger.info(f"Writing DataFrame back to file: {local_path}")
            with pd.ExcelWriter(local_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            logger.info(f"Successfully wrote Excel file")
            
            # Upload updated file
            logger.info(f"Uploading updated file to Google Drive")
            media = MediaFileUpload(local_path, 
                                  mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                  resumable=True)
            
            self.drive_service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            logger.info(f"Successfully uploaded to Google Drive")
            
            # Clean up - add delay and error handling for Windows file locking
            try:
                import time
                time.sleep(0.1)  # Small delay to ensure file is released
                os.unlink(local_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not delete temporary file {local_path}: {e}")
                # Try again after a longer delay
                try:
                    time.sleep(1)
                    os.unlink(local_path)
                except (OSError, PermissionError) as e2:
                    logger.warning(f"Still could not delete temporary file {local_path}: {e2}")
                    # File will be cleaned up by system later
            
            logger.info(f"Updated Excel file {file_id} at {col}{row}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing to Excel file: {e}")
            raise
    
    def write_csv_data(self, file_id: str, row: int, col: int, value: str) -> bool:
        """
        Write data to CSV file.
        
        Args:
            file_id (str): CSV file ID
            row (int): Row number (1-based)
            col (int): Column number (1-based)
            value (str): Value to write
            
        Returns:
            bool: True if successful
        """
        try:
            # Download current file
            local_path = self._download_drive_file(file_id)
            
            # Read current data
            data = []
            with open(local_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)
            
            # Update the cell (convert to 0-based indexing)
            row_idx = row - 1
            col_idx = col - 1
            
            # Extend data if needed
            while len(data) <= row_idx:
                data.append([''] * max(len(data[0]) if data else 1, col_idx + 1))
            
            for i in range(len(data)):
                while len(data[i]) <= col_idx:
                    data[i].append('')
            
            # Update the cell
            data[row_idx][col_idx] = value
            
            # Write back to file
            with open(local_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(data)
            
            # Upload updated file
            media = MediaFileUpload(local_path, 
                                  mimetype='text/csv',
                                  resumable=True)
            
            self.drive_service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            
            # Clean up - add delay and error handling for Windows file locking
            try:
                import time
                time.sleep(0.1)  # Small delay to ensure file is released
                os.unlink(local_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not delete temporary file {local_path}: {e}")
                # Try again after a longer delay
                try:
                    time.sleep(1)
                    os.unlink(local_path)
                except (OSError, PermissionError) as e2:
                    logger.warning(f"Still could not delete temporary file {local_path}: {e2}")
                    # File will be cleaned up by system later
            
            logger.info(f"Updated CSV file {file_id} at row {row}, col {col}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing to CSV file: {e}")
            raise
    
    def create_new_sheet(self, title: str, data: List[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new Google Sheet.
        
        Args:
            title (str): Sheet title
            data (List[List[str]], optional): Initial data
            
        Returns:
            Dict[str, Any]: Sheet information
        """
        try:
            # Create spreadsheet
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'Sheet1'
                        }
                    }
                ]
            }
            
            result = self.sheets_service.spreadsheets().create(body=spreadsheet).execute()
            sheet_id = result['spreadsheetId']
            
            # Add initial data if provided
            if data:
                self.write_sheet_data(sheet_id, "A1", data)
            
            # Set permissions if folder is specified
            if self.drive_folder_id:
                self._move_to_folder(sheet_id, self.drive_folder_id)
            
            logger.info(f"Created new sheet: {title} (ID: {sheet_id})")
            
            return {
                'id': sheet_id,
                'title': title,
                'url': f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            }
            
        except Exception as e:
            logger.error(f"Error creating new sheet: {e}")
            raise
    
    def read_csv_from_drive(self, filename: str) -> List[List[str]]:
        """
        Read CSV file from Google Drive.
        
        Args:
            filename (str): CSV filename
            
        Returns:
            List[List[str]]: CSV data
        """
        try:
            # Find file in Drive
            file_id = self._get_drive_file_id(filename, 'text/csv')
            
            # Download file
            local_path = self._download_drive_file(file_id)
            
            # Read CSV data
            data = []
            with open(local_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)
            
            # Clean up
            os.unlink(local_path)
            
            logger.info(f"Read {len(data)} rows from CSV file: {filename}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading CSV from Drive: {e}")
            raise
    
    def read_csv_by_file_id(self, file_id: str) -> List[List[str]]:
        """
        Read CSV file from Google Drive by file ID.
        
        Args:
            file_id (str): Google Drive file ID
            
        Returns:
            List[List[str]]: CSV data
        """
        try:
            # Download file
            local_path = self._download_drive_file(file_id)
            
            # Read CSV data
            data = []
            with open(local_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)
            
            # Clean up
            os.unlink(local_path)
            
            logger.info(f"Read {len(data)} rows from CSV file ID: {file_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading CSV from Drive by file ID: {e}")
            raise
    
    def write_csv_to_drive(self, filename: str, data: List[List[str]], 
                          create_new: bool = False) -> bool:
        """
        Write CSV data to Google Drive.
        
        Args:
            filename (str): CSV filename
            data (List[List[str]]): CSV data
            create_new (bool): Create new file if doesn't exist
            
        Returns:
            bool: True if successful
        """
        temp_path = None
        try:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.csv')
            os.close(temp_fd)  # Close the file descriptor immediately
            
            # Write CSV data
            with open(temp_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(data)
            
            # Small delay to ensure file is fully written
            import time
            time.sleep(0.1)
            
            if create_new:
                # Create new file in Drive
                file_metadata = {
                    'name': filename,
                    'parents': [self.drive_folder_id] if self.drive_folder_id else []
                }
                
                media = MediaFileUpload(temp_path, mimetype='text/csv', resumable=True)
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                logger.info(f"Created new CSV file: {filename} (ID: {file['id']})")
            else:
                # Update existing file
                file_id = self._get_drive_file_id(filename, 'text/csv')
                
                media = MediaFileUpload(temp_path, mimetype='text/csv', resumable=True)
                self.drive_service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
                
                logger.info(f"Updated CSV file: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing CSV to Drive: {e}")
            raise
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not delete temp file {temp_path}: {cleanup_error}")
    
    def read_excel_from_drive(self, filename: str, sheet_name: str = None) -> List[List[str]]:
        """
        Read Excel file from Google Drive.
        
        Args:
            filename (str): Excel filename
            sheet_name (str, optional): Sheet name, uses first sheet if not provided
            
        Returns:
            List[List[str]]: Excel data
        """
        try:
            # Find file in Drive
            file_id = self._get_drive_file_id(filename, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
            # Download file
            local_path = self._download_drive_file(file_id)
            
            # Read Excel data
            workbook = load_workbook(local_path, read_only=True)
            sheet = workbook[sheet_name] if sheet_name else workbook.active
            
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append([str(cell) if cell is not None else '' for cell in row])
            
            workbook.close()
            
            # Clean up
            os.unlink(local_path)
            
            logger.info(f"Read {len(data)} rows from Excel file: {filename}")
            return data
            
        except Exception as e:
            logger.error(f"Error reading Excel from Drive: {e}")
            raise
    
    def read_excel_by_file_id(self, file_id: str, sheet_name: str = None) -> List[List[str]]:
        """
        Read Excel file from Google Drive by file ID.
        
        Args:
            file_id (str): Google Drive file ID
            sheet_name (str, optional): Sheet name, uses first sheet if not provided
            
        Returns:
            List[List[str]]: Excel data
        """
        local_path = None
        try:
            # Download file
            local_path = self._download_drive_file(file_id)
            
            # Get file info for debugging
            file_info = self.drive_service.files().get(fileId=file_id, fields='name,mimeType,size').execute()
            file_name = file_info.get('name', 'Unknown')
            mime_type = file_info.get('mimeType', 'Unknown')
            file_size = file_info.get('size', 'Unknown')
            
            # Check file extension from the actual file name, not the downloaded path
            file_extension = os.path.splitext(file_name)[1].lower()
            
            logger.info(f"Processing Excel file: {file_name}, extension: '{file_extension}', mime: {mime_type}, size: {file_size}")
            
            # Check if it's actually an Excel file
            expected_mime_types = [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
                'application/vnd.ms-excel',  # .xls (legacy)
                'application/vnd.ms-excel.sheet.macroEnabled.12',  # .xlsm
                'application/vnd.openxmlformats-officedocument.spreadsheetml.template',  # .xltx
                'application/vnd.ms-excel.template.macroEnabled.12'  # .xltm
            ]
            
            if mime_type not in expected_mime_types:
                raise ValueError(
                    f"File is not a recognized Excel format. "
                    f"File name: {file_name}, MIME type: {mime_type}. "
                    f"Expected Excel MIME types: {', '.join(expected_mime_types)}"
                )
            
            # If MIME type is correct but no extension, assume it's .xlsx
            if not file_extension and mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                file_extension = '.xlsx'
                logger.info(f"Assuming .xlsx extension for file: {file_name}")
            
            # Read Excel file with pandas
            if not PANDAS_AVAILABLE:
                raise ValueError("pandas is not available - cannot read Excel files")
            
            try:
                data = self._read_excel_with_pandas(local_path, sheet_name)
                logger.info(f"Successfully read Excel file with pandas: {file_name}")
                
            except Exception as pandas_error:
                logger.error(f"pandas failed for {file_name}: {pandas_error}")
                
                # Check if it's a legacy format
                if file_extension == '.xls':
                    raise ValueError(
                        f"Legacy Excel format (.xls) not supported. "
                        f"Please convert the file to .xlsx format in Excel first. "
                        f"Supported formats: .xlsx, .xlsm, .xltx, .xltm"
                    )
                elif not file_extension:
                    raise ValueError(
                        f"File '{file_name}' has no file extension. "
                        f"Please rename the file to include a valid Excel extension (.xlsx, .xlsm, .xltx, .xltm). "
                        f"Current MIME type: {mime_type}"
                    )
                else:
                    # Check if the error is about unsupported format
                    error_str = str(pandas_error).lower()
                    if "does not support" in error_str or "file format" in error_str or "unable to read" in error_str:
                        raise ValueError(
                            f"❌ **Excel File Format Issue**\n\n"
                            f"The Excel file appears to be corrupted or in an unsupported format.\n\n"
                            f"**File Details:**\n"
                            f"• Name: {file_name}\n"
                            f"• Extension: {file_extension}\n"
                            f"• MIME Type: {mime_type}\n"
                            f"• Size: {file_size} bytes\n\n"
                            f"**Possible Solutions:**\n"
                            f"1. **Open and Re-save**: Open the file in Microsoft Excel and save it as a new .xlsx file\n"
                            f"2. **Check File Integrity**: The file might be corrupted - try downloading it from Google Drive and opening it\n"
                            f"3. **Convert Format**: If it's an older Excel format, convert it to .xlsx\n\n"
                            f"**Error Details:** {str(pandas_error)}"
                        )
                    else:
                        raise ValueError(
                            f"Unable to read Excel file. "
                            f"File extension: '{file_extension}', MIME type: {mime_type}. "
                            f"Please ensure the file is a valid Excel file (.xlsx, .xlsm, .xltx, .xltm). "
                            f"Error: {str(pandas_error)}"
                        )
            
            logger.info(f"Read {len(data)} rows from Excel file ID: {file_id}")
            return data
            
        except Exception as e:
            # Provide more helpful error messages
            if "does not support" in str(e) or "file format" in str(e) or "Unable to read Excel" in str(e):
                # Extract the specific error details
                error_details = str(e)
                if "File name:" in error_details:
                    # Parse the detailed error message
                    lines = error_details.split('\n')
                    file_info = ""
                    for line in lines:
                        if "File name:" in line or "MIME type:" in line:
                            file_info += line.strip() + "\n"
                    
                    error_msg = (
                        f"❌ **Excel File Error**\n\n"
                        f"The Excel file could not be read by this bot.\n\n"
                        f"**File Information:**\n{file_info}\n"
                        f"**Supported formats:** .xlsx, .xlsm, .xltx, .xltm\n\n"
                        f"**To fix this:**\n"
                        f"1. Open the file in Microsoft Excel\n"
                        f"2. Go to File → Save As\n"
                        f"3. Choose 'Excel Workbook (.xlsx)' format\n"
                        f"4. Save and try again\n\n"
                        f"**Error details:** {str(e)}"
                    )
                else:
                    error_msg = (
                        f"❌ **Excel Format Error**\n\n"
                        f"The Excel file format is not supported by this bot.\n\n"
                        f"**Supported formats:** .xlsx, .xlsm, .xltx, .xltm\n\n"
                        f"**To fix this:**\n"
                        f"1. Open the file in Microsoft Excel\n"
                        f"2. Go to File → Save As\n"
                        f"3. Choose 'Excel Workbook (.xlsx)' format\n"
                        f"4. Save and try again\n\n"
                        f"**Error details:** {str(e)}"
                    )
                raise ValueError(error_msg)
            else:
                logger.error(f"Error reading Excel from Drive by file ID: {e}")
                raise
        finally:
            # Clean up
            if local_path and os.path.exists(local_path):
                try:
                    os.unlink(local_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not delete temp file {local_path}: {cleanup_error}")
    
    def _read_excel_with_pandas(self, file_path: str, sheet_name: str = None) -> List[List[str]]:
        """
        Read Excel file using pandas as a fallback method.
        
        Args:
            file_path (str): Path to the Excel file
            sheet_name (str, optional): Sheet name, uses first sheet if not provided
            
        Returns:
            List[List[str]]: Excel data
        """
        try:
            # Read Excel file with pandas
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, keep_default_na=False, na_values=[''])
            else:
                df = pd.read_excel(file_path, keep_default_na=False, na_values=[''])
            
            # Clean up NaN values
            df = df.fillna('')
            
            # Convert DataFrame to list of lists
            data = []
            
            # Add column headers as first row
            headers = df.columns.tolist()
            data.append([str(col) for col in headers])
            
            # Add data rows
            for _, row in df.iterrows():
                data.append([str(val) if val != '' else '' for val in row])
            
            logger.info(f"Successfully read Excel file with pandas: {len(data)} rows")
            return data
            
        except Exception as e:
            logger.error(f"Error reading Excel with pandas: {e}")
            raise ValueError(f"Pandas failed to read Excel file: {str(e)}")
    
    def write_excel_to_drive(self, filename: str, data: List[List[str]], 
                            sheet_name: str = "Sheet1", create_new: bool = False) -> bool:
        """
        Write Excel data to Google Drive.
        
        Args:
            filename (str): Excel filename
            data (List[List[str]]): Excel data
            sheet_name (str): Sheet name
            create_new (bool): Create new file if doesn't exist
            
        Returns:
            bool: True if successful
        """
        if not PANDAS_AVAILABLE:
            raise ValueError("pandas is not available - cannot write Excel files")
        
        temp_path = None
        try:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
            os.close(temp_fd)  # Close the file descriptor immediately
            
            # Convert data to pandas DataFrame
            if data:
                # Use first row as headers if available
                headers = data[0] if data else []
                df_data = data[1:] if len(data) > 1 else []
                
                # Create DataFrame
                df = pd.DataFrame(df_data, columns=headers)
            else:
                # Empty DataFrame
                df = pd.DataFrame()
            
            # Write to Excel file
            with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Small delay to ensure file is fully written
            import time
            time.sleep(0.1)
            
            if create_new:
                # Create new file in Drive
                file_metadata = {
                    'name': filename,
                    'parents': [self.drive_folder_id] if self.drive_folder_id else []
                }
                
                media = MediaFileUpload(temp_path, 
                                      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                      resumable=True)
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                logger.info(f"Created new Excel file: {filename} (ID: {file['id']})")
            else:
                # Update existing file
                file_id = self._get_drive_file_id(filename, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                
                media = MediaFileUpload(temp_path,
                                      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                      resumable=True)
                self.drive_service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
                
                logger.info(f"Updated Excel file: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing Excel to Drive: {e}")
            raise
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not delete temp file {temp_path}: {cleanup_error}")
    
    def _get_drive_file_id(self, filename: str, mime_type: str) -> str:
        """Get file ID from Google Drive by filename and MIME type."""
        try:
            query = f"name='{filename}' and mimeType='{mime_type}'"
            if self.drive_folder_id:
                query += f" and '{self.drive_folder_id}' in parents"
            
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                raise FileNotFoundError(f"File '{filename}' not found in Drive")
            
            return files[0]['id']
            
        except Exception as e:
            logger.error(f"Error getting Drive file ID: {e}")
            raise
    
    def _download_drive_file(self, file_id: str) -> str:
        """Download file from Google Drive to temporary location."""
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = tempfile.NamedTemporaryFile(delete=False)
            
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
            
            fh.close()
            return fh.name
            
        except Exception as e:
            logger.error(f"Error downloading Drive file: {e}")
            raise
    
    def _move_to_folder(self, file_id: str, folder_id: str):
        """Move file to specified folder."""
        try:
            file = self.drive_service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            
            self.drive_service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
        except Exception as e:
            logger.error(f"Error moving file to folder: {e}")
            raise
    
    def _validate_range(self, range_name: str):
        """Validate Google Sheets range format."""
        import re
        if not re.match(r'^[A-Z]+[0-9]+(:[A-Z]+[0-9]+)?$', range_name):
            raise ValueError(f"Invalid range format: {range_name}")
    
    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """
        Get file information from Google Drive.
        
        Args:
            filename (str): Filename
            
        Returns:
            Dict[str, Any]: File information
        """
        try:
            # Try different MIME types
            mime_types = [
                'text/csv',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ]
            
            for mime_type in mime_types:
                try:
                    file_id = self._get_drive_file_id(filename, mime_type)
                    
                    file_info = self.drive_service.files().get(
                        fileId=file_id,
                        fields='id,name,mimeType,createdTime,modifiedTime,size'
                    ).execute()
                    
                    return {
                        'id': file_info['id'],
                        'name': file_info['name'],
                        'mime_type': file_info['mimeType'],
                        'created_time': file_info['createdTime'],
                        'modified_time': file_info['modifiedTime'],
                        'size': file_info.get('size', 0)
                    }
                    
                except FileNotFoundError:
                    continue
            
            raise FileNotFoundError(f"File '{filename}' not found in Drive")
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            raise
    
    def list_available_sheets(self) -> List[Dict[str, Any]]:
        """
        List all available Google Sheets in the specified folder.
        
        Returns:
            List[Dict[str, Any]]: List of sheet information
        """
        try:
            # Build query to search for Google Sheets in the specific folder
            if self.drive_folder_id:
                query = f"mimeType='application/vnd.google-apps.spreadsheet' and trashed=false and '{self.drive_folder_id}' in parents"
                logger.info(f"Searching for sheets in folder: {self.drive_folder_id}")
            else:
                query = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
                logger.warning("No GOOGLE_DRIVE_FOLDER_ID specified, searching all sheets")
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id,name,createdTime,modifiedTime,webViewLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} Google Sheets in folder")
            
            sheets = []
            for file in files:
                sheets.append({
                    'id': file['id'],
                    'name': file['name'],
                    'url': file['webViewLink'],
                    'created': file['createdTime'],
                    'modified': file['modifiedTime']
                })
            
            return sheets
            
        except Exception as e:
            logger.error(f"Error listing available sheets: {e}")
            return []
    
    def list_available_excel_files(self) -> List[Dict[str, Any]]:
        """
        List all available Excel files in the specified folder.
        
        Returns:
            List[Dict[str, Any]]: List of Excel file information
        """
        try:
            # Build query to search for Excel files in the specific folder
            if self.drive_folder_id:
                query = f"(mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel') and trashed=false and '{self.drive_folder_id}' in parents"
                logger.info(f"Searching for Excel files in folder: {self.drive_folder_id}")
            else:
                query = "(mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel') and trashed=false"
                logger.warning("No GOOGLE_DRIVE_FOLDER_ID specified, searching all Excel files")
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id,name,createdTime,modifiedTime,webViewLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} Excel files in folder")
            
            excel_files = []
            for file in files:
                excel_files.append({
                    'id': file['id'],
                    'name': file['name'],
                    'url': file['webViewLink'],
                    'created': file['createdTime'],
                    'modified': file['modifiedTime']
                })
            
            return excel_files
            
        except Exception as e:
            logger.error(f"Error listing available Excel files: {e}")
            return []
    
    def list_available_csv_files(self) -> List[Dict[str, Any]]:
        """
        List all available CSV files in the specified folder.
        
        Returns:
            List[Dict[str, Any]]: List of CSV file information
        """
        try:
            # Build query to search for CSV files in the specific folder
            if self.drive_folder_id:
                query = f"mimeType='text/csv' and trashed=false and '{self.drive_folder_id}' in parents"
                logger.info(f"Searching for CSV files in folder: {self.drive_folder_id}")
            else:
                query = "mimeType='text/csv' and trashed=false"
                logger.warning("No GOOGLE_DRIVE_FOLDER_ID specified, searching all CSV files")
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id,name,createdTime,modifiedTime,webViewLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} CSV files in folder")
            
            csv_files = []
            for file in files:
                csv_files.append({
                    'id': file['id'],
                    'name': file['name'],
                    'url': file['webViewLink'],
                    'created': file['createdTime'],
                    'modified': file['modifiedTime']
                })
            
            return csv_files
            
        except Exception as e:
            logger.error(f"Error listing available CSV files: {e}")
            return []

    # ==================== COMPREHENSIVE CRUD OPERATIONS ====================
    
    def read_file_data(self, file_id: str) -> Dict[str, Any]:
        """Read data from any supported file type"""
        try:
            logger.info(f"Reading file data: {file_id}")
            
            # Get file metadata
            file_metadata = self._get_file_metadata(file_id)
            file_type = self._determine_file_type(file_metadata)
            logger.info(f"File type determined: {file_type}")
            
            if file_type == 'excel':
                return self._read_excel_file(file_id)
            elif file_type == 'csv':
                return self._read_csv_file(file_id)
            elif file_type == 'sheets':
                return self._read_sheets_file(file_id)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Failed to read file data: {str(e)}")
            raise

    def _get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata to determine file type"""
        try:
            file_metadata = self.drive_service.files().get(fileId=file_id).execute()
            return file_metadata
        except Exception as e:
            logger.error(f"Failed to get file metadata: {str(e)}")
            raise

    def _determine_file_type(self, file_metadata: Dict[str, Any]) -> str:
        """Determine file type based on MIME type and name"""
        mime_type = file_metadata.get('mimeType', '')
        name = file_metadata.get('name', '').lower()
        
        if 'spreadsheet' in mime_type or name.endswith('.xlsx') or name.endswith('.xls'):
            return 'excel'
        elif 'csv' in mime_type or name.endswith('.csv'):
            return 'csv'
        elif 'google-apps.spreadsheet' in mime_type:
            return 'sheets'
        else:
            return 'unknown'

    def _read_excel_file(self, file_id: str) -> Dict[str, Any]:
        """Read Excel file data"""
        try:
            local_path = self._download_drive_file(file_id)
            # Read with proper handling of empty cells
            df = pd.read_excel(local_path, keep_default_na=False, na_values=[''])
            
            # Clean up NaN values
            df = df.fillna('')
            
            # Convert DataFrame to list of lists for display
            data = df.values.tolist()
            headers = df.columns.tolist()
            
            # Debug logging
            logger.info(f"DEBUG - Excel read: shape={df.shape}, headers={headers}")
            logger.info(f"DEBUG - Excel data: {data}")
            
            # Clean up temp file
            os.unlink(local_path)
            
            return {
                'type': 'excel',
                'headers': headers,
                'data': data,
                'shape': df.shape
            }
        except Exception as e:
            logger.error(f"Failed to read Excel file: {str(e)}")
            raise

    def _read_csv_file(self, file_id: str) -> Dict[str, Any]:
        """Read CSV file data"""
        try:
            local_path = self._download_drive_file(file_id)
            # Read with proper handling of empty cells
            df = pd.read_csv(local_path, keep_default_na=False, na_values=[''])
            
            # Clean up NaN values
            df = df.fillna('')
            
            data = df.values.tolist()
            headers = df.columns.tolist()
            
            os.unlink(local_path)
            
            return {
                'type': 'csv',
                'headers': headers,
                'data': data,
                'shape': df.shape
            }
        except Exception as e:
            logger.error(f"Failed to read CSV file: {str(e)}")
            raise

    def _read_sheets_file(self, file_id: str) -> Dict[str, Any]:
        """Read Google Sheets data"""
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=file_id,
                range='A1:ZZ1000'  # Adjust range as needed
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return {
                    'type': 'sheets',
                    'headers': [],
                    'data': [],
                    'shape': (0, 0)
                }
            
            headers = values[0] if values else []
            data = values[1:] if len(values) > 1 else []
            
            return {
                'type': 'sheets',
                'headers': headers,
                'data': data,
                'shape': (len(data), len(headers))
            }
        except Exception as e:
            logger.error(f"Failed to read Google Sheets file: {str(e)}")
            raise

    def write_file_data(self, file_id: str, row: int, col: str, value: str) -> bool:
        """Write data to any supported file type"""
        try:
            logger.info(f"Writing data: file_id={file_id}, row={row}, col={col}, value={value}")
            
            # Get file metadata
            file_metadata = self._get_file_metadata(file_id)
            file_type = self._determine_file_type(file_metadata)
            logger.info(f"Writing to file type: {file_type}")
            
            if file_type == 'excel':
                return self.write_excel_data(file_id, row, col, value)
            elif file_type == 'csv':
                return self._write_csv_data(file_id, row, col, value)
            elif file_type == 'sheets':
                return self._write_sheets_data(file_id, row, col, value)
            else:
                raise ValueError(f"Unsupported file type for writing: {file_type}")
                
        except Exception as e:
            logger.error(f"Failed to write file data: {str(e)}")
            raise

    def _write_csv_data(self, file_id: str, row: int, col: str, value: str) -> bool:
        """Write data to CSV file"""
        try:
            logger.info(f"Starting CSV write: file_id={file_id}, row={row}, col={col}, value={value}")
            
            # Download current file
            local_path = self._download_drive_file(file_id)
            # Read with proper handling of empty cells
            df = pd.read_csv(local_path, keep_default_na=False, na_values=[''])
            
            # Convert column letter to index
            col_idx = ord(col.upper()) - ord('A')
            
            # Ensure DataFrame has enough rows and columns
            max_rows_needed = max(row, len(df))
            max_cols_needed = max(col_idx + 1, len(df.columns))
            
            # Extend DataFrame if needed
            if len(df) < max_rows_needed:
                new_rows = pd.DataFrame(index=range(len(df), max_rows_needed), columns=df.columns)
                df = pd.concat([df, new_rows], ignore_index=True)
            
            if len(df.columns) < max_cols_needed:
                for i in range(len(df.columns), max_cols_needed):
                    col_name = f'Column_{chr(65 + i)}'
                    df[col_name] = ''
            
            # Update the cell
            df.iloc[row - 1, col_idx] = value
            
            # Clean up NaN values and ensure proper data types
            df = df.fillna('')
            
            # Write back to file
            df.to_csv(local_path, index=False)
            
            # Upload updated file
            media = MediaFileUpload(local_path, 
                                  mimetype='text/csv',
                                  resumable=True)
            
            self.drive_service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            
            # Clean up
            os.unlink(local_path)
            
            return True
            
        except Exception as e:
            logger.error(f"CSV write failed: {str(e)}")
            raise

    def _write_sheets_data(self, file_id: str, row: int, col: str, value: str) -> bool:
        """Write data to Google Sheets"""
        try:
            logger.info(f"Starting Google Sheets write: file_id={file_id}, row={row}, col={col}, value={value}")
            
            # Convert to A1 notation
            cell_range = f"{col}{row}"
            
            # Update the cell
            body = {
                'values': [[value]]
            }
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=file_id,
                range=cell_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Updated {result.get('updatedCells')} cells")
            return True
            
        except Exception as e:
            logger.error(f"Google Sheets write failed: {str(e)}")
            raise

    def create_file(self, name: str, file_type: str, parent_folder_id: str = None) -> str:
        """Create a new file of specified type"""
        try:
            logger.info(f"Creating new {file_type} file: {name}")
            
            file_metadata = {
                'name': name,
                'parents': [parent_folder_id] if parent_folder_id else []
            }
            
            if file_type == 'excel':
                file_metadata['mimeType'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                # Create empty Excel file
                df = pd.DataFrame()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                temp_file.close()
                
                with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                media = MediaFileUpload(temp_file.name, 
                                      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                      resumable=True)
                
            elif file_type == 'csv':
                file_metadata['mimeType'] = 'text/csv'
                # Create empty CSV file
                df = pd.DataFrame()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
                temp_file.close()
                
                df.to_csv(temp_file.name, index=False)
                
                media = MediaFileUpload(temp_file.name, 
                                      mimetype='text/csv',
                                      resumable=True)
                
            elif file_type == 'sheets':
                file_metadata['mimeType'] = 'application/vnd.google-apps.spreadsheet'
                media = None
                
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Create file
            if media:
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
            else:
                file = self.drive_service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
            
            # Clean up temp file
            if 'temp_file' in locals():
                os.unlink(temp_file.name)
            
            logger.info(f"Created {file_type} file with ID: {file.get('id')}")
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Failed to create file: {str(e)}")
            raise

    def list_files(self, folder_id: str = None, file_type: str = None) -> List[Dict[str, Any]]:
        """List files in Google Drive"""
        try:
            query = "trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            if file_type:
                if file_type == 'excel':
                    query += " and (mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel')"
                elif file_type == 'csv':
                    query += " and mimeType='text/csv'"
                elif file_type == 'sheets':
                    query += " and mimeType='application/vnd.google-apps.spreadsheet'"
            
            results = self.drive_service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} files")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise