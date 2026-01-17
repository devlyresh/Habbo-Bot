# parsers.py
from dataclasses import dataclass, field
import struct
from habbo_packet import Buffer

# -----------------------------------------------------------------------------
# DATA STRUCTURES (DTOs)
# -----------------------------------------------------------------------------

@dataclass
class NavigatorRoom:
    """Represents a single Room result in the Navigator search."""
    flat_id: int        # The unique ID of the room
    room_name: str
    owner_name: str
    user_count: int     # Current users inside
    max_user_count: int # Capacity (e.g. 25, 50)
    description: str

@dataclass
class HabboUser:
    """
    Represents an entity (Avatar) currently inside a Room.
    Parsed from the 'Users' packet.
    """
    web_id: int         # Global Account ID
    name: str
    motto: str
    figure: str         # Look string (e.g. "hr-100.hd-180...")
    room_index: int     # Local ID within the room (used for walking/chat packets)
    x: int
    y: int
    z: str              # Height as a string
    gender: str
    group_name: str
    achievement_score: int

@dataclass
class UserObject:
    """Represents the currently logged-in bot's own profile data."""
    user_id: int
    name: str
    last_access_date: str
    name_change_allowed: bool

# -----------------------------------------------------------------------------
# NAVIGATOR PARSERS
# -----------------------------------------------------------------------------

def parse_navigator_search_result(payload: bytes) -> list[NavigatorRoom]:
    """
    Parses Packet 537 (NavigatorSearchResultBlocks).
    
    Structure is complex and hierarchical:
    1. Search Meta Data (Code/Text)
    2. List of Categories/Blocks (e.g., "Popular", "Promoted")
    3. List of Rooms within those Categories
    
    Returns a flattened list of all unique rooms found.
    """
    buf = Buffer(payload)
    results = []
    
    # 1. Top Level Search Info
    _search_code = buf.read_string() # e.g., "official_view"
    _search_text = buf.read_string() # e.g., ""
    
    # 2. Result Blocks Loop
    block_count = buf.read_integer()
    
    for _ in range(block_count):
        _category_code = buf.read_string()
        _category_text = buf.read_string()
        _action_allowed = buf.read_integer()
        _is_collapsed = buf.read_boolean()
        _view_mode = buf.read_integer()
        
        # 3. Rooms Loop (Inside Block)
        room_count = buf.read_integer()
        
        for _ in range(room_count):
            # --- Standard Room Data ---
            flat_id = buf.read_integer()
            room_name = buf.read_string()
            owner_id = buf.read_integer()
            owner_name = buf.read_string()
            door_mode = buf.read_integer()
            user_count = buf.read_integer()
            max_user_count = buf.read_integer()
            description = buf.read_string()
            trade_mode = buf.read_integer()
            score = buf.read_integer()
            ranking = buf.read_integer()
            category_id = buf.read_integer()
            
            # --- Tags (e.g., "roleplay", "dating") ---
            tag_count = buf.read_integer()
            for _ in range(tag_count):
                _tag = buf.read_string()
            
            # --- Bitmask Flags ---
            # Habbo uses a bitmask to determine if extra data follows.
            # 1 = Official Room Image
            # 2 = Group Room Data
            # 4 = Room Promotion/Ad
            bitmask = buf.read_integer()
            
            # Official Room Display
            if (bitmask & 1) > 0:
                _official_name = buf.read_string()
                
            # Group Room Data
            if (bitmask & 2) > 0:
                _group_id = buf.read_integer()
                _group_name = buf.read_string()
                _group_badge = buf.read_string()
                
            # Room Ad Data
            if (bitmask & 4) > 0:
                _promo_name = buf.read_string()
                _promo_desc = buf.read_string()
                _promo_minutes = buf.read_integer()

            # Note: Newer headers might use bit 8, 16, etc.
            # Standard implementations usually stop checking at 4.

            results.append(NavigatorRoom(
                flat_id=flat_id,
                room_name=room_name,
                owner_name=owner_name,
                user_count=user_count,
                max_user_count=max_user_count,
                description=description
            ))
            
    return results


