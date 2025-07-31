"""
Slack service for message formatting, modal handling, and API interactions.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web.slack_response import SlackResponse

logger = logging.getLogger(__name__)

# Global Slack client
slack_client = None

def get_slack_client() -> WebClient:
    """
    Get or create Slack client instance.
    
    Returns:
        WebClient: Slack client instance
    """
    global slack_client
    
    if slack_client is None:
        token = os.getenv('SLACK_BOT_TOKEN')
        if not token:
            raise ValueError("SLACK_BOT_TOKEN not configured")
        
        slack_client = WebClient(token=token)
    
    return slack_client

class SlackService:
    """Service for Slack API interactions and message formatting."""
    
    def __init__(self):
        """Initialize Slack service."""
        self.client = get_slack_client()
    
    def post_message(self, channel: str, text: str = None, blocks: List[Dict] = None, 
                    thread_ts: str = None, ephemeral: bool = False) -> Dict[str, Any]:
        """
        Post message to Slack channel.
        
        Args:
            channel (str): Channel ID or name
            text (str, optional): Message text
            blocks (List[Dict], optional): Message blocks
            thread_ts (str, optional): Thread timestamp
            ephemeral (bool): Whether message should be ephemeral
            
        Returns:
            Dict[str, Any]: Response data
        """
        try:
            kwargs = {
                'channel': channel,
                'text': text or "Message from Slack Data Manager Bot"
            }
            
            if blocks:
                kwargs['blocks'] = blocks
            
            if thread_ts:
                kwargs['thread_ts'] = thread_ts
            
            if ephemeral:
                kwargs['response_type'] = 'ephemeral'
            
            response = self.client.chat_postMessage(**kwargs)
            
            logger.info(f"Posted message to channel {channel}")
            return response
            
        except SlackApiError as e:
            logger.error(f"Slack API error posting message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error posting message: {e}")
            raise
    
    def update_message(self, channel: str, ts: str, text: str = None, 
                      blocks: List[Dict] = None) -> Dict[str, Any]:
        """
        Update existing message in Slack.
        
        Args:
            channel (str): Channel ID
            ts (str): Message timestamp
            text (str, optional): New message text
            blocks (List[Dict], optional): New message blocks
            
        Returns:
            Dict[str, Any]: Response data
        """
        try:
            kwargs = {
                'channel': channel,
                'ts': ts
            }
            
            if text:
                kwargs['text'] = text
            
            if blocks:
                kwargs['blocks'] = blocks
            
            response = self.client.chat_update(**kwargs)
            
            logger.info(f"Updated message {ts} in channel {channel}")
            return response
            
        except SlackApiError as e:
            logger.error(f"Slack API error updating message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating message: {e}")
            raise
    
    def open_modal(self, trigger_id: str, modal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Open modal in Slack.
        
        Args:
            trigger_id (str): Trigger ID from interaction
            modal (Dict[str, Any]): Modal configuration
            
        Returns:
            Dict[str, Any]: Response data
        """
        try:
            response = self.client.views_open(
                trigger_id=trigger_id,
                view=modal
            )
            
            logger.info(f"Opened modal with trigger_id {trigger_id}")
            return response
            
        except SlackApiError as e:
            logger.error(f"Slack API error opening modal: {e}")
            raise
        except Exception as e:
            logger.error(f"Error opening modal: {e}")
            raise
    
    def update_modal(self, view_id: str, modal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing modal in Slack.
        
        Args:
            view_id (str): View ID
            modal (Dict[str, Any]): Updated modal configuration
            
        Returns:
            Dict[str, Any]: Response data
        """
        try:
            response = self.client.views_update(
                view_id=view_id,
                view=modal
            )
            
            logger.info(f"Updated modal {view_id}")
            return response
            
        except SlackApiError as e:
            logger.error(f"Slack API error updating modal: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating modal: {e}")
            raise
    
    def format_data_blocks(self, data: List[List[str]], source: str, 
                          extra_actions: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Format data into Slack blocks.
        
        Args:
            data (List[List[str]]): Data to format
            source (str): Data source (sheet, csv, excel)
            extra_actions (Dict[str, Any], optional): Additional action parameters
            
        Returns:
            List[Dict[str, Any]]: Formatted blocks
        """
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Data from {source.upper()}*"
                }
            },
            {"type": "divider"}
        ]
        
        if data:
            # Display header row if available
            if data:
                header = " | ".join(data[0]) if data[0] else ""
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*`{header}`*"
                    }
                })
                
                # Display data rows
                for row in data[1:]:
                    row_text = " | ".join(row) if row else ""
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": row_text
                        }
                    })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "No data found for the specified range."
                }
            })
        
        # Add action buttons
        actions = [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "🔄 Refresh"
                },
                "action_id": "refresh_data",
                "value": json.dumps({
                    "source": source,
                    "params": extra_actions or {}
                })
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "✏️ Update Cell"
                },
                "action_id": "open_update_modal",
                "value": json.dumps({
                    "source": source,
                    "params": extra_actions or {}
                })
            },

        ]
        
        blocks.append({"type": "actions", "elements": actions})
        return blocks
    
    def build_main_menu_blocks(self) -> List[Dict[str, Any]]:
        """
        Build main menu blocks.
        
        Returns:
            List[Dict[str, Any]]: Main menu blocks
        """
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hello! I'm your Data Manager Bot. How can I help you today?"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 List Sheets*\nView all available Google Sheets"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "List Sheets"
                    },
                    "action_id": "list_sheets_menu",
                    "style": "primary"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📄 Create New Sheet*\nCreate a new Google Sheet in your Drive folder"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Create Sheet"
                    },
                    "action_id": "create_sheet_menu",
                    "style": "primary"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 List Excel Files*\nView all available Excel files"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "List Excel"
                    },
                    "action_id": "list_excel_menu",
                    "style": "primary"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📈 Create Excel File*\nCreate a new Excel file in your Drive folder"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Create Excel"
                    },
                    "action_id": "create_excel_menu",
                    "style": "primary"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 List CSV Files*\nView all available CSV files"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "List CSV"
                    },
                    "action_id": "list_csv_menu",
                    "style": "primary"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📄 Create CSV File*\nCreate a new CSV file in your Drive folder"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Create CSV"
                    },
                    "action_id": "create_csv_menu",
                    "style": "primary"
                }
            }
        ]
    
    def build_get_data_modal(self, source: str = "sheet") -> Dict[str, Any]:
        """
        Build modal for getting data.
        
        Args:
            source (str): Data source type
            
        Returns:
            Dict[str, Any]: Modal configuration
        """
        modal = {
            "type": "modal",
            "callback_id": f"get_{source}_data_modal",
            "title": {
                "type": "plain_text",
                "text": f"Get {source.upper()} Data"
            },
            "submit": {
                "type": "plain_text",
                "text": "Get Data"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "range_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Range (e.g., A1:B10)"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "range_input",
                        "initial_value": "A1:B10",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter range like A1:B10"
                        }
                    }
                }
            ]
        }
        
        # Add source-specific fields
        if source in ["csv", "excel"]:
            modal["blocks"].insert(0, {
                "type": "input",
                "block_id": "filename_block",
                "label": {
                    "type": "plain_text",
                    "text": "Filename"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "filename_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": f"Enter {source.upper()} filename"
                    }
                }
            })
        
        if source == "excel":
            modal["blocks"].insert(2, {
                "type": "input",
                "block_id": "sheet_name_block",
                "label": {
                    "type": "plain_text",
                    "text": "Sheet Name (optional)"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "sheet_name_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Leave empty for first sheet"
                    }
                }
            })
        
        return modal
    
    def build_write_data_modal(self, source: str = "sheet", sheet_id: str = None) -> Dict[str, Any]:
        """
        Build modal for writing data.
        
        Args:
            source (str): Data source type
            sheet_id (str, optional): Sheet ID for sheet operations
            
        Returns:
            Dict[str, Any]: Modal configuration
        """
        modal = {
            "type": "modal",
            "callback_id": f"write_{source}_data_modal",
            "title": {
                "type": "plain_text",
                "text": f"Write {source.upper()} Data"
            },
            "submit": {
                "type": "plain_text",
                "text": "Update"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "row_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Row"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "row_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter row number"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "col_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Column"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "col_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter column letter (A, B, C...)"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "value_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Value"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "value_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter the value to write"
                        }
                    }
                }
            ]
        }
        
        # Add source-specific fields
        if source in ["csv", "excel"]:
            modal["blocks"].insert(0, {
                "type": "input",
                "block_id": "filename_block",
                "label": {
                    "type": "plain_text",
                    "text": "Filename"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "filename_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": f"Enter {source.upper()} filename"
                    }
                }
            })
        
        if source == "excel":
            modal["blocks"].insert(2, {
                "type": "input",
                "block_id": "sheet_name_block",
                "label": {
                    "type": "plain_text",
                    "text": "Sheet Name (optional)"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "sheet_name_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Leave empty for first sheet"
                    }
                }
            })
        
        # Add private metadata for sheet operations
        if source == "sheet" and sheet_id:
            modal["private_metadata"] = json.dumps({
                "sheet_id": sheet_id,
                "source": source
            })
        
        return modal
    
    def build_create_file_modal(self, file_type: str = "sheet") -> Dict[str, Any]:
        """
        Build modal for creating new files.
        
        Args:
            file_type (str): Type of file to create
            
        Returns:
            Dict[str, Any]: Modal configuration
        """
        modal = {
            "type": "modal",
            "callback_id": f"create_{file_type}_modal",
            "title": {
                "type": "plain_text",
                "text": f"Create New {file_type.upper()}"
            },
            "submit": {
                "type": "plain_text",
                "text": "Create"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title_block",
                    "label": {
                        "type": "plain_text",
                        "text": "File Title"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter file title"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "template_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Template"
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "template_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a template"
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Empty"
                                },
                                "value": "empty"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Sales Report"
                                },
                                "value": "sales"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Inventory"
                                },
                                "value": "inventory"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Project Tracker"
                                },
                                "value": "project"
                            }
                        ]
                    }
                }
            ]
        }
        
        return modal
    
    def format_error_message(self, error: str, context: str = None) -> List[Dict[str, Any]]:
        """
        Format error message for Slack.
        
        Args:
            error (str): Error message
            context (str, optional): Additional context
            
        Returns:
            List[Dict[str, Any]]: Error blocks
        """
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":x: *Error*\n{error}"
                }
            }
        ]
        
        if context:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Context: {context}"
                    }
                ]
            })
        
        return blocks
    
    def format_sheets_list_blocks(self, sheets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format sheets list as Slack blocks.
        
        Args:
            sheets (List[Dict[str, Any]]): List of sheet information
            
        Returns:
            List[Dict[str, Any]]: Formatted blocks
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Available Google Sheets"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        for i, sheet in enumerate(sheets, 1):
            # Format date
            modified_date = sheet['modified'][:10] if sheet['modified'] else 'Unknown'
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{i}. {sheet['name']}*\n"
                           f"🆔 `{sheet['id']}`\n"
                           f"📅 Modified: {modified_date}\n"
                           f"🔗 <{sheet['url']}|Open in Google Sheets>"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Get Data"
                    },
                    "action_id": f"get_data_sheet_{sheet['id']}",
                    "value": sheet['id']
                }
            })
            
            if i < len(sheets):  # Don't add divider after last item
                blocks.append({"type": "divider"})
        
                return blocks
    
    def format_excel_list_blocks(self, excel_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format Excel files list as Slack blocks.
        
        Args:
            excel_files (List[Dict[str, Any]]): List of Excel file information
            
        Returns:
            List[Dict[str, Any]]: Formatted blocks
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Available Excel Files"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        for i, file in enumerate(excel_files, 1):
            # Format date
            modified_date = file['modified'][:10] if file['modified'] else 'Unknown'
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{i}. {file['name']}*\n:id: {file['id']}\n:date: Modified: {modified_date}\n:link: <{file['url']}|Open in Google Drive>"
                }
            })
        
        return blocks
    
    def format_csv_list_blocks(self, csv_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format CSV files list as Slack blocks.
        
        Args:
            csv_files (List[Dict[str, Any]]): List of CSV file information
            
        Returns:
            List[Dict[str, Any]]: Formatted blocks
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📋 Available CSV Files"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        for i, file in enumerate(csv_files, 1):
            # Format date
            modified_date = file['modified'][:10] if file['modified'] else 'Unknown'
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{i}. {file['name']}*\n:id: {file['id']}\n:date: Modified: {modified_date}\n:link: <{file['url']}|Open in Google Drive>"
                }
            })
        
        return blocks
    
    def build_create_excel_modal(self) -> Dict[str, Any]:
        """
        Build modal for creating Excel files.
        
        Returns:
            Dict[str, Any]: Modal configuration
        """
        modal = {
            "type": "modal",
            "callback_id": "create_excel_modal",
            "title": {
                "type": "plain_text",
                "text": "Create Excel File"
            },
            "submit": {
                "type": "plain_text",
                "text": "Create"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title_block",
                    "label": {
                        "type": "plain_text",
                        "text": "File Name"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter file name (e.g., Sales Report)"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "template_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Template"
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "template_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a template"
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Empty"
                                },
                                "value": "empty"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Sales Report"
                                },
                                "value": "sales"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Inventory"
                                },
                                "value": "inventory"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Project Tracker"
                                },
                                "value": "project"
                            }
                        ]
                    }
                }
            ]
        }
        
        return modal
    
    def build_create_csv_modal(self) -> Dict[str, Any]:
        """
        Build modal for creating CSV files.
        
        Returns:
            Dict[str, Any]: Modal configuration
        """
        modal = {
            "type": "modal",
            "callback_id": "create_csv_modal",
            "title": {
                "type": "plain_text",
                "text": "Create CSV File"
            },
            "submit": {
                "type": "plain_text",
                "text": "Create"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title_block",
                    "label": {
                        "type": "plain_text",
                        "text": "File Name"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter file name (e.g., Sales Data)"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "template_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Template"
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "template_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a template"
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Empty"
                                },
                                "value": "empty"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Sales Report"
                                },
                                "value": "sales"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Inventory"
                                },
                                "value": "inventory"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Project Tracker"
                                },
                                "value": "project"
                            }
                        ]
                    }
                }
            ]
        }
        
        return modal
    
    def format_success_message(self, message: str, details: str = None) -> List[Dict[str, Any]]:
        """
        Format success message for Slack.
        
        Args:
            message (str): Success message
            details (str, optional): Additional details
            
        Returns:
            List[Dict[str, Any]]: Success blocks
        """
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: *Success*\n{message}"
                }
            }
        ]
        
        if details:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": details
                    }
                ]
            })
        
        return blocks 
    
    def build_create_sheet_modal(self) -> Dict[str, Any]:
        """
        Build modal for creating new Google Sheets.
        
        Returns:
            Dict[str, Any]: Modal configuration
        """
        modal = {
            "type": "modal",
            "callback_id": "create_sheet_modal",
            "title": {
                "type": "plain_text",
                "text": "Create New Google Sheet"
            },
            "submit": {
                "type": "plain_text",
                "text": "Create"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "title_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Sheet Title"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "title_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Enter sheet title (e.g., Project Tracker)"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "template_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Template (Optional)"
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "template_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a template"
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Empty Sheet"
                                },
                                "value": "empty"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Task Tracker"
                                },
                                "value": "task_tracker"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Sales Report"
                                },
                                "value": "sales_report"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Inventory List"
                                },
                                "value": "inventory"
                            }
                        ]
                    }
                }
            ]
        }
        
        return modal

 