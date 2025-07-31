"""
Simplified command handler with only /start command and interactive buttons.
"""

import json
import logging
import threading
from flask import jsonify, request
from app.core.auth import require_auth
from app.core.rate_limiter import rate_limit
from app.services.slack_service import SlackService
from app.services.google_service import GoogleService
from app.utils.helpers import log_request

logger = logging.getLogger(__name__)

# Initialize services
slack_service = SlackService()
google_service = GoogleService()

def handle_google_credential_error(user_id: str, channel_id: str = None) -> dict:
    """
    Handle Google credential errors.
    """
    error_message = "❌ Google credentials not configured properly. Please check your setup."
    
    if channel_id:
        slack_service.post_message(
            channel=channel_id,
            text=error_message,
            ephemeral=True
        )
    
    return jsonify({
        'response_type': 'ephemeral',
        'text': error_message
    })

@require_auth
@rate_limit(max_requests=50, window=3600, action="slash_command")
def handle_command():
    """
    Handle Slack slash commands and interactions.
    """
    try:
        # Check if this is an interaction (button click) or slash command
        if 'payload' in request.form:
            # This is an interaction
            return handle_interaction(request.form.get('payload'))
        
        user_id = request.user_id
        command = request.form.get('command')
        text = request.form.get('text', '')
        channel_id = request.form.get('channel_id')
        
        # Log the command
        log_request(user_id, f"slash_command_{command}", {"text": text})
        
        if command == '/start':
            return handle_start_command(channel_id)
        else:
            return jsonify({
                'response_type': 'ephemeral',
                'text': f"Unknown command: {command}. Use /start to see available options."
            })
            
    except Exception as e:
        logger.error(f"Error handling command: {e}", exc_info=True)
        return jsonify({
            'response_type': 'ephemeral',
            'text': f"An error occurred: {str(e)}"
        })

