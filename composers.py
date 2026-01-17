from habbo_packet import HabboPacket
from constants import Outgoing

# =============================================================================
# CONNECTION & HANDSHAKE
# =============================================================================

def compose_unique_id(machine_id: str, fingerprint: str, platform: str) -> HabboPacket:
    """
    Composes the UniqueID packet (Packet 813).
    Sent during the login handshake to identify the device.
    
    Structure: {out:UniqueID}{s:machine_id}{s:fingerprint}{s:platform}
    """
    packet = HabboPacket(Outgoing.UNIQUE_ID)
    packet.write_string(machine_id)
    packet.write_string(fingerprint)
    packet.write_string(platform)
    return packet

def compose_latency_ping_request(request_id: int) -> HabboPacket:
    """
    Composes the LatencyPingRequest packet.
    The client MUST send this approximately every 10-20 seconds.
    Used to measure lag and keep the TCP connection alive.
    
    Structure: {out:LatencyPingRequest}{i:id}
    """
    packet = HabboPacket(Outgoing.LATENCY_PING_REQUEST)
    packet.write_integer(request_id)
    return packet

def compose_pong() -> HabboPacket:
    """
    Composes the Pong packet.
    Sent immediately after receiving a Ping (Packet 3928) from the server.
    
    Structure: {out:Pong} (Empty Body)
    """
    packet = HabboPacket(Outgoing.PONG)
    return packet

def compose_info_retrieve() -> HabboPacket:
    """
    Composes the InfoRetrieve packet (Packet 357).
    Sent after Authentication OK. Tells server to send our UserObject (Packet 1157).
    
    Structure: {out:InfoRetrieve} (Empty Body)
    """
    return HabboPacket(Outgoing.INFO_RETRIEVE)


# =============================================================================
# ROOM NAVIGATION & ENTRY
# =============================================================================

def compose_get_guest_room(room_id: int, enter_room: bool = True, room_forward: bool = False) -> HabboPacket:
    """
    Requests access to a room (Packet 2312).
    
    Structure: {out:GetGuestRoom}{i:room_id}{i:enter_flag}{i:forward_flag}
    
    Args:
        room_id: The ID of the room to join.
        enter_room: 1 = Enter immediately, 0 = Just load info.
        room_forward: 1 = Forwarded by another system, 0 = Normal click.
    """
    packet = HabboPacket(Outgoing.GET_GUEST_ROOM)
    packet.write_integer(room_id)
    packet.write_integer(1 if enter_room else 0)      # AS3 boolean-as-int
    packet.write_integer(1 if room_forward else 0)    # AS3 boolean-as-int
    return packet

def compose_quit_room() -> HabboPacket:
    """
    Leaves the current room and returns to Hotel View (Packet 2).
    
    Structure: {out:Quit} (Empty Body)
    """
    packet = HabboPacket(Outgoing.QUIT_ROOM)
    return packet

def compose_select_initial_room(room_template_id: str = "12") -> HabboPacket:
    """
    Used during the New User Experience (NUX) to pick a starter room.
    
    Structure: {out:SelectInitialRoom}{s:"12"}
    Note: The ID is sent as a String here, unlike normal room entry.
    """
    packet = HabboPacket(Outgoing.SELECT_INITIAL_ROOM)
    packet.write_string(room_template_id) 
    return packet

def compose_update_home_room(room_id: int) -> HabboPacket:
    """
    Sets the user's "Home" room.
    
    Structure: {out:UpdateHomeRoom}{i:room_id}
    """
    packet = HabboPacket(Outgoing.UPDATE_HOME_ROOM)
    packet.write_integer(room_id)
    return packet

def compose_new_navigator_search(category: str, data: str = "") -> HabboPacket:
    """
    Performs a search in the Room Navigator.
    
    Structure: {out:NewNavigatorSearch}{s:category}{s:query}
    
    Args:
        category: 'official_view', 'hotel_view', 'myworld_view', etc.
        data: The search query (empty string for default list).
    """
    packet = HabboPacket(Outgoing.NEW_NAVIGATOR_SEARCH)
    packet.write_string(category)
    packet.write_string(data)
    return packet

def compose_get_interstitial() -> HabboPacket:
    """
    Requests the interstitial (Ad) status. 
    Sent during room loading.
    
    Structure: {out:GetInterstitial}
    """
    return HabboPacket(Outgoing.GET_INTERSTITIAL)


# =============================================================================
# ROOM INTERACTION & MOVEMENT
# =============================================================================

def compose_move_avatar(x: int, y: int) -> HabboPacket:
    """
    Moves the avatar to specific coordinates.
    
    Structure: {out:MoveAvatar}{i:x}{i:y}
    """
    packet = HabboPacket(Outgoing.MOVE_AVATAR)
    packet.write_integer(x)
    packet.write_integer(y)
    return packet

def compose_dance(dance_id: int) -> HabboPacket:
    """
    Triggers a dance animation.
    0 = Stop, 1 = Normal, 2 = Pogo, 3 = Duck, 4 = Rollie.
    
    Structure: {out:Dance}{i:id}
    """
    packet = HabboPacket(Outgoing.DANCE)
    packet.write_integer(dance_id)
    return packet

def compose_sign(sign_id: int) -> HabboPacket:
    """
    Holds up a sign (0-14).
    
    Structure: {out:Sign}{i:id}
    """
    packet = HabboPacket(Outgoing.SIGN)
    packet.write_integer(sign_id)
    return packet

def compose_change_posture(posture_id: int) -> HabboPacket:
    """
    Changes stance (Sit/Stand).
    0 = Stand, 1 = Sit.
    
    Structure: {out:ChangePosture}{i:id}
    """
    packet = HabboPacket(Outgoing.CHANGE_POSTURE)
    packet.write_integer(posture_id)
    return packet