# -----------------------------------------------------------------------------
# USER / ENTITY PARSERS
# -----------------------------------------------------------------------------

def parse_user_object(payload: bytes) -> UserObject:
    """
    Parses Packet 1157 (UserObject).
    Contains details about the logged-in user.
    """
    buf = Buffer(payload)
    
    user_id = buf.read_integer()
    name = buf.read_string()
    buf.read_string() # Figure (Look)
    buf.read_string() # Gender
    buf.read_integer() # CustomData
    buf.read_integer() # RealName
    buf.read_boolean() # DirectMail
    buf.read_integer() # RespectTotal
    buf.read_integer() # RespectLeft
    buf.read_boolean() # StreamPublishing
    
    last_access_date = buf.read_string()
    name_change_allowed = buf.read_boolean()
    
    return UserObject(user_id, name, last_access_date, name_change_allowed)

def parse_noobness_level(payload: bytes) -> int:
    """
    Parses Packet 3228.
    Server uses this to determine if the user is 'New' (Noob).
    """
    buf = Buffer(payload)
    return buf.read_integer()

def parse_flat_created(payload: bytes) -> int:
    """
    Parses Packet 379 (FlatCreated).
    Sent after successfully creating a room.
    Returns: The new room_id (int).
    """
    buf = Buffer(payload)
    room_id = buf.read_integer()
    buf.read_string() # Room Name (ignore)
    return room_id

def parse_users(payload: bytes) -> list[HabboUser]:
    """
    Parses Packet 2887 (Users).
    Sent when entering a room or when new users appear.
    """
    users = []
    buf = Buffer(payload)
    
    count = buf.read_integer()
    for _ in range(count):
        web_id = buf.read_integer()
        name = buf.read_string()
        motto = buf.read_string()
        figure = buf.read_string()
        room_index = buf.read_integer() # Crucial for targeting actions
        x = buf.read_integer()
        y = buf.read_integer()
        z = buf.read_string()
        _body_direction = buf.read_integer() 
        
        user_type = buf.read_integer()
        
        # Defaults
        gender = ""
        group_name = ""
        achievement_score = 0

        # Type 1: Human User
        if user_type == 1:
            gender = buf.read_string()
            _group_id = buf.read_integer()
            _group_status = buf.read_integer()
            group_name = buf.read_string()
            _figure_string_update_marker = buf.read_string() 
            achievement_score = buf.read_integer()
            _is_moderator = buf.read_boolean()

        # Type 2: Pet (Cat/Dog/etc)
        elif user_type == 2:
            # Structure: SubType, OwnerId, OwnerName, Rarity, etc.
            # Skipped for bot simplicity
            pass
            
        # Type 4: Bot (Rentable/Public)
        elif user_type == 4:
            # Structure: BotOwnerId, BotOwnerName...
            pass
        
        # Only add valid users to the list
        user = HabboUser(
            web_id=web_id, name=name, motto=motto, figure=figure,
            room_index=room_index, x=x, y=y, z=z,
            gender=gender, group_name=group_name, achievement_score=achievement_score
        )
        users.append(user)
        
    return users

def parse_user_remove(payload: bytes) -> str:
    """
    Parses Packet 1069 (UserRemove).
    Sent when a user leaves the room or disconnects.
    Returns: The 'room_index' (as string) of the user to remove.
    """
    buf = Buffer(payload)
    room_index_str = buf.read_string()
    return room_index_str

def parse_flood_control(payload: bytes) -> int:
    """
    Parses Packet 1475 (FloodControl).
    Sent when the user is muted for spamming.
    Returns: Seconds remaining (int).
    """
    buf = Buffer(payload)
    seconds_remaining = buf.read_integer()
    return seconds_remaining


# -----------------------------------------------------------------------------
# ROOM MAPPING / GEOMETRY PARSERS
# -----------------------------------------------------------------------------