def handle_interaction(payload_str):
    """
    Handle Slack interactions (button clicks, etc.).
    """
    try:
        logger.info("Interaction received")
        payload = json.loads(payload_str)
        logger.info(f"Payload: {payload}")
        
        interaction_type = payload.get('type')
        logger.info(f"Interaction type: {interaction_type}")
        
        if interaction_type == 'block_actions':
            return handle_block_actions(payload)
        elif interaction_type == 'view_submission':
            return handle_view_submission(payload)
        else:
            logger.warning(f"Unknown interaction type: {interaction_type}")
            return jsonify({'ok': True})
        
    except Exception as e:
        logger.error(f"Error handling interaction: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_block_actions(payload):
    """
    Handle block actions (button clicks).
    """
    try:
        actions = payload.get('actions', [])
        if not actions:
            return jsonify({'ok': True})
        
        action = actions[0]
        action_id = action.get('action_id')
        
        if action_id == 'list_sheets_menu':
            return handle_list_sheets_action(payload)
        elif action_id == 'create_sheet_menu':
            return handle_create_sheet_action(payload)
        elif action_id == 'list_excel_menu':
            return handle_list_excel_action(payload)
        elif action_id == 'create_excel_menu':
            return handle_create_excel_action(payload)
        elif action_id == 'list_csv_menu':
            return handle_list_csv_action(payload)
        elif action_id == 'create_csv_menu':
            return handle_create_csv_action(payload)
        elif action_id.startswith('get_data_sheet_'):
            return handle_get_data_sheet_action(payload, action)
        elif action_id.startswith('get_data_excel_'):
            return handle_get_data_excel_action(payload, action)
        elif action_id.startswith('get_data_csv_'):
            return handle_get_data_csv_action(payload, action)
        elif action_id == 'refresh_data':
            return handle_refresh_data_action(payload, action)
        elif action_id == 'open_update_modal':
            return handle_open_update_modal_action(payload, action)
        else:
            logger.info(f"Unhandled action: {action_id}")
            return jsonify({'ok': True})
            
    except Exception as e:
        logger.error(f"Error handling block actions: {e}")
        return jsonify({'ok': True})

def handle_list_sheets_action(payload):
    """
    Handle list sheets button click.
    """
    try:
        logger.info("Handling list sheets action")
        user_id = payload.get('user', {}).get('id')
        channel_id = payload.get('channel', {}).get('id')
        
        # Send immediate response
        response = jsonify({'ok': True})
        
        # Fetch sheets in background
        def fetch_and_send_sheets():
            try:
                # Check Google credentials first
                cred_status = google_service.check_credentials()
                if cred_status['status'] != 'valid':
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Google credentials issue: {cred_status['error']}",
                        ephemeral=True
                    )
                    return
                
                # Get available sheets
                sheets = google_service.list_available_sheets()
                
                if not sheets:
                    slack_service.post_message(
                        channel=user_id,
                        text="📝 No Google Sheets found in your Drive folder.",
                        ephemeral=True
                    )
                    return
                
                # Format and send response
                blocks = slack_service.format_sheets_list_blocks(sheets)
                slack_service.post_message(
                    channel=user_id,
                    blocks=blocks,
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error fetching sheets: {e}")
                slack_service.post_message(
                    channel=user_id,
                    text=f"❌ Error listing sheets: {str(e)}",
                    ephemeral=True
                )
        
        # Start async operation
        thread = threading.Thread(target=fetch_and_send_sheets)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling list sheets action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_create_sheet_action(payload):
    """
    Handle create sheet button click.
    """
    try:
        logger.info("Handling create sheet action")
        user_id = payload.get('user', {}).get('id')
        channel_id = payload.get('channel', {}).get('id')
        trigger_id = payload.get('trigger_id')
        
        logger.info(f"Channel ID: {channel_id}, User ID: {user_id}, Trigger ID: {trigger_id}")
        
        if not trigger_id:
            logger.error("No trigger_id found in payload")
            return jsonify({'ok': True})
        
        # Build and open modal
        modal = slack_service.build_create_sheet_modal()
        slack_service.open_modal(trigger_id, modal)
        
        return jsonify({'ok': True})
        
    except Exception as e:
        logger.error(f"Error handling create sheet action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_get_data_sheet_action(payload, action):
    """
    Handle get data sheet button click.
    """
    try:
        logger.info("Handling get data sheet action")
        user_id = payload.get('user', {}).get('id')
        
        # Send immediate response
        response = jsonify({'ok': True})
        
        # Extract sheet ID from action value (direct sheet ID)
        sheet_id = action.get('value')
        if not sheet_id:
            logger.error("No sheet ID found in action value")
            return response
        
        # Extract sheet name from action ID
        action_id = action.get('action_id', '')
        sheet_name = action_id.replace('get_data_sheet_', '') if action_id.startswith('get_data_sheet_') else 'Unknown'
        
        # Fetch data in background
        def fetch_and_send_data():
            try:
                # Check Google credentials first
                cred_status = google_service.check_credentials()
                if cred_status['status'] != 'valid':
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Google credentials issue: {cred_status['error']}",
                        ephemeral=True
                    )
                    return
                
                # Get sheet data
                data = google_service.read_sheet_data(sheet_id, "A1:Z10")
                
                if not data:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"📝 No data found in sheet",
                        ephemeral=True
                    )
                    return
                
                # Format and send response
                blocks = slack_service.format_data_blocks(data, sheet_id, {"sheet_id": sheet_id})
                slack_service.post_message(
                    channel=user_id,
                    blocks=blocks,
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error fetching sheet data: {e}")
                slack_service.post_message(
                    channel=user_id,
                    text=f"❌ Error getting data from sheet: {str(e)}",
                    ephemeral=True
                )
        
        # Start async operation
        thread = threading.Thread(target=fetch_and_send_data)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling get data sheet action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_get_data_excel_action(payload, action):
    """
    Handle get data Excel button click.
    """
    try:
        logger.info("Handling get data Excel action")
        user_id = payload.get('user', {}).get('id')
        
        # Send immediate response
        response = jsonify({'ok': True})
        
        # Extract Excel file ID from action value (direct file ID)
        file_id = action.get('value')
        if not file_id:
            logger.error("No Excel file ID found in action value")
            return response
        
        # Extract file name from action ID
        action_id = action.get('action_id', '')
        file_name = action_id.replace('get_data_excel_', '') if action_id.startswith('get_data_excel_') else 'Unknown'
        
        # Fetch data in background
        def fetch_and_send_excel_data():
            try:
                # Check Google credentials first
                cred_status = google_service.check_credentials()
                if cred_status['status'] != 'valid':
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Google credentials issue: {cred_status['error']}",
                        ephemeral=True
                    )
                    return
                
                # Get Excel data
                data = google_service.read_excel_by_file_id(file_id)
                
                if not data:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"📝 No data found in Excel file",
                        ephemeral=True
                    )
                    return
                
                # Format and send response
                blocks = slack_service.format_data_blocks(data, 'excel', {"file_id": file_id})
                slack_service.post_message(
                    channel=user_id,
                    blocks=blocks,
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error fetching Excel data: {e}")
                slack_service.post_message(
                    channel=user_id,
                    text=f"❌ Error getting data from Excel file: {str(e)}",
                    ephemeral=True
                )
        
        # Start async operation
        thread = threading.Thread(target=fetch_and_send_excel_data)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling get data Excel action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_get_data_csv_action(payload, action):
    """
    Handle get data CSV button click.
    """
    try:
        logger.info("Handling get data CSV action")
        user_id = payload.get('user', {}).get('id')
        
        # Send immediate response
        response = jsonify({'ok': True})
        
        # Extract CSV file ID from action value (direct file ID)
        file_id = action.get('value')
        if not file_id:
            logger.error("No CSV file ID found in action value")
            return response
        
        # Extract file name from action ID
        action_id = action.get('action_id', '')
        file_name = action_id.replace('get_data_csv_', '') if action_id.startswith('get_data_csv_') else 'Unknown'
        
        # Fetch data in background
        def fetch_and_send_csv_data():
            try:
                # Check Google credentials first
                cred_status = google_service.check_credentials()
                if cred_status['status'] != 'valid':
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Google credentials issue: {cred_status['error']}",
                        ephemeral=True
                    )
                    return
                
                # Get CSV data
                data = google_service.read_csv_by_file_id(file_id)
                
                if not data:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"📝 No data found in CSV file",
                        ephemeral=True
                    )
                    return
                
                # Format and send response
                blocks = slack_service.format_data_blocks(data, 'csv', {"file_id": file_id})
                slack_service.post_message(
                    channel=user_id,
                    blocks=blocks,
                    ephemeral=True
                )
                
            except Exception as e:
                logger.error(f"Error fetching CSV data: {e}")
                slack_service.post_message(
                    channel=user_id,
                    text=f"❌ Error getting data from CSV file: {str(e)}",
                    ephemeral=True
                )
        
        # Start async operation
        thread = threading.Thread(target=fetch_and_send_csv_data)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling get data CSV action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_refresh_data_action(payload, action):
    """
    Handle refresh data button click.
    """
    try:
        logger.info("Handling refresh data action")
        user_id = payload.get('user', {}).get('id')
        
        # Send immediate response
        response = jsonify({'ok': True})
        
        # Extract file info from action value
        value = action.get('value', '{}')
        try:
            file_info = json.loads(value)
            source = file_info.get('source', 'sheet')
            params = file_info.get('params', {})
        except (json.JSONDecodeError, KeyError):
            logger.error("Failed to parse file info from action value")
            return response
        
        # Refresh data in background
        def refresh_data():
            try:
                # Check Google credentials first
                cred_status = google_service.check_credentials()
                if cred_status['status'] != 'valid':
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Google credentials issue: {cred_status['error']}",
                        ephemeral=True
                    )
                    return
                
                # Get updated data based on source using comprehensive CRUD operations
                if source == 'excel':
                    file_id = params.get('file_id')
                    if not file_id:
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ No file ID found for Excel refresh",
                            ephemeral=True
                        )
                        return
                    file_data = google_service.read_file_data(file_id)
                    data = file_data.get('data', [])
                    if file_data.get('headers'):
                        data = [file_data['headers']] + data
                    logger.info(f"DEBUG - Excel refresh: original_data={file_data.get('data', [])}")
                    logger.info(f"DEBUG - Excel refresh: headers={file_data.get('headers', [])}")
                    logger.info(f"DEBUG - Excel refresh: final_data={data}")
                    extra_actions = {"file_id": file_id}
                elif source == 'csv':
                    file_id = params.get('file_id')
                    if not file_id:
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ No file ID found for CSV refresh",
                            ephemeral=True
                        )
                        return
                    file_data = google_service.read_file_data(file_id)
                    data = file_data.get('data', [])
                    if file_data.get('headers'):
                        data = [file_data['headers']] + data
                    extra_actions = {"file_id": file_id}
                else:
                    # Default to sheet
                    sheet_id = params.get('sheet_id')
                    if not sheet_id:
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ No sheet ID found for refresh",
                            ephemeral=True
                        )
                        return
                    data = google_service.read_sheet_data(sheet_id, "A1:Z10")
                    extra_actions = {"sheet_id": sheet_id}
                
                if not data:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"📝 No data found in {source}",
                        ephemeral=True
                    )
                    return
                
                # Format and send response
                blocks = slack_service.format_data_blocks(data, source, extra_actions)
                slack_service.post_message(
                    channel=user_id,
                    blocks=blocks,
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error refreshing {source} data: {e}")
                slack_service.post_message(
                    channel=user_id,
                    text=f"❌ Error refreshing data from {source}: {str(e)}",
                    ephemeral=True
                )
        
        # Start async operation
        thread = threading.Thread(target=refresh_data)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling refresh data action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_open_update_modal_action(payload, action):
    """
    Handle open update modal button click.
    """
    try:
        logger.info("Handling open update modal action")
        user_id = payload.get('user', {}).get('id')
        trigger_id = payload.get('trigger_id')
        
        # Parse the value to get source and params
        import json
        value_data = json.loads(action.get('value', '{}'))
        source = value_data.get('source', 'sheet')
        params = value_data.get('params', {})
        
        logger.info(f"Opening update modal for source: {source}, params: {params}")
        
        if not trigger_id:
            logger.error("No trigger_id found in payload")
            return jsonify({'ok': True})
        
        # Build and open modal based on source
        if source == 'excel':
            file_id = params.get('file_id')
            modal = slack_service.build_write_data_modal('excel', file_id)
        elif source == 'csv':
            file_id = params.get('file_id')
            modal = slack_service.build_write_data_modal('csv', file_id)
        else:
            # Default to sheet
            sheet_id = params.get('sheet_id')
            modal = slack_service.build_write_data_modal('sheet', sheet_id)
        
        slack_service.open_modal(trigger_id, modal)
        
        return jsonify({'ok': True})
            
    except Exception as e:
        logger.error(f"Error handling open update modal action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_list_excel_action(payload):
    """
    Handle list Excel files button click.
    """
    try:
        logger.info("Handling list Excel action")
        user_id = payload.get('user', {}).get('id')
        
        # Send immediate response
        response = jsonify({'ok': True})
        
        # Fetch Excel files in background
        def fetch_and_send_excel():
            try:
                # Check Google credentials first
                cred_status = google_service.check_credentials()
                if cred_status['status'] != 'valid':
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Google credentials issue: {cred_status['error']}",
                        ephemeral=True
                    )
                    return
                
                # Get available Excel files
                excel_files = google_service.list_available_excel_files()
                
                if not excel_files:
                    slack_service.post_message(
                        channel=user_id,
                        text="📝 No Excel files found in your Drive folder.",
                        ephemeral=True
                    )
                    return
                
                # Format and send response
                blocks = slack_service.format_excel_list_blocks(excel_files)
                slack_service.post_message(
                    channel=user_id,
                    blocks=blocks,
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error fetching Excel files: {e}")
                slack_service.post_message(
                    channel=user_id,
                    text=f"❌ Error listing Excel files: {str(e)}",
                    ephemeral=True
                )
        
        # Start async operation
        thread = threading.Thread(target=fetch_and_send_excel)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling list Excel action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_create_excel_action(payload):
    """
    Handle create Excel file button click.
    """
    try:
        logger.info("Handling create Excel action")
        user_id = payload.get('user', {}).get('id')
        trigger_id = payload.get('trigger_id')
        
        if not trigger_id:
            logger.error("No trigger_id found in payload")
            return jsonify({'ok': True})
        
        # Build and open modal
        modal = slack_service.build_create_excel_modal()
        slack_service.open_modal(trigger_id, modal)
        
        return jsonify({'ok': True})
        
    except Exception as e:
        logger.error(f"Error handling create Excel action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_list_csv_action(payload):
    """
    Handle list CSV files button click.
    """
    try:
        logger.info("Handling list CSV action")
        user_id = payload.get('user', {}).get('id')
        
        # Send immediate response
        response = jsonify({'ok': True})
        
        # Fetch CSV files in background
        def fetch_and_send_csv():
            try:
                # Check Google credentials first
                cred_status = google_service.check_credentials()
                if cred_status['status'] != 'valid':
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Google credentials issue: {cred_status['error']}",
                        ephemeral=True
                    )
                    return
                
                # Get available CSV files
                csv_files = google_service.list_available_csv_files()
                
                if not csv_files:
                    slack_service.post_message(
                        channel=user_id,
                        text="📝 No CSV files found in your Drive folder.",
                        ephemeral=True
                    )
                    return
                
                # Format and send response
                blocks = slack_service.format_csv_list_blocks(csv_files)
                slack_service.post_message(
                    channel=user_id,
                    blocks=blocks,
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error fetching CSV files: {e}")
                slack_service.post_message(
                    channel=user_id,
                    text=f"❌ Error listing CSV files: {str(e)}",
                    ephemeral=True
                )
        
        # Start async operation
        thread = threading.Thread(target=fetch_and_send_csv)
        thread.daemon = True
        thread.start()
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling list CSV action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_create_csv_action(payload):
    """
    Handle create CSV file button click.
    """
    try:
        logger.info("Handling create CSV action")
        user_id = payload.get('user', {}).get('id')
        trigger_id = payload.get('trigger_id')
        
        if not trigger_id:
            logger.error("No trigger_id found in payload")
            return jsonify({'ok': True})
        
        # Build and open modal
        modal = slack_service.build_create_csv_modal()
        slack_service.open_modal(trigger_id, modal)
        
        return jsonify({'ok': True})
        
    except Exception as e:
        logger.error(f"Error handling create CSV action: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_view_submission(payload):
    """
    Handle modal submissions.
    """
    try:
        logger.info("Modal submission received")
        view = payload.get('view', {})
        callback_id = view.get('callback_id', '')
        
        if callback_id in ['write_data_modal', 'write_sheet_data_modal', 'write_excel_data_modal', 'write_csv_data_modal']:
            return handle_write_data_modal_submission(payload)
        elif callback_id == 'create_sheet_modal':
            return handle_create_sheet_modal_submission(payload)
        elif callback_id == 'create_excel_modal':
            return handle_create_excel_modal_submission(payload)
        elif callback_id == 'create_csv_modal':
            return handle_create_csv_modal_submission(payload)
        else:
            logger.info(f"Unknown modal callback_id: {callback_id}")
            return jsonify({'ok': True})
        
    except Exception as e:
        logger.error(f"Error handling view submission: {e}", exc_info=True)
        return jsonify({'ok': True})

def handle_write_data_modal_submission(payload):
    """
    Handle write data modal submission.
    """
    try:
        logger.info("Handling write data modal submission")
        view = payload.get('view', {})
        state = view.get('state', {}).get('values', {})
        
        # Extract form values
        row = state.get('row_block', {}).get('row_input', {}).get('value', '')
        col = state.get('col_block', {}).get('col_input', {}).get('value', '')
        value = state.get('value_block', {}).get('value_input', {}).get('value', '')
        
        # Extract metadata from private_metadata
        private_metadata = view.get('private_metadata', '{}')
        try:
            metadata = json.loads(private_metadata)
            source = metadata.get('source', 'sheet')
            
            # Get the appropriate ID based on source
            if source == 'excel':
                file_id = metadata.get('file_id')
                if not file_id:
                    logger.error("No file_id found in private_metadata for Excel")
                    return jsonify({
                        'response_action': 'errors',
                        'errors': {
                            'row_block': 'Configuration error: File ID not found'
                        }
                    })
            elif source == 'csv':
                file_id = metadata.get('file_id')
                if not file_id:
                    logger.error("No file_id found in private_metadata for CSV")
                    return jsonify({
                        'response_action': 'errors',
                        'errors': {
                            'row_block': 'Configuration error: File ID not found'
                        }
                    })
            else:
                # Default to sheet
                sheet_id = metadata.get('sheet_id')
                if not sheet_id:
                    logger.error("No sheet_id found in private_metadata")
                    return jsonify({
                        'response_action': 'errors',
                        'errors': {
                            'row_block': 'Configuration error: Sheet ID not found'
                        }
                    })
        except (json.JSONDecodeError, KeyError):
            logger.error("Failed to parse private_metadata")
            return jsonify({
                'response_action': 'errors',
                'errors': {
                    'row_block': 'Configuration error: Invalid metadata'
                }
            })
        
        # Log the appropriate ID based on source
        if source == 'excel':
            logger.info(f"Modal values - Excel File ID: {file_id}, Row: {row}, Col: {col}, Value: {value}")
        elif source == 'csv':
            logger.info(f"Modal values - CSV File ID: {file_id}, Row: {row}, Col: {col}, Value: {value}")
        else:
            logger.info(f"Modal values - Sheet ID: {sheet_id}, Row: {row}, Col: {col}, Value: {value}")
        
        # Basic validation only (fast)
        if not all([row, col, value]):
            return jsonify({
                'response_action': 'errors',
                'errors': {
                    'row_block': 'All fields are required'
                }
            })
        
        # Validate inputs (fast)
        try:
            row_num = int(row)
            if row_num < 1:
                raise ValueError("Row must be positive")
        except ValueError:
            return jsonify({
                'response_action': 'errors',
                'errors': {
                    'row_block': 'Row must be a positive number'
                }
            })
        
        # Convert column number to letter if needed (fast)
        try:
            col_num = int(col)
            if col_num < 1:
                raise ValueError("Column must be positive")
            # Convert number to letter (1=A, 2=B, etc.)
            col_letter = chr(64 + col_num)  # ASCII 65 is 'A'
            col = col_letter
        except ValueError:
            # If col is already a letter, use it as is
            if not col.isalpha():
                return jsonify({
                    'response_action': 'errors',
                    'errors': {
                        'col_block': 'Column must be a number (1,2,3...) or letter (A,B,C...)'
                    }
                })
        
        # Write data asynchronously based on source
        def update_data_async():
            try:
                # Log the variables at the start of async function
                logger.info(f"DEBUG - Async function start: row={row}, col={col}, value={value}")
                
                # Check Google credentials first
                user_id = payload.get('user', {}).get('id')
                if user_id:
                    cred_status = google_service.check_credentials()
                    if cred_status['status'] != 'valid':
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ Google credentials issue: {cred_status['error']}",
                            ephemeral=True
                        )
                        return
                
                # Update based on source type using comprehensive CRUD operations
                if source == 'excel':
                    try:
                        logger.info(f"Attempting to write Excel data: file_id={file_id}, row={row}, col={col}, value={value}")
                        google_service.write_file_data(file_id, int(row), col, value)
                        success_msg = f"✅ Updated Excel file at {col}{row} with value: {value}"
                        logger.info(f"Excel write successful: {success_msg}")
                        logger.info(f"DEBUG - Success message variables: col={col}, row={row}, value={value}")
                    except Exception as e:
                        logger.error(f"Excel write failed: {e}")
                        raise
                elif source == 'csv':
                    try:
                        logger.info(f"Attempting to write CSV data: file_id={file_id}, row={row}, col={col}, value={value}")
                        google_service.write_file_data(file_id, int(row), col, value)
                        success_msg = f"✅ Updated CSV file at {col}{row} with value: {value}"
                        logger.info(f"CSV write successful: {success_msg}")
                    except Exception as e:
                        logger.error(f"CSV write failed: {e}")
                        raise
                else:
                    # Default to sheet
                    range_name = f"{col}{row}"
                    google_service.write_sheet_data(sheet_id, range_name, value=value)
                    success_msg = f"✅ Updated Google Sheet at {col}{row} with value: {value}"
                
                # Send success message to user
                if user_id:
                    logger.info(f"DEBUG - Final success message variables: col={col}, row={row}, value={value}")
                    slack_service.post_message(
                        channel=user_id,
                        text=f"✅ Successfully updated cell {col}{row} with value: '{value}'",
                        ephemeral=True
                    )
            except Exception as e:
                logger.error(f"Error in async sheet update: {e}")
                # Send error message to user
                user_id = payload.get('user', {}).get('id')
                if user_id:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Error updating cell: {str(e)}",
                        ephemeral=True
                    )
        
        # Start async operation
        thread = threading.Thread(target=update_data_async)
        thread.daemon = True
        thread.start()
        
        # Return immediate success - this closes the modal
        return jsonify({
            'response_action': 'clear'
        })
        
    except Exception as e:
        logger.error(f"Error writing to sheet: {e}")
        # Check if it's a Google API error
        error_msg = str(e)
        if "403" in error_msg and "permission" in error_msg.lower():
            error_msg = "Permission denied. Please check your Google account permissions."
        elif "404" in error_msg:
            error_msg = "Sheet not found. Please check the sheet ID."
        else:
            error_msg = f"Error updating cell: {error_msg}"
        
        return jsonify({
            'response_action': 'errors',
            'errors': {
                'row_block': error_msg
            }
        })

def handle_create_sheet_modal_submission(payload):
    """
    Handle create sheet modal submission.
    """
    try:
        logger.info("Handling create sheet modal submission")
        view = payload.get('view', {})
        state = view.get('state', {}).get('values', {})
        
        # Extract form values
        title = state.get('title_block', {}).get('title_input', {}).get('value', '')
        template = state.get('template_block', {}).get('template_input', {}).get('selected_option', {}).get('value', 'empty')
        
        logger.info(f"Modal values - Title: {title}, Template: {template}")
        
        # Basic validation only (fast)
        if not title:
            return jsonify({
                'response_action': 'errors',
                'errors': {
                    'title_block': 'Sheet title is required'
                }
            })
        
        # Create the sheet asynchronously
        def create_sheet_async():
            try:
                # Check Google credentials first
                user_id = payload.get('user', {}).get('id')
                if user_id:
                    cred_status = google_service.check_credentials()
                    if cred_status['status'] != 'valid':
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ Google credentials issue: {cred_status['error']}",
                            ephemeral=True
                        )
                        return
                
                # Get template data
                template_data = get_template_data(template)
                
                # Create new sheet
                result = google_service.create_new_sheet(title, template_data)
                
                # Send success message to user
                if user_id:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"✅ Successfully created new Google Sheet: '{title}'\n🔗 <{result['url']}|Open in Google Sheets>",
                        ephemeral=True
                    )
            except Exception as e:
                logger.error(f"Error in async sheet creation: {e}")
                # Send error message to user
                if user_id:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Error creating sheet: {str(e)}",
                        ephemeral=True
                    )
        
        # Start async operation
        thread = threading.Thread(target=create_sheet_async)
        thread.daemon = True
        thread.start()
        
        # Return immediate success - this closes the modal
        return jsonify({
            'response_action': 'clear'
        })
            
    except Exception as e:
        logger.error(f"Error handling create sheet modal submission: {e}", exc_info=True)
        return jsonify({
            'response_action': 'errors',
            'errors': {
                'title_block': f'Error: {str(e)}'
            }
        })

