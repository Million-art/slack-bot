"""
Helper utilities for the Slack Data Manager Bot.
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def log_request(request_type: str, user_id: str = None, details: str = None):
    """
    Log request details for debugging and monitoring.
    
    Args:
        request_type (str): Type of request (e.g., 'command', 'interaction')
        user_id (str, optional): User ID making the request
        details (str, optional): Additional details about the request
    """
    log_message = f"Request: {request_type}"
    if user_id:
        log_message += f" | User: {user_id}"
    if details:
        log_message += f" | Details: {details}"
    
    logger.info(log_message)

def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize user input for security.
    
    Args:
        input_str (str): Input string to sanitize
        max_length (int): Maximum allowed length
        
    Returns:
        str: Sanitized input string
    """
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', input_str)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized.strip()

def format_error_message(error: str, context: str = None) -> str:
    """
    Format error message for user display.
    
    Args:
        error (str): Error message
        context (str, optional): Additional context
        
    Returns:
        str: Formatted error message
    """
    message = f"❌ Error: {error}"
    
    if context:
        message += f"\nContext: {context}"
    
    return message

def extract_cell_reference(cell_ref: str) -> Optional[tuple]:
    """
    Extract row and column from cell reference.
    
    Args:
        cell_ref (str): Cell reference (e.g., "A1")
        
    Returns:
        Optional[tuple]: (row, col) or None if invalid
    """
    if not cell_ref:
        return None
    
    # Pattern for cell reference like A1, B2, etc.
    pattern = r'^([A-Z]+)([0-9]+)$'
    match = re.match(pattern, cell_ref.upper())
    
    if not match:
        return None
    
    col = match.group(1)
    row = int(match.group(2))
    
    return (row, col)

def parse_range_string(range_str: str) -> Optional[tuple]:
    """
    Parse range string into coordinates.
    
    Args:
        range_str (str): Range string (e.g., "A1:B10")
        
    Returns:
        Optional[tuple]: (start_row, start_col, end_row, end_col) or None
    """
    if not range_str:
        return None
    
    # Pattern for range like A1:B10
    pattern = r'^([A-Z]+)([0-9]+):([A-Z]+)([0-9]+)$'
    match = re.match(pattern, range_str.upper())
    
    if not match:
        return None
    
    start_col = match.group(1)
    start_row = int(match.group(2))
    end_col = match.group(3)
    end_row = int(match.group(4))
    
    return (start_row, start_col, end_row, end_col)

def column_letter_to_index(column_letter: str) -> int:
    """
    Convert column letter to 1-based index.
    
    Args:
        column_letter (str): Column letter (A, B, C...)
        
    Returns:
        int: Column index (1-based)
    """
    result = 0
    for char in column_letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result

def index_to_column_letter(index: int) -> str:
    """
    Convert 1-based index to column letter.
    
    Args:
        index (int): Column index (1-based)
        
    Returns:
        str: Column letter
    """
    result = ""
    while index > 0:
        index -= 1
        result = chr(ord('A') + (index % 26)) + result
        index //= 26
    return result

def chunk_data(data: List[List[str]], chunk_size: int = 100) -> List[List[List[str]]]:
    """
    Split data into chunks for processing.
    
    Args:
        data (List[List[str]]): Data to chunk
        chunk_size (int): Size of each chunk
        
    Returns:
        List[List[List[str]]]: Chunked data
    """
    if not data:
        return []
    
    chunks = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks

def flatten_data(data: List[List[str]]) -> List[str]:
    """
    Flatten 2D data into 1D list.
    
    Args:
        data (List[List[str]]): 2D data
        
    Returns:
        List[str]: Flattened data
    """
    if not data:
        return []
    
    flattened = []
    for row in data:
        flattened.extend(row)
    
    return flattened

def transpose_data(data: List[List[str]]) -> List[List[str]]:
    """
    Transpose 2D data (swap rows and columns).
    
    Args:
        data (List[List[str]]): Data to transpose
        
    Returns:
        List[List[str]]: Transposed data
    """
    if not data:
        return []
    
    # Find the maximum row length
    max_cols = max(len(row) for row in data) if data else 0
    
    # Transpose the data
    transposed = []
    for col in range(max_cols):
        new_row = []
        for row in data:
            if col < len(row):
                new_row.append(row[col])
            else:
                new_row.append('')
        transposed.append(new_row)
    
    return transposed