def compose_avatar_effect_activated(effect_id: int) -> HabboPacket:
    """
    STEP 1 of wearing an effect: Activates it from Inventory.
    
    Structure: {out:AvatarEffectActivated}{i:effect_id}
    """
    packet = HabboPacket(Outgoing.AVATAR_EFFECT_ACTIVATED)
    packet.write_integer(effect_id)
    return packet

def compose_avatar_effect_selected(effect_id: int) -> HabboPacket:
    """
    STEP 2 of wearing an effect: Visually applies it to the avatar.
    Pass -1 to remove current effect.
    
    Structure: {out:AvatarEffectSelected}{i:effect_id}
    """
    packet = HabboPacket(Outgoing.AVATAR_EFFECT_SELECTED)
    packet.write_integer(effect_id)
    return packet


# =============================================================================
# CHAT & COMMUNICATION
# =============================================================================

def compose_shout(message: str, style: int) -> HabboPacket:
    """
    Shouts a message (Bold text, visible further away).
    
    Structure: {out:Shout}{s:msg}{i:style}
    
    Args:
        message: The text to speak.
        style: The Bubble ID (0=Normal, 18=Dark, 23=Robot, etc).
    """
    packet = HabboPacket(Outgoing.SHOUT)
    packet.write_string(message)
    packet.write_integer(style)
    return packet

def compose_whisper(text: str, style: int = 0) -> HabboPacket:
    """
    Whispers to a specific user.
    
    Structure: {out:Whisper}{s:"TargetName Message"}{i:style}
    IMPORTANT: The target username is part of the string, separated by a space.
    """
    packet = HabboPacket(Outgoing.WHISPER)
    packet.write_string(text)
    packet.write_integer(style)
    return packet


# =============================================================================
# USER PROFILE & SOCIAL
# =============================================================================

def change_motto(motto: str) -> HabboPacket:
    """
    Updates the user's motto.
    
    Structure: {out:ChangeMotto}{s:motto}
    """
    packet = HabboPacket(Outgoing.CHANGE_MOTTO)
    packet.write_string(motto)
    return packet

def compose_update_figure(gender: str, figure: str) -> HabboPacket:
    """
    Updates the Avatar's visual appearance.
    
    Structure: {out:UpdateFigureData}{s:gender}{s:figure_string}
    Args:
        gender: "M" or "F".
        figure: Complex string (e.g., "lg-3023-82.ch-875...").
    """
    packet = HabboPacket(Outgoing.UPDATE_FIGURE)
    try:
        packet.write_string(str(gender or "M"))
    except Exception:
        packet.write_string("M")
    try:
        packet.write_string(str(figure or ""))
    except Exception:
        packet.write_string("")
    return packet

def compose_change_username(newname: str) -> HabboPacket:
    """
    Changes the username (Part of NUX or Name Change Tool).
    
    Structure: {out:ChangeUserName}{s:newname}
    """
    packet = HabboPacket(Outgoing.CHANGE_USERNAME)
    packet.write_string(newname)
    return packet

def compose_request_friend(username: str) -> HabboPacket:
    """
    Sends a friend request to the target username.
    
    Structure: {out:RequestFriend}{s:username}
    """
    packet = HabboPacket(Outgoing.REQUEST_FRIEND)
    packet.write_string(username)
    return packet

def compose_respect_user(user_id: int) -> HabboPacket:
    """
    Gives a "Respect" point to another user.
    
    Structure: {out:RespectUser}{i:user_id}
    """
    packet = HabboPacket(Outgoing.RESPECT_USER)
    packet.write_integer(user_id)
    return packet

def compose_replenish_respect() -> HabboPacket:
    """
    DevTool/Cheat Packet? 
    Observed sequence used to seemingly refresh respect count.
    
    Structure: {out:ReplenishRespect}{i:0}{i:0}{i:0}{i:2}{i:11}{i:1}
    """
    packet = HabboPacket(Outgoing.REPLENISH_RESPECT)
    packet.write_integer(0)
    packet.write_integer(0)
    packet.write_integer(0)
    packet.write_integer(2)
    packet.write_integer(11)
    packet.write_integer(1)
    return packet


# =============================================================================
# ECONOMY & REWARDS
# =============================================================================

def compose_purchase_from_catalog(page_id: int, item_id: int, extra_data: str, amount: int) -> HabboPacket:
    """
    Buys an item from the Catalog.
    
    Structure: {out:PurchaseFromCatalog}{i:page}{i:item}{s:extra}{i:amt}
    
    Args:
        page_id: The ID of the catalog page.
        item_id: The unique ID of the offer/item.
        extra_data: Specific text (e.g. for Trophies/Pets), usually empty.
        amount: Quantity (usually 1).
    """
    packet = HabboPacket(Outgoing.PURCHASE_FROM_CATALOG)
    packet.write_integer(page_id)
    packet.write_integer(item_id)
    packet.write_string(extra_data)
    packet.write_integer(amount)
    return packet

def compose_income_reward_status() -> HabboPacket:
    """
    Requests the status of the 'Income' (Daily/Level) Rewards.
    Must be sent before claiming.
    
    Structure: {out:IncomeRewardStatus}
    """
    return HabboPacket(Outgoing.INCOME_REWARD_STATUS)

def compose_income_reward_claim(reward_type: int) -> HabboPacket:
    """
    Claims a specific reward.
    
    Structure: {out:IncomeRewardClaim}{b:reward_type}
    NOTE: Uses write_byte (8-bit), not integer (32-bit).
    
    Args:
        reward_type: 0, 1, or 2 depending on the reward category.
    """
    packet = HabboPacket(Outgoing.INCOME_REWARD_CLAIM)
    packet.write_byte(reward_type)
    return packet