def handle_create_excel_modal_submission(payload):
    """
    Handle create Excel modal submission.
    """
    try:
        logger.info("Handling create Excel modal submission")
        view = payload.get('view', {})
        state = view.get('state', {}).get('values', {})
        
        # Extract form values
        title = state.get('title_block', {}).get('title_input', {}).get('value', '')
        template = state.get('template_block', {}).get('template_input', {}).get('selected_option', {}).get('value', 'empty')
        
        logger.info(f"Modal values - Title: {title}, Template: {template}")
        
        # Basic validation only (fast)
        if not title:
            return jsonify({
                'response_action': 'errors',
                'errors': {
                    'title_block': 'File name is required'
                }
            })
        
        # Create the Excel file asynchronously
        def create_excel_async():
            try:
                # Check Google credentials first
                user_id = payload.get('user', {}).get('id')
                if user_id:
                    cred_status = google_service.check_credentials()
                    if cred_status['status'] != 'valid':
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ Google credentials issue: {cred_status['error']}",
                            ephemeral=True
                        )
                        return
                
        # Get template data
                template_data = get_template_data(template)
                
                # Create new Excel file
                filename = f"{title}.xlsx"
                success = google_service.write_excel_to_drive(filename, template_data, create_new=True)
                
                if success:
                    # Send success message to user
                    if user_id:
                        slack_service.post_message(
                            channel=user_id,
                            text=f"✅ Successfully created new Excel file: '{filename}'",
                            ephemeral=True
                        )
                else:
                    if user_id:
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ Failed to create Excel file: '{filename}'",
                            ephemeral=True
                        )
            except Exception as e:
                logger.error(f"Error in async Excel creation: {e}")
                # Send error message to user
                if user_id:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Error creating Excel file: {str(e)}",
                        ephemeral=True
                    )
        
        # Start async operation
        thread = threading.Thread(target=create_excel_async)
        thread.daemon = True
        thread.start()
        
        # Return immediate success - this closes the modal
        return jsonify({
            'response_action': 'clear'
        })
        
    except Exception as e:
        logger.error(f"Error handling create Excel modal submission: {e}", exc_info=True)
        return jsonify({
            'response_action': 'errors',
            'errors': {
                'title_block': f'Error: {str(e)}'
            }
        })

