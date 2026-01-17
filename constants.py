# constants.py
import hashlib
import uuid

# =============================================================================
# CONNECTION CONFIGURATION
# =============================================================================

HABBO_HOST = "game-us.habbo.com"
HABBO_PORT = 30000
TIMEOUT = 10

# Files
ACCOUNTS_FILE = "accounts.json"

# =============================================================================
# CLIENT IDENTIFICATION & FINGERPRINTING
# =============================================================================
# These values mimic the Flash/Air client version to avoid "Outdated Client" errors.

RELEASE_VERSION = "WIN63-202511041237-472105733"
CLIENT_TYPE = "FLASH25"
PLATFORM_ID = 6
CLIENT_VERSION = 4
EXTERNAL_VARIABLES_URL = "https://www.habbo.com/gamedata/external_variables/1"

# Static Machine/Fingerprint Info
# In a real scenario, you might want to randomize these per bot instance.
STATIC_MACHINE_ID = "" 
STATIC_FINGERPRINT = "~a239d36007e0c37b48238796aa759aa"
STATIC_PLATFORM_STRING = "WIN/51,1,1,5"

def generate_md5_fingerprint():
    """
    Generates a random 32-char MD5 fingerprint based on a new UUID.
    Used during the login handshake to identify the 'device'.
    """
    random_data = str(uuid.uuid4()).encode('utf-8')
    return f"~{hashlib.md5(random_data).hexdigest()}"

# =============================================================================
# CRYPTOGRAPHY
# =============================================================================
# The RSA Public Key used to encrypt the Diffie-Hellman handshake.
# This specific key is generally static for the Habbo PC/Flash client.

RSA_MODULUS_HEX = "C5DFF029848CD5CF4A84ADEFB2DA6685704920D5EBE8850B82C419A97B95302DE3B8021F37719FEBD4B3516E04D1E4702E74C468C9FF4BBBB5DD44A1E3A08687EDBEF7C30A176F7C8C83226A77F7982F7442D884D8149E924C486F43035C07B9167EA998416919DA4116D5E0598C11BA1542B4160136F04135C06EDF80170245E73C0DAD63895F52DCED3735582C5852744C8EC40AF576F26A9C8DC5B64ED3DAD40EFAAC6A76A1F5C2A422A8A4691F8991356467BDA61E1D34D0F35531058C8F741E4661ACFCB15C806A996AC312A8D33BF45079B89E11787537B37364749B883BDBFDE51A1A55086CF16159F5DEBCC76342AC2EF6950DA0C70C5845C97DFD49"
RSA_EXPONENT_HEX = "10001"

# =============================================================================
# GAME DATA (FIGURES & ADMINS)
# =============================================================================

# Used for NUX (New User Experience) randomization
RANDOM_FIGURES_MALE = [
    "ch-255-64.hr-893-31.sh-3068-64-1408.lg-3088-64-1408.hd-208-10",
    "ha-1018-0.sh-305-64.lg-3023-64.hd-180-1.ch-225-88.hr-155-40.cc-3294-88-88",
    "ha-1020-0.sh-3115-64-1408.lg-3078-1408.hd-209-1370.ch-255-90.hr-125-31.ca-1804-73",
    "ch-809-83.hr-110-44.sh-300-64.lg-270-84.hd-200-30",
    "ha-1013-1408.sh-908-1408.lg-275-64.hd-209-10.ch-255-82.hr-170-31",
    "ch-255-66.hr-3090-34.sh-3068-1320-1408.lg-3023-66.hd-209-10",
    "ch-808-85.hr-125-48.lg-3078-64.hd-205-1371",
    "ha-1004-91.lg-3078-91.ea-1404-64.hd-190-19.ch-3030-71.hr-170-45.cp-3288-64.he-1608-0",
    "ea-1404-64.ch-267-64.lg-3078-1408.wa-2009-1408.sh-906-1408.hd-208-10.hr-125-42.fa-1208-91",
    "ea-1406-0.ch-210-1408.lg-3216-72.wa-3074-1320-1320.he-1610-0.ca-1802-0.sh-905-72.hd-207-10.hr-170-45.cc-3294-83-73.fa-1201-0",
    "sh-305-1408.hd-180-14.ch-267-1408.lg-280-64.hr-170-31",
    "ea-1404-64.ch-220-81.lg-285-64.sh-290-1408.hd-205-10.hr-3090-45.fa-1201-0",
    "ch-3111-82-1408.lg-285-64.sh-290-64.hd-180-1.hr-170-34.fa-1210-0",
]

