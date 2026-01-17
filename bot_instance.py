# bot_instance.py

import time
from collections import deque
from typing import TYPE_CHECKING
import threading

# Use TYPE_CHECKING to avoid circular import issues with HabboClientGUI
if TYPE_CHECKING:
    from habbo_client_gui import HabboClientGUI

class BotInstance:
    """A wrapper class to manage the state and logs of a single bot."""
    def __init__(self, account_data, index):
        self.account_data = account_data
        self.index = index # This is the 1-based index from the accounts.json file
        self.client: 'HabboClientGUI' = None
        self.status = "Idle"  # Idle, Preparing, Connecting, Connected, Disconnected, Stopped
        self.log_buffer = deque(maxlen=200) # Store last 200 log lines
        self.sso_ticket = None
        self.mute_info = None
        self.proxy_address = None 
        self.connect_thread: threading.Thread = None

    def add_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_buffer.append(f"[{timestamp}] {message}")
    def set_status(self, new_status: str):
        """Allows external classes like the client to update the bot's status."""
        self.status = new_status
        self.add_log(f"Status changed to: {new_status}")
    def get_display_name(self):
        """
        Generates a descriptive display name for the bot in the dashboard.
        Format: "Name (#Index) [Status] (ProxyIP)" or "Bot #Index [Status] (ProxyIP)".
        """
        # Step 1: Find the custom name from the account data
        name = None
        try:
            if isinstance(self.account_data, list):
                # Look for the special info object containing the name
                for item in self.account_data:
                    if isinstance(item, dict) and 'name' in item and 'domain' not in item:
                        name = item.get('name')
                        if name:  # Found a valid name, stop looking
                            break
        except Exception:
            pass  # Ignore errors if data format is unexpected

        # Step 2: Build the base name string, using the custom name if found
        if name:
            base_name = f"{name} (#{self.index})"
        else:
            base_name = f"Bot #{self.index}"

        # Step 3: Append the bot's current status
        display_str = f"{base_name} [{self.status}]"
        
        # Step 4: Append the proxy IP address, if one is assigned
        if self.proxy_address:
            try:
                # Safely split to avoid errors if the format is unexpected
                ip = self.proxy_address.split(':')[0]
                display_str += f" ({ip})"
            except Exception:
                pass # Don't crash if the proxy address string is malformed

        return display_str
    
    def set_mute_status(self, mute_string: str | None):
        """Sets or clears the secondary mute status information."""
        self.mute_info = mute_string
        if mute_string:
            self.add_log(f"Mute status updated: {mute_string}")
        else:
            self.add_log("Mute status cleared.")