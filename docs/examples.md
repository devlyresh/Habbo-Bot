# 📖 Habbo Bot Cookbook & Examples

This guide provides copy-paste snippets for common tasks. All code assumes you have an instance of the bot running (e.g., `bot = HabboClientGUI(...)`).

<br>

## 🏃 Movement

### 1. Basic Walking
Move the avatar to specific X, Y coordinates.

```python
# Walk to X=10, Y=10
bot.walk(10, 10)
```
### 2. Random Room Walking
This smart mode checks the room map (walls/furniture) and only walks to valid tiles.

```python
# Enable collision checking (Don't walk through walls)
bot.set_walk_room_aware(True)

# Start walking every 3 seconds
bot.walk_random(delay=3.0)

# Stop walking
# bot.stop_random_walk()
```

## 💬 Chat & Communication

### 1. Shouting (Bold Text)
Useful for getting attention. The style argument changes the speech bubble.

```python
# Style 1 = Normal
# Style 23 = Robot
# Style 18 = Dark
bot.shout("I am running on Python!", style=1)
```

### 2. Whispering
Send a private message to a user in the same room.
```python
target_username = "Steve"
bot.whisper(target_username, "Hey, I am a bot.", style=0)

```
### 3. Simple Auto-Reply Bot
Add this inside your main while loop to make the bot respond to chat.

```
import time

while bot.connected:
    # Check if a new message arrived in the last 0.5 seconds
    if bot.last_chat_message and (time.time() - bot.last_chat_time < 0.5):
        msg = bot.last_chat_message.lower()
        user = bot.last_chat_user_name
        
        # Ignore our own messages
        if user != bot.username:
            print(f"[{user}] said: {msg}")
            
            if "hello" in msg:
                bot.shout(f"Hi there, {user}!", style=1)
            elif "jump" in msg:
                bot.dance(1) # Start dancing
            
            # Clear message so we don't reply twice
            bot.last_chat_message = None
            
    time.sleep(0.1)
```

## 🕵️ Proxy Usage (Anti-Ban)
To run multiple bots safely, use SOCKS5 proxies. This hides your real IP address.
code
```python
# Format: protocol://username:password@ip:port
# Or just: protocol://ip:port

proxy_config = "socks5://user123:pass123@192.168.0.1:1080"

bot = HabboClientGUI(
    sso_ticket=ticket,
    bot_index=1,
    proxy=proxy_config, # <--- Pass the proxy here
    logger=logger
)

```

## 🤖 Advanced Logic
### 1. "Follow Bot" (Stalker Mode)
This script makes the bot constantly follow a specific user in the room.
code

```python
import time

TARGET_USER = "MyMainAccount"

while bot.connected:
    target_obj = None
    
    # Search for the user in the room cache
    # bot.users_in_room is a dict: {room_index: HabboUser object}
    for index, user in bot.users_in_room.items():
        if user.name == TARGET_USER:
            target_obj = user
            break
    
    if target_obj:
        # Walk to their coordinates
        # We check distance so we don't spam packets if we are already there
        if abs(target_obj.x - bot.x) > 1 or abs(target_obj.y - bot.y) > 1:
             bot.walk(target_obj.x, target_obj.y)
    else:
        print(f"Waiting for {TARGET_USER} to enter the room...")
        
    time.sleep(0.8) # Update every 0.8 seconds
```
## 2. Anti-AFK
Habbo kicks inactive users after ~15 minutes. This snippet prevents that.

```python
import random
import time

last_action = time.time()

while bot.connected:
    if time.time() - last_action > 300: # Every 5 minutes
        # Perform a tiny action
        action = random.choice(['wave', 'look_around'])
        
        if action == 'wave':
            bot.shout(" *waves* ", style=0)
        else:
            # Turn the bot's head slightly (Move to current position)
            # This refreshes the idle timer
            bot.walk(bot.x, bot.y)
            
        last_action = time.time()
    
    time.sleep(1)
```

### 👗 Appearance
## Change Outfit
You need a valid figure string.

```python
# Example: Blue shirt, jeans
figure_str = "ch-210-66.lg-270-82.sh-300-64"
bot.update_figure("M", figure_str)
```