def parse_floor_height_map(payload: bytes, room_map):
    """
    Parses Packet 590 (FloorHeightMap).
    Defines the visual walls and floor layout.
    
    Logic:
    1. Reads a string map (e.g. "xxxxx\rxxxxx").
    2. Initializes the RoomMap 2D arrays.
    3. Guesses the Door location based on gaps in the wall.
    """
    buf = Buffer(payload)
    _use_legacy_parser = buf.read_boolean()
    _wall_height = buf.read_integer()

    map_string = buf.read_string()
    rows = map_string.strip().split('\r') # Rows are separated by Carriage Return

    room_map.height = len(rows)
    room_map.width = len(rows[0]) if room_map.height > 0 else 0

    # Initialize char map
    room_map.floor_map = [['' for _ in range(room_map.width)] for _ in range(room_map.height)]

    for y, row_str in enumerate(rows):
        for x, tile_char in enumerate(row_str):
            room_map.floor_map[y][x] = tile_char
    
    # --- IMPORTANT INITIALIZATION ---
    # We pre-fill the logical maps (heights, blockage) here with default values.
    # This ensures that if the 'HeightMap' packet (3055) arrives late or is malformed,
    # the bot won't crash when accessing coordinate [y][x].
    w, h = room_map.width, room_map.height
    room_map.tile_heights = [[0.0 for _ in range(w)] for _ in range(h)]
    room_map.stacking_blocked = [[False for _ in range(w)] for _ in range(h)]
    room_map.is_room_tile = [[False for _ in range(w)] for _ in range(h)]

    # --- Door Finding Heuristic ---
    # Loops through the map looking for a gap in the 'x' (walls).
    # This identifies where the avatar spawns when entering.
    door_x, door_y, door_dir = -1, -1, 0
    
    for y in range(room_map.height):
        for x in range(room_map.width):
            if room_map.floor_map[y][x].lower() == 'x':
                continue
            try:
                # Check for gap surrounded by 'x' (Door facing East)
                if rows[y-1][x] == 'x' and rows[y][x-1] == 'x' and rows[y+1][x] == 'x':
                    door_x, door_y, door_dir = x, y, 90
                    break
                # Check for gap (Door facing South)
                if rows[y-1][x] == 'x' and rows[y][x-1] == 'x' and rows[y][x+1] == 'x':
                    door_x, door_y, door_dir = x, y, 180
                    break
            except IndexError:
                continue
        if door_x != -1:
            break
            
    room_map.door_x = door_x
    room_map.door_y = door_y


def parse_height_map(payload: bytes, room_map):
    """
    Parses Packet 3055 (HeightMap).
    Contains raw Short Integers representing tile status (Stacking/Height).
    
    This packet does NOT contain width/height info; it relies on 
    `parse_floor_height_map` having run first.
    """
    width = room_map.width
    height = room_map.height

    if width == 0 or height == 0:
        return

    # Each tile is 2 bytes (Short)
    expected_size = width * height * 2
    raw_map_data = payload

    # Sanity check for data length
    if len(raw_map_data) != expected_size:
        raw_map_data = raw_map_data[:expected_size]

    # Bitmasks for tile flags
    # 0x4000 (1 << 14) -> Is Stacking Blocked?
    # 0x0200 (1 << 9)  -> Is it a valid Room Tile?
    # 0x3FFF           -> Remaining bits = Height Value * 256
    STACKING_BLOCKED_MASK = 1 << 14
    ROOM_TILE_MASK = 1 << 9 
    
    for y in range(height):
        for x in range(width):
            index = (y * width + x) * 2
            
            if index + 2 > len(raw_map_data):
                break 

            # Read unsigned short (>H could be used, but >h handles negatives if logic requires)
            tile_value = struct.unpack('>h', raw_map_data[index:index+2])[0]
            
            room_map.stacking_blocked[y][x] = (tile_value & STACKING_BLOCKED_MASK) != 0
            
            # If the bit is NOT set, it is a valid room tile (counter-intuitive logic)
            room_map.is_room_tile[y][x] = (tile_value & ROOM_TILE_MASK) == 0
            
            # Height calculation (Habbo stores height * 256)
            room_map.tile_heights[y][x] = (tile_value & 0x3FFF) / 256.0