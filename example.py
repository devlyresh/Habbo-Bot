import time
import threading
import sys

# Import our custom libraries
from sso_retriever import get_sso_ticket
from habbo_client import HabboClientGUI # Assuming your main class file is named habbo_client.py
import constants as const

# ============================================================================
# CONFIGURATION
# ============================================================================

# 1. YOUR HABBO COOKIES
# You must grab these from your browser (F12 -> Network -> Filter: clientnative/url -> Request Headers)
# You need 'session.id' and 'browser_token'.
MY_COOKIES = [
    {"name": "session.id", "value": "your session id"},
    {"name": "browser_token", "value": "your browser token"}
]

# 2. PROXY SETTINGS (Optional)
# Format: "ip:port" or "ip:port:user:pass"
# Leave as None to use your own IP.
PROXY_URL = None 

# 3. TARGET ROOM ID
# 80257391 is usually the "Welcome Lounge" or a Public Room ID in .com
TARGET_ROOM_ID = 80257391 

# ============================================================================
# LOGGING HELPER
# ============================================================================
def logger(msg):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [BOT] {msg}")

# ============================================================================
# MAIN BOT LOGIC
# ============================================================================
def run_example_bot():
    print("--- Habbo Python Client Example ---")

    # Step 1: Get SSO Ticket
    logger("Fetching SSO Ticket...")
    ticket = get_sso_ticket(MY_COOKIES, PROXY_URL)
    
    if not ticket:
        logger("❌ Failed to get SSO Ticket. Check your cookies.")
        sys.exit(1)
        
    logger(f"Got Ticket: {ticket[:10]}...")

    # Step 2: Initialize Client
    # We pass '1' as bot_index just for internal naming
    bot = HabboClientGUI(
        sso_ticket=ticket,
        bot_index=1,
        proxy=PROXY_URL if PROXY_URL else "127.0.0.1:0", # Dummy proxy if None
        logger=logger
    )

    # Step 3: Connect via TCP
    if bot.connect():
        logger("✅ Connected to Habbo Game Server!")
    else:
        logger("❌ Failed to connect to Game Server.")
        sys.exit(1)

    # Step 4: Join a Room
    logger(f"Joining Room ID: {TARGET_ROOM_ID}...")
    bot.join_room(TARGET_ROOM_ID)

    # Step 5: Wait for Room Load (HeightMap)
    # The client has an internal event that triggers when the room geometry is loaded
    if bot._in_room_event.wait(timeout=10.0):
        logger("🏠 Successfully entered the room!")
    else:
        logger("⚠️ Timed out waiting for room load (Maybe room is full or locked?)")

    # ========================================================================
    # GAMEPLAY DEMO
    # ========================================================================
    
    try:
        # A. Walk to specific coordinates (x=5, y=5)
        logger("Walking to (5, 5)...")
        bot.walk(5, 5)
        time.sleep(2)

        # B. Shout something
        logger("Shouting message...")
        bot.shout("Hello from Python! 🐍", style=1) # Style 1 = Normal Bubble
        time.sleep(2)

        # C. Dance
        logger("Dancing...")
        bot.dance(1) # 1 = Normal Dance
        time.sleep(3)
        bot.dance(0) # Stop Dancing

        # D. Random Walk (Room Aware)
        # This uses the RoomMap to only pick valid tiles
        logger("Starting Random Walk...")
        bot.set_walk_room_aware(True)
        bot.walk_random(delay=2.5) # Move every 2.5 seconds

        # Keep the script running to listen for chat/events
        while bot.connected:
            # Simple interaction: Echo chat
            if bot.last_chat_message and (time.time() - bot.last_chat_time < 1.0):
                msg = bot.last_chat_message
                user = bot.last_chat_user_name
                
                # Check so we don't reply to ourselves
                if user != bot.username: 
                    logger(f"Heard {user}: {msg}")
                    # Simple command
                    if msg == "!ping":
                        bot.shout(f"Pong! {user}")
                        bot.last_chat_message = None # Clear it so we don't spam

            time.sleep(0.1)

    except KeyboardInterrupt:
        logger("Stopping bot...")
    finally:
        bot.stop_random_walk()
        bot.disconnect()
        logger("Disconnected.")

if __name__ == "__main__":

    run_example_bot()