def handle_create_csv_modal_submission(payload):
    """
    Handle create CSV modal submission.
    """
    try:
        logger.info("Handling create CSV modal submission")
        view = payload.get('view', {})
        state = view.get('state', {}).get('values', {})
        
        # Extract form values
        title = state.get('title_block', {}).get('title_input', {}).get('value', '')
        template = state.get('template_block', {}).get('template_input', {}).get('selected_option', {}).get('value', 'empty')
        
        logger.info(f"Modal values - Title: {title}, Template: {template}")
        
        # Basic validation only (fast)
        if not title:
            return jsonify({
                'response_action': 'errors',
                'errors': {
                    'title_block': 'File name is required'
                }
            })
        
        # Create the CSV file asynchronously
        def create_csv_async():
            try:
                # Check Google credentials first
                user_id = payload.get('user', {}).get('id')
                if user_id:
                    cred_status = google_service.check_credentials()
                    if cred_status['status'] != 'valid':
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ Google credentials issue: {cred_status['error']}",
                            ephemeral=True
                        )
                        return
                
                # Get template data
                template_data = get_template_data(template)
        
                # Create new CSV file
                filename = f"{title}.csv"
                success = google_service.write_csv_to_drive(filename, template_data, create_new=True)
                
                if success:
                    # Send success message to user
                    if user_id:
                        slack_service.post_message(
                            channel=user_id,
                            text=f"✅ Successfully created new CSV file: '{filename}'",
                            ephemeral=True
                        )
                else:
                    if user_id:
                        slack_service.post_message(
                            channel=user_id,
                            text=f"❌ Failed to create CSV file: '{filename}'",
                            ephemeral=True
                        )
            except Exception as e:
                logger.error(f"Error in async CSV creation: {e}")
                # Send error message to user
                if user_id:
                    slack_service.post_message(
                        channel=user_id,
                        text=f"❌ Error creating CSV file: {str(e)}",
                        ephemeral=True
                    )
        
        # Start async operation
        thread = threading.Thread(target=create_csv_async)
        thread.daemon = True
        thread.start()
        
        # Return immediate success - this closes the modal
        return jsonify({
            'response_action': 'clear'
        })
        
    except Exception as e:
        logger.error(f"Error handling create CSV modal submission: {e}", exc_info=True)
        return jsonify({
            'response_action': 'errors',
            'errors': {
                'title_block': f'Error: {str(e)}'
            }
        })

