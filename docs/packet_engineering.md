# 🛠️ Packet Engineering & Upgrading Guide

Habbo is a live service game. Every few weeks, the developers update the client. When this happens, **Packet Headers (IDs)** often change.

If your bot connects successfully but **actions (like Walking, Chatting, or Dancing) stop working**, it usually means the Packet ID for that action has changed.

This guide teaches you how to find the new IDs and update the code yourself.

<br>

## 🧰 Tools Required

1.  **[G-Earth](https://github.com/sirjonasxx/G-Earth)**: A powerful Packet Logger and Injector.
2.  **Habbo Official Client**: You need to log in normally (via the Launcher) to capture packets.

<br>

## 🔬 How to Find a Packet ID

Let's say the **DANCE** feature stops working. Here is how to fix it:

1.  **Open G-Earth** and connect it to the Habbo Client.
2.  Open the **Console / Logger** tab in G-Earth.
3.  **Clear the log** so it's empty.
4.  In the actual game window, perform the action (e.g., Start Dancing).
5.  Look at the G-Earth log. You will see an **Outgoing** packet appear immediately.

It will look something like this:

```text
[Outgoing] Header: 345, Length: 6, Data: {i:1}
Header: 345 -> This is the new Packet ID.
Data: {i:1} -> This is the payload. {i:1} means it is sending one Integer with value 1.
```

##  📝 Updating the Bot
Now that you have the new ID (345), you need to update the Python code.
Open constants.py.
Find the class named Outgoing.
Locate the variable for the action (e.g., DANCE).
Update the number.

```python
class Outgoing:
    # ... other packets ...
    
    # Old value was 785
    DANCE = 345  # <--- Update this to the number you found in G-Earth
    
    # ... other packets ...
```

Restart your bot. The feature will now work.

## 🏗️ Adding New Features
If you want to add a feature that the bot doesn't currently support (e.g., Scratching a Pet), follow this workflow:
### Step 1: Record the Packet
Scratch a pet in-game while G-Earth is running.
You see: [Outgoing] Header: 3201, Data: {i:55555}
(Note: 55555 is the Pet ID in this example).

### Step 2: Define the Header
Open constants.py and add the new ID to the Outgoing class.

```python
class Outgoing:
    # ... existing headers ...
    SCRATCH_PET = 3201
```

Step 3: Create the Composer
Open composers.py. You need to create a function that builds this packet.
Since the data was {i:55555}, we know we need to write one Integer.

```python
from constants import Outgoing
from habbo_packet import HabboPacket

def compose_scratch_pet(pet_id: int) -> HabboPacket:
    """
    Respects/Scratches a pet.
    Packet Structure: {Header}{Int:PetID}
    """
    packet = HabboPacket(Outgoing.SCRATCH_PET)
    packet.write_integer(pet_id)
    return packet
```


### Step 4: Use it in your script
Now you can use this function in your main.py or logic loop.

```python
from composers import compose_scratch_pet

# Scratch the pet with ID 55555
bot.send_packet(compose_scratch_pet(55555))
```

### 🌐 Resources
Sulek.dev API: An automatically updated database of Habbo Packet IDs and Structures. Check this site if you can't run G-Earth; they often list the current headers for US/COM hotels.
<br>
Discord: Join shuffleah on Discord if you are stuck or need the GUI version.