def filter_data_by_column(data: List[List[str]], column_index: int, value: str) -> List[List[str]]:
    """
    Filter data by column value.
    
    Args:
        data (List[List[str]]): Data to filter
        column_index (int): Column index to filter by
        value (str): Value to filter for
        
    Returns:
        List[List[str]]: Filtered data
    """
    if not data:
        return []
    
    filtered = []
    for row in data:
        if column_index < len(row) and str(row[column_index]) == str(value):
            filtered.append(row)
    
    return filtered

def sort_data_by_column(data: List[List[str]], column_index: int, reverse: bool = False) -> List[List[str]]:
    """
    Sort data by column.
    
    Args:
        data (List[List[str]]): Data to sort
        column_index (int): Column index to sort by
        reverse (bool): Sort in reverse order
        
    Returns:
        List[List[str]]: Sorted data
    """
    if not data:
        return []
    
    def get_sort_key(row):
        if column_index < len(row):
            # Try to convert to number for proper sorting
            try:
                return float(row[column_index])
            except (ValueError, TypeError):
                return str(row[column_index])
        return ""
    
    return sorted(data, key=get_sort_key, reverse=reverse)

def validate_data_structure(data: List[List[str]]) -> bool:
    """
    Validate that data has consistent structure.
    
    Args:
        data (List[List[str]]): Data to validate
        
    Returns:
        bool: True if data structure is valid
    """
    if not data:
        return True
    
    # Check that all rows have the same number of columns
    first_row_length = len(data[0])
    for row in data:
        if len(row) != first_row_length:
            return False
    
    return True

def get_data_statistics(data: List[List[str]]) -> Dict[str, Any]:
    """
    Get statistics about the data.
    
    Args:
        data (List[List[str]]): Data to analyze
        
    Returns:
        Dict[str, Any]: Data statistics
    """
    if not data:
        return {
            'rows': 0,
            'columns': 0,
            'empty_cells': 0,
            'non_empty_cells': 0
        }
    
    rows = len(data)
    columns = len(data[0]) if data else 0
    
    empty_cells = 0
    non_empty_cells = 0
    
    for row in data:
        for cell in row:
            if cell and str(cell).strip():
                non_empty_cells += 1
            else:
                empty_cells += 1
    
    return {
        'rows': rows,
        'columns': columns,
        'empty_cells': empty_cells,
        'non_empty_cells': non_empty_cells,
        'total_cells': empty_cells + non_empty_cells
    }

def clean_data(data: List[List[str]]) -> List[List[str]]:
    """
    Clean data by removing empty rows and trimming whitespace.
    
    Args:
        data (List[List[str]]): Data to clean
        
    Returns:
        List[List[str]]: Cleaned data
    """
    if not data:
        return []
    
    cleaned = []
    for row in data:
        # Clean each cell
        cleaned_row = [str(cell).strip() if cell else '' for cell in row]
        
        # Only add row if it has at least one non-empty cell
        if any(cell for cell in cleaned_row):
            cleaned.append(cleaned_row)
    
    return cleaned

def merge_data_sets(data1: List[List[str]], data2: List[List[str]], merge_by_column: int = 0) -> List[List[str]]:
    """
    Merge two data sets by a common column.
    
    Args:
        data1 (List[List[str]]): First data set
        data2 (List[List[str]]): Second data set
        merge_by_column (int): Column index to merge by
        
    Returns:
        List[List[str]]: Merged data
    """
    if not data1 or not data2:
        return data1 if data1 else data2
    
    # Create lookup for data2
    data2_lookup = {}
    for row in data2:
        if merge_by_column < len(row):
            key = str(row[merge_by_column])
            data2_lookup[key] = row
    
    # Merge data
    merged = []
    for row1 in data1:
        if merge_by_column < len(row1):
            key = str(row1[merge_by_column])
            if key in data2_lookup:
                # Merge rows
                merged_row = row1 + data2_lookup[key]
                merged.append(merged_row)
            else:
                # Add row1 with empty values for data2 columns
                empty_cols = [''] * len(data2[0]) if data2 else []
                merged_row = row1 + empty_cols
                merged.append(merged_row)
    
    return merged 