def get_template_data(template: str):
    """
    Get template data for new sheets.
    """
    templates = {
        'empty': [],
        'task_tracker': [
            ['Task', 'Status', 'Assignee', 'Due Date', 'Priority'],
            ['', 'Not Started', '', '', 'Medium']
        ],
        'sales_report': [
            ['Product', 'Sales', 'Revenue', 'Date', 'Region'],
            ['', '0', '$0', '', '']
        ],
        'inventory': [
            ['Item', 'Quantity', 'Price', 'Category', 'Last Updated'],
            ['', '0', '$0', '', '']
        ]
    }
    
    return templates.get(template, [])

def handle_start_command(channel_id):
    """
    Handle /start command - show main menu.
    """
    try:
        blocks = slack_service.build_main_menu_blocks()
        
        return jsonify({
            'response_type': 'in_channel',
            'blocks': blocks,
            'text': 'Welcome to Slack Data Manager Bot!'
        })
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        return jsonify({
            'response_type': 'ephemeral',
            'text': f"Error displaying menu: {str(e)}"
        })

# Create Flask blueprint
from flask import Blueprint

command_bp = Blueprint('command', __name__)

# Register routes
@command_bp.route('/command', methods=['POST'])
def command_endpoint():
    return handle_command()

@command_bp.route('/interactions/command', methods=['POST'])
def interactions_endpoint():
    return handle_interaction(request.form.get('payload', '{}')) 