RANDOM_FIGURES_FEMALE = [
    "ca-1804-83.hd-629-1.ch-685-73.lg-3216-1408.sh-907-1408.hr-890-36",
    "hd-600-1.ch-685-82.lg-3088-64-1408.he-3274-82.sh-735-82.hr-890-45",
    "hd-600-10.ch-813-82.lg-710-82.he-1602-81.fa-3276-72.sh-905-82.hr-890-34",
    "hd-629-10.sh-3068-1408-71.hr-890-31.ch-665-1408.lg-3216-74",
    "hd-615-1.ch-816-73.lg-695-64.fa-3276-73.sh-907-64.hr-681-45",
    "hd-600-10.ch-660-73.lg-720-91.fa-3276-73.sh-740-1408.hr-515-44",
    "hd-600-1.sh-3068-1408-1408.hr-545-31.ch-665-1408.lg-3216-91",
    "hd-600-1371.sh-3068-1408-1408.hr-545-31.ch-665-1408.lg-3216-91",
    "hd-600-1371.ch-665-73.lg-720-91.fa-1212-73.ea-1404-64.sh-740-1408.hr-550-44"
]

# List of known admins/staff. Used for auto-disconnect safety logic.
ADMINS = [
    "noodlesoup","knitty","GentleTeapot","TheWeatherFrog","Alyx_Staff",
    "Amaiazing","WaltzMatilda","sparkaro","Guaja","Truculencia","istanbul",
    "Olsoweir","Natunen","-LittleMin","PrincessTwinkle"
]

# =============================================================================
# PACKET HEADERS (OUTGOING)
# =============================================================================

class Outgoing:
    # Handshake
    CLIENT_HELLO = 4000
    INIT_DIFFIE_HANDSHAKE = 1445
    COMPLETE_DIFFIE_HANDSHAKE = 3393
    VERSION_CHECK = 1422
    UNIQUE_ID = 760
    SSO_TICKET = 3674
    INFO_RETRIEVE = 3745
    
    # Ping/Pong
    LATENCY_PING_REQUEST = 1255
    PONG = 2418
    
    # Room Entry & Navigation
    GET_GUEST_ROOM = 2158
    GET_INTERSTITIAL = 1452
    QUIT_ROOM = 765
    SELECT_INITIAL_ROOM = 1993
    UPDATE_HOME_ROOM = 763
    NEW_NAVIGATOR_SEARCH = 3780
    
    # Room Interaction
    MOVE_AVATAR = 1551
    SHOUT = 901
    WHISPER = 1758
    DANCE = 785
    SIGN = 1153
    CHANGE_POSTURE = 2980
    RESPECT_USER = 2911
    REPLENISH_RESPECT = 2865
    
    # User Profile
    CHANGE_MOTTO = 2599
    UPDATE_FIGURE = 1724
    CHANGE_USERNAME = 3685
    REQUEST_FRIEND = 1718
    
    # Inventory / Effects / Catalog
    AVATAR_EFFECT_ACTIVATED = 1639
    AVATAR_EFFECT_SELECTED = 2538
    PURCHASE_FROM_CATALOG = 3853
    INCOME_REWARD_STATUS = 3488
    INCOME_REWARD_CLAIM = 649


# =============================================================================
# PACKET HEADERS (INCOMING)
# =============================================================================

class Incoming:
    # Handshake
    SERVER_INIT_DIFFIE_HANDSHAKE = 503
    SERVER_COMPLETE_DIFFIE_HANDSHAKE = 3722
    AUTHENTICATION_OK = 115
    REQUEST_MACHINE_ID = 2200
    
    # General
    PING = 2829
    LATENCY_PING_RESPONSE = 1380
    FLOOD_CONTROL = 1475
    
    # Room Data
    USERS = 2887
    USER_REMOVE = 1069
    FLOOR_HEIGHT_MAP = 590
    HEIGHT_MAP = 3055
    ROOM_ENTRY_TILE = 1251
    NAVIGATOR_SEARCH_RESULT_BLOCKS = 537
    FLAT_CREATED = 379 
    
    # User Data
    USER_OBJECT = 1157
    NOOBNESS_LEVEL = 3228