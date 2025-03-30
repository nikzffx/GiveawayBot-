import re
import datetime
from typing import Dict, Union, Optional

def parse_time(time_string: str) -> int:
    """
    Parse a time string into seconds
    
    Formats supported:
    - Xs: X seconds
    - Xm: X minutes
    - Xh: X hours
    - Xd: X days
    - Any combination of the above (e.g., 1d12h30m)
    
    Args:
        time_string: The time string to parse
        
    Returns:
        The time in seconds
    
    Raises:
        ValueError: If the time string format is invalid
    """
    if not time_string:
        raise ValueError("Time string cannot be empty")
    
    # Define the regex pattern to match time units
    pattern = r'(\d+)([smhd])'
    
    # Find all matches in the time string
    matches = re.findall(pattern, time_string.lower())
    
    if not matches:
        raise ValueError(f"Invalid time format: {time_string}")
    
    # Define multipliers for each unit
    multipliers = {
        's': 1,           # seconds
        'm': 60,          # minutes
        'h': 3600,        # hours
        'd': 86400        # days
    }
    
    # Calculate the total duration in seconds
    total_seconds = 0
    for value, unit in matches:
        if unit not in multipliers:
            raise ValueError(f"Invalid time unit: {unit}")
        
        total_seconds += int(value) * multipliers[unit]
    
    return total_seconds

def format_time_remaining(seconds: Union[int, float]) -> str:
    """
    Format time in seconds to a human-readable string
    
    Args:
        seconds: The time in seconds
        
    Returns:
        A formatted string like "1d 12h 30m 15s"
    """
    seconds = max(0, int(seconds))
    
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

def create_discord_timestamp(timestamp: Union[int, float], format_type: str = "f") -> str:
    """
    Create a Discord formatted timestamp that will display in the user's local time zone
    
    Args:
        timestamp: Unix timestamp (seconds since epoch)
        format_type: Discord timestamp format type:
            - 't': Short time (e.g., "9:41 PM")
            - 'T': Long time (e.g., "9:41:30 PM")
            - 'd': Short date (e.g., "04/20/2021")
            - 'D': Long date (e.g., "April 20, 2021")
            - 'f': Short date/time (default) (e.g., "April 20, 2021 9:41 PM")
            - 'F': Long date/time (e.g., "Tuesday, April 20, 2021 9:41 PM")
            - 'R': Relative time (e.g., "2 hours ago")
    
    Returns:
        A Discord timestamp that will display in the user's local time zone
    """
    return f"<t:{int(timestamp)}:{format_type}>"

def format_end_time(end_time: Union[int, float]) -> dict:
    """
    Format end time into multiple useful formats for display
    
    Args:
        end_time: Unix timestamp (seconds since epoch)
        
    Returns:
        Dictionary containing formatted time strings for various display formats
    """
    # Convert to datetime for formatting
    dt = datetime.datetime.fromtimestamp(end_time)
    formatted_utc = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Create various Discord timestamp formats
    # Short date/time format (e.g., "April 20, 2021 9:41 PM")
    discord_absolute = create_discord_timestamp(end_time, "f") 
    
    # Long date/time format (e.g., "Tuesday, April 20, 2021 9:41 PM")
    discord_long = create_discord_timestamp(end_time, "F")
    
    # Relative time (e.g., "in 2 hours", "in 3 days")
    discord_relative = create_discord_timestamp(end_time, "R")
    
    # Short time only (e.g., "9:41 PM")
    discord_time = create_discord_timestamp(end_time, "t")
    
    # Short date only (e.g., "04/20/2021")
    discord_date = create_discord_timestamp(end_time, "d")
    
    return {
        # Standard formats
        "absolute": formatted_utc,
        "timestamp": end_time,
        
        # Discord auto-converting formats
        "discord_absolute": discord_absolute,
        "discord_long": discord_long, 
        "discord_relative": discord_relative,
        "discord_time": discord_time,
        "discord_date": discord_date,
        
        # Formatted strings for direct use
        "local": f"Local time: {discord_absolute}",
        "local_long": f"Local time: {discord_long}",
        "countdown": discord_relative,
        
        # Compact format for inline display
        "compact": f"{discord_relative} ({discord_time})"
    }
