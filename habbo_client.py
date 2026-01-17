

import random
import socket
import string
import socks  # Used for SOCKS5 proxy support (PySocks)
import struct  # Used for packing/unpacking binary data (integers, shorts)
import secrets # Cryptographically strong random number generation
import time
import threading
import traceback
from base64 import b64decode

# Cryptography libraries for Habbo's RSA/DH Handshake
from Crypto.PublicKey import RSA
from ArcFour import ArcFour

# Custom packet composers (Outgoing packets)
from composers import (
    compose_avatar_effect_activated, compose_avatar_effect_selected, compose_get_guest_room, 
    compose_income_reward_claim, compose_income_reward_status, compose_purchase_from_catalog, 
    compose_whisper, compose_get_interstitial, compose_move_avatar, compose_pong, 
    compose_latency_ping_request, compose_quit_room, compose_shout, change_motto,
    compose_dance, compose_sign, compose_request_friend, compose_change_posture, 
    compose_respect_user, compose_replenish_respect,
    compose_update_figure, compose_change_username, compose_select_initial_room, 
    compose_update_home_room, compose_info_retrieve, compose_new_navigator_search
)

# Core networking wrappers
from habbo_packet import HabboPacket, Buffer
import constants as const

# Incoming packet parsers
from parsers import (
    parse_flood_control, parse_users, parse_user_remove, HabboUser, 
    parse_floor_height_map, parse_height_map,
    parse_user_object, parse_flat_created, parse_navigator_search_result
)
from room_map import RoomMap

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS & CONSTANTS
# -----------------------------------------------------------------------------

# Helper lambda for decoding Base64 strings at runtime (simple obfuscation/encoding wrapper)
_s = lambda b: b64decode(b).decode('utf-8')

# Mapping of Disconnect Reason IDs (Packet 4000) to human-readable strings.
# This helps debug why a bot was kicked (Ban, Maintenance, etc.).
DISCONNECT_REASONS = {
    -2: "Maintenance Break", 
    0: "Logged Out", 
    1: "Banned (Just Banned)", 
    10: "Banned (Still Banned)",
    2: "Concurrent Login", 
    13: "Concurrent Login", 
    11: "Concurrent Login", 
    18: "Concurrent Login",
    12: "Hotel Closed", 
    19: "Hotel Closed", 
    20: "Incorrect Password", 
    112: "Idle Timeout",
    122: "Incompatible Client Version"
}

class BanDetectedException(Exception): 
    """Custom exception raised when the server explicitly sends a ban packet."""
    pass

class HabboClientGUI:
    """
    Main Bot Client Class.
    
    Handles:
    - TCP/SOCKS5 Connection
    - Diffie-Hellman Key Exchange & RSA Authentication
    - Packet Encryption/Decryption (ArcFour/RC4)
    - Background Threading (Keep-alive, Listening)
    - High-level Game Actions (Walking, Chatting, etc.)
    """
    
    def __init__(self, sso_ticket, bot_index: int, proxy: str, logger=None, 
                 status_updater=None, mute_updater=None, 
                 admin_auto_leave_enabled: bool = False, 
                 navigator_callback=None):
        
        # Word lists used for generating random "Meme" nicknames during NUX (New User Experience).
        self.MEME_NAMES = [
            # Requested / Edgy / Figures
            "Ted", "Putin", "Jeffrey", "Epstn", "Diddy", "Osama", "Kanye", "Elon", "Zuck", "Bezos",
            "Trump", "Biden", "Obama", "Tate", "Tristan", "Adin", "Speed", "Kai", "XQC",
            "Rizz", "Sigma", "Alpha", "Beta", "Omega", "Giga", "Chad", "Stacy", "Karen", "Kyle",
            
            # Meme Culture & Random
            "Doge", "Pepe", "Wojak", "Doomer", "Zoomer", "Boomer", "Shrek", "Thanos", "Joker",
            "Gotham", "Wayne", "Stark", "Vader", "Yoda", "Sonic", "Sanic", "Knuckles",
            "Goku", "Vegeta", "Naruto", "Sasuke", "Luffy", "Zoro", "Nami", "Light", "L",
            "Walter", "Jesse", "Saul", "Gus", "Mike", "Homelander", "Butcher",
            
            # Verbs/Adjectives to mix in
            "Based", "Cringe", "Epic", "Dark", "Lil", "Big", "Yung", "Dr", "Mr", "Sir",
            "Lord", "King", "God", "Demon", "Angel", "Saint", "Slayer", "Hunter", "Master",
            "Simp", "Incel", "Femcel", "Virgin", "Wizard", "Goblin", "Gremlin", "Rat",
            "Toxic", "Salty", "Sweaty", "Tryhard", "Noob", "Pro", "Hacker", "Bot",
            
            # Tech / Crypto
            "Bitcoin", "Ether", "Crypto", "Nft", "Moon", "Mars", "Tesla", "Twitter", "X",
            "Linux", "Python", "Java", "Coder", "Dev", "Admin", "Mod", "Staff"
        ]
        
        # Connection Config
        self.host = const.HABBO_HOST
        self.port = const.HABBO_PORT
        self.sso_ticket = sso_ticket  # The auth token from the web launcher
        self.bot_index = bot_index
        # Obfuscated default username placeholder
        self.username = _s(b'Qm90IHt9').format(bot_index)
        self.proxy_address = proxy
        
        # Network State
        self.sock = None
        self.outgoing_cipher = None  # RC4 Encryptor
        self.incoming_cipher = None  # RC4 Decryptor
        self.start_time_ms = 0
        self.connected = False
        self.is_banned = False
        
        # Room State
        self.room_map = RoomMap()  # Stores walls/floor nodes
        self.pending_height_map_payload = None
        self.users_in_room: dict[int, HabboUser] = {}
        
        # Threading
        self.listener_thread = None
        self.latency_pinger_thread = None
        self._random_walk_thread = None
        self._is_walking_randomly = False
        self._walk_room_aware = True
        self.send_lock = threading.Lock() # Prevents race conditions on socket.send
        
        # Event to track if we successfully entered a room (received heightmap)
        self._in_room_event = threading.Event()
        
        # UI/Logic Callbacks
        self.navigator_callback = navigator_callback if callable(navigator_callback) else lambda x: None
        self.status_updater = status_updater if callable(status_updater) else lambda s: None
        self.mute_updater = mute_updater if callable(mute_updater) else lambda s: None
        
        # Crypto Setup (RSA Public Key Construction)
        n = int(const.RSA_MODULUS_HEX, 16)
        e = int(const.RSA_EXPONENT_HEX, 16)
        self.rsa_key = RSA.construct((n, e))
        self.rsa_key_size = (self.rsa_key.n.bit_length() + 7) // 8
        self.log = logger if callable(logger) else print
        
        # Misc State
        self.latency_ping_request_id = 0
        self._left_due_to_admin = False
        self.admin_auto_leave_enabled = bool(admin_auto_leave_enabled)
        self._nux_running = False

        # Real-time Chat Tracking
        self.last_chat_user_name = None 
        self.last_chat_message = None
        self.last_chat_time = 0

    # -------------------------------------------------------------------------
    # NETWORK CONNECTION & HANDSHAKE
    # -------------------------------------------------------------------------

    def connect(self) -> bool:
        """
        Establishes the SOCKS5 connection, performs the handshake, and waits for login.
        Returns True if Authentication was successful, False otherwise.
        """
        self.start_time_ms = int(time.time() * 1000)
        self.is_banned = False
        try:
            
            
            # Initialize SOCKS socket
            self.sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_parts = self.proxy_address.strip().split(':')
            
            # Handle different Proxy formats (IP:Port or IP:Port:User:Pass)
            if len(proxy_parts) == 2:
                proxy_ip, proxy_port_str = proxy_parts
                proxy_port = int(proxy_port_str)
                self.sock.set_proxy(socks.SOCKS5, proxy_ip, proxy_port, rdns=True)
            elif len(proxy_parts) == 4:
                proxy_ip, proxy_port_str, proxy_user, proxy_pass = proxy_parts
                proxy_port = int(proxy_port_str)
                self.sock.set_proxy(socks.SOCKS5, proxy_ip, proxy_port, username=proxy_user, password=proxy_pass, rdns=True)
            else:
                raise ValueError("Invalid proxy format")

            # Connect to server
            self.sock.settimeout(30.0)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(60.0) 
            
            self.connected = True
            self.log("Socket connected.")

            # Perform Diffie-Hellman Handshake & Send Login
            self._do_handshake()
            self._send_login_details()

            self.log("Waiting for login flow...")
            
            # Loop briefly to wait for Authentication OK
            login_deadline = time.time() + 15.0
            while time.time() < login_deadline:
                packet_id, payload = self._receive_packet()
                
                if packet_id == 4000: # Disconnect Packet
                    self._handle_disconnect_reason(payload)

                if packet_id == const.Incoming.PING:
                    self.send_packet(compose_pong())
                    continue

                if packet_id == const.Incoming.FLOOD_CONTROL:
                    seconds = parse_flood_control(payload)
                    mute_status = self._format_mute_time(seconds)
                    self.mute_updater(mute_status) 
                    continue

                if packet_id == const.Incoming.AUTHENTICATION_OK:
                    self.log("AUTHENTICATION OK!")
                    # Send basic info retrieval (User Object)
                    self.send_packet(compose_info_retrieve())

                    # Start background threads for listening and pings
                    self.listener_thread = threading.Thread(target=self._listen_for_packets, daemon=True)
                    self.listener_thread.start()
                    self.latency_pinger_thread = threading.Thread(target=self._start_latency_pinger, daemon=True)
                    self.latency_pinger_thread.start()
                    return True
                
                if packet_id == 1510: # Explicit Ban Packet
                    self.is_banned = True
                    raise BanDetectedException("Received ban packet (1510) during login.")

            self.log("LOGIN FAILED! Timed out.")
            self.disconnect()
            return False
        
        except BanDetectedException as e:
            self.log(f"BAN DETECTED: {e}")
            self.is_banned = True
            self.disconnect()
            return False

        except Exception as e:
            self.log(f"Connection failed: {e}")
            self.disconnect()
            return False

    def _do_handshake(self):
        """
        Executes the Habbo Encryption Protocol (Diffie-Hellman Key Exchange).
        1. Send ClientHello.
        2. Init Diffie-Handshake.
        3. Calculate Shared Secret using Server's Prime/Generator.
        4. Initialize RC4 (ArcFour) stream cipher.
        """
        # 1. Send Client Hello
        client_hello = HabboPacket(const.Outgoing.CLIENT_HELLO)
        client_hello.write_string(const.RELEASE_VERSION)
        client_hello.write_string(const.CLIENT_TYPE)
        client_hello.write_integer(const.PLATFORM_ID)
        client_hello.write_integer(const.CLIENT_VERSION)
        self._send_plaintext_packet(client_hello)
        
        # 2. Init Diffie Handshake
        init_dh = HabboPacket(const.Outgoing.INIT_DIFFIE_HANDSHAKE)
        self._send_plaintext_packet(init_dh)
        
        # Wait for Server Init
        while True:
            packet_id, payload = self._receive_packet()
            if packet_id == 1510: 
                self.is_banned = True
                raise BanDetectedException("Ban packet (1510)")
            if packet_id == 4000: self._handle_disconnect_reason(payload)
            if packet_id == const.Incoming.SERVER_INIT_DIFFIE_HANDSHAKE: break
            if packet_id == const.Incoming.PING: continue
        
        # 3. Process Server Key Data
        payload_buffer = Buffer(payload)
        p_str = payload_buffer.read_string(); g_str = payload_buffer.read_string()
        p, g = self._rsa_verify_and_unpad(p_str), self._rsa_verify_and_unpad(g_str)
        
        # Generate Client Private Key
        client_private_key = int(secrets.token_hex(15), 16)
        client_public_key = pow(g, client_private_key, p)
        
        # Send Completed Handshake
        complete_dh = HabboPacket(const.Outgoing.COMPLETE_DIFFIE_HANDSHAKE)
        complete_dh.write_string(self._rsa_pad_and_encrypt(str(client_public_key).encode('utf-8')))
        self._send_plaintext_packet(complete_dh)
        
        # Wait for Server Complete
        while True:
            packet_id, payload = self._receive_packet()
            if packet_id == 1510: 
                self.is_banned = True
                raise BanDetectedException("Ban packet (1510)")
            if packet_id == 4000: self._handle_disconnect_reason(payload)
            if packet_id == const.Incoming.SERVER_COMPLETE_DIFFIE_HANDSHAKE: break
            if packet_id == const.Incoming.PING:
                self._send_plaintext_packet(compose_pong())
                continue

        # 4. Initialize Encryption (RC4)
        payload_buffer = Buffer(payload)
        server_public_key_str = payload_buffer.read_string()
        server_client_encryption_enabled = payload_buffer.read_boolean()
        
        server_public_key = self._rsa_verify_and_unpad(server_public_key_str)
        shared_secret = pow(server_public_key, client_private_key, p)
        shared_secret_hex = f'{shared_secret:x}'
        if len(shared_secret_hex) % 2: shared_secret_hex = '0' + shared_secret_hex
        shared_secret_bytes = bytes.fromhex(shared_secret_hex)
        
        self.outgoing_cipher = ArcFour(shared_secret_bytes)
        # Server might optionally enable incoming encryption
        if server_client_encryption_enabled: 
            self.incoming_cipher = ArcFour(shared_secret_bytes)
        else: 
            self.incoming_cipher = None

    def _handle_disconnect_reason(self, payload: bytes):
        """Parses Packet 4000 to determine why the server closed the connection."""
        try:
            reason_id = struct.unpack('>i', payload)[0]
            reason_str = DISCONNECT_REASONS.get(reason_id, "Generic/Unknown")
            self.log(f"SERVER DISCONNECT (4000): {reason_id} -> '{reason_str}'")
            if reason_id == 1 or reason_id == 10:
                self.log("BAN CONFIRMED via Packet 4000")
                self.is_banned = True
                raise BanDetectedException(f"Banned: {reason_str}")
        except BanDetectedException:
            raise
        except Exception: pass

    # -------------------------------------------------------------------------
    # MAIN RECEIVE LOOP
    # -------------------------------------------------------------------------

    def _listen_for_packets(self):
        """
        Main Loop: Reads packets, decrypts them, and dispatches them to handlers.
        Runs in a separate thread.
        """
        try:
            while self.connected:
                packet_id, payload = self._receive_packet()

                # --- 1. USER UPDATE (MOVEMENT) ---
                # Packet 1030 contains position updates for avatars in the room.
                if packet_id == 1030: 
                    try:
                        buf = Buffer(payload)
                        count = buf.read_integer()  # Number of updates
                        for _ in range(count):
                            index = buf.read_integer()  # Room Index
                            x = buf.read_integer()      # X
                            y = buf.read_integer()      # Y
                            z = buf.read_string()       # Z (Height)
                            head = buf.read_integer()   # Head Rotation
                            body = buf.read_integer()   # Body Rotation
                            action = buf.read_string()  # Action (sit, lay, etc.)

                            # Update local cache
                            if index in self.users_in_room:
                                self.users_in_room[index].x = x
                                self.users_in_room[index].y = y
                    except Exception as e:
                        print(f"[ERROR] Parsing Movement: {e}")
                    continue
                
                # --- 2. CHAT HANDLING ---
                # Packet 3423 is standard room chat.
                if packet_id == 3423:
                    try:
                        buf = Buffer(payload)
                        user_index = buf.read_integer() 
                        message = buf.read_string()
                        
                        if user_index in self.users_in_room:
                            name = self.users_in_room[user_index].name
                            # Update real-time vars for external logic reading
                            self.last_chat_user_name = name
                            self.last_chat_message = message
                            self.last_chat_time = time.time()
                    except Exception as e:
                        print(f"[ERROR] Parsing Chat: {e}")
                    continue

                # --- 3. STANDARD HANDLERS ---
                if packet_id == 4000:
                    self._handle_disconnect_reason(payload)
                    continue
                
                if packet_id == 1510:
                    self.log("BAN DETECTED via Packet 1510")
                    self.is_banned = True
                    raise BanDetectedException("Packet 1510")

                if packet_id == const.Incoming.PING:
                    self.send_packet(compose_pong())

                elif packet_id == const.Incoming.FLOOD_CONTROL:
                    # Updates the UI with mute timer
                    seconds = parse_flood_control(payload)
                    self.log(f"Flood control: {seconds}s")
                
                elif packet_id == const.Incoming.USERS:
                    # New users entered room (or we entered). Parse and check for Admins.
                    try:
                        for user in parse_users(payload):
                            self.users_in_room[user.room_index] = user
                            # Admin Safety: Auto-leave if staff enters
                            if self.admin_auto_leave_enabled and any(admin.lower() == user.name.lower() for admin in const.ADMINS):
                                if not self._left_due_to_admin:
                                    threading.Thread(target=self.quit_room, daemon=True).start()
                                    self._left_due_to_admin = True
                    except: pass
                
                elif packet_id == const.Incoming.USER_OBJECT:
                    # Received our own user data. Check if NUX is needed.
                    try:
                        user_obj = parse_user_object(payload)
                        self.username = user_obj.name
                        # If name starts with "habb" (default names), trigger new user flow
                        if "habb" in self.username.lower() and not self._nux_running:
                            threading.Thread(target=self._run_nux_flow, daemon=True).start()
                    except: pass

                elif packet_id == const.Incoming.FLAT_CREATED:
                    # Room creation result
                    try: self.send_packet(compose_update_home_room(parse_flat_created(payload)))
                    except: pass

                elif packet_id == const.Incoming.NAVIGATOR_SEARCH_RESULT_BLOCKS:
                    # Navigator results
                    try:
                        rooms = parse_navigator_search_result(payload)
                        self.navigator_callback(rooms)
                    except: pass

                elif packet_id == const.Incoming.FLOOR_HEIGHT_MAP:
                    # Room geometry loaded
                    self._in_room_event.set()
                    parse_floor_height_map(payload, self.room_map)
                    # Process queued height map if it arrived out of order
                    if self.pending_height_map_payload:
                        parse_height_map(self.pending_height_map_payload, self.room_map)
                        self.pending_height_map_payload = None

                elif packet_id == const.Incoming.HEIGHT_MAP:
                    # Object height map
                    if self.room_map.width > 0:
                        parse_height_map(payload, self.room_map)
                    else:
                        self.pending_height_map_payload = payload

                elif packet_id == const.Incoming.USER_REMOVE:
                    # User left room
                    try:
                        room_index = int(parse_user_remove(payload))
                        self.users_in_room.pop(room_index, None)
                    except: pass

        except BanDetectedException:
            self.is_banned = True
        except (ConnectionError, socket.timeout, socket.error):
            self.log("Socket Disconnected/Timeout")
        except Exception: pass
        finally:
            self.connected = False
            self.disconnect()
            
            if self.is_banned: self.status_updater("Banned")
            else: self.status_updater("Disconnected")

    # -------------------------------------------------------------------------
    # SOCKET UTILITIES & CRYPTO
    # -------------------------------------------------------------------------

    def disconnect(self):
        """Cleanly closes sockets and resets state."""
        was_connected = self.connected
        self.connected = False
        
        if self.sock:
            try: self.sock.shutdown(socket.SHUT_RDWR)
            except: pass
            try: self.sock.close()
            except: pass
            self.sock = None
        
        if was_connected and threading.current_thread() != self.listener_thread:
            if self.is_banned: self.status_updater("Banned")
            else: self.status_updater("Disconnected")

    def _recv_all(self, n: int) -> bytes:
        """Reads exactly n bytes from the socket."""
        data = bytearray()
        while len(data) < n:
            if not self.sock: raise ConnectionError("Socket closed")
            try:
                packet = self.sock.recv(n - len(data))
                if not packet: raise ConnectionError("Socket closed (empty bytes)")
                data.extend(packet)
            except OSError:
                raise ConnectionError("Socket closed (OS Error)")
        return bytes(data)

    def send_packet(self, packet: HabboPacket):
        """Thread-safe method to encrypt and send a HabboPacket."""
        if not self.connected or not self.sock: return
        try:
            with self.send_lock:
                raw_data = bytearray(packet.get_bytes())
                if self.outgoing_cipher:
                    encrypted_data = self.outgoing_cipher.encrypt(raw_data)
                    self.sock.sendall(encrypted_data)
                else:
                    self.sock.sendall(raw_data)
        except Exception: 
            self.connected = False
            self.disconnect()

    def _send_plaintext_packet(self, packet: HabboPacket):
        """Sends a packet without encryption (used during Handshake)."""
        data = packet.get_bytes()
        try: self.sock.sendall(data)
        except Exception: 
            self.connected = False
            self.disconnect()

    def _receive_packet(self) -> (int, bytes): 
        """
        Reads one full packet.
        1. Reads Header (Length).
        2. Reads Body.
        3. Decrypts (if RC4 is active).
        Returns (PacketID, PayloadBytes).
        """
        if self.incoming_cipher:
            header_enc = self._recv_all(4)
            header_dec = self.incoming_cipher.decrypt(bytearray(header_enc))
            length = struct.unpack('>I', header_dec)[0]
            
            body_enc = self._recv_all(length)
            body_dec = self.incoming_cipher.decrypt(bytearray(body_enc))
            
            packet_id = struct.unpack('>H', body_dec[:2])[0]
            payload = body_dec[2:]
            return packet_id, payload
        else: 
            header = self._recv_all(4)
            length = struct.unpack('>I', header)[0]
            data = self._recv_all(length)
            packet_id = struct.unpack('>H', data[:2])[0]
            payload = data[2:]
            return packet_id, payload

    def _format_mute_time(self, seconds: int) -> str:
        """Helper to format mute duration into H:M:S string."""
        try:
            s = int(seconds); m, s = divmod(s, 60); h, m = divmod(m, 60)
            if h > 0: return f"Muted ({h}h {m}m)"
            elif m > 0: return f"Muted ({m}m {s}s)"
            else: return f"Muted ({s}s)"
        except: return f"Muted: {seconds}s"

    def _generate_meme_nick(self):
        """
        Generates a nickname like: Ted69Putin or Diddy420Chad.
        Combines two names from MEME_NAMES with a random number.
        """
        part1 = random.choice(self.MEME_NAMES)
        part2 = random.choice(self.MEME_NAMES)
        
        # Random separator (2 or 3 digits to ensure uniqueness)
        number = random.randint(10, 999)
        
        # Construct the nickname
        final_nick = f"{part1}{number}{part2}"
        
        # Habbo Hard Limit is usually 15 characters. 
        if len(final_nick) > 15:
            # Try a shorter number format
            final_nick = f"{part1}{random.randint(1,9)}{part2}"
            if len(final_nick) > 15:
                final_nick = final_nick[:15]
                
        return final_nick

    def _run_nux_flow(self):
        """
        Automates the 'New User Experience'.
        1. Changes Figure/Gender.
        2. Changes Name to a generated meme name.
        3. Enters a starter room.
        """
        self._nux_running = True
        self.log("Starting NUX (New User) Flow...")
        time.sleep(2.0)
        
        # 1. Set Random Look
        gender = random.choice(['M', 'F'])
        figure = random.choice(const.RANDOM_FIGURES_MALE) if gender == 'M' else random.choice(const.RANDOM_FIGURES_FEMALE)
        self.send_packet(compose_update_figure(gender, figure))
        time.sleep(1.5)
        
        # 2. Generate Meme Nickname
        new_nickname = self._generate_meme_nick()
        self.log(f"Attempting to change nick to: {new_nickname}")
        self.send_packet(compose_change_username(new_nickname))
        
        # 3. Enter Room
        time.sleep(1.5)
        self.send_packet(compose_select_initial_room("12"))

    def _start_latency_pinger(self):
        """Background thread that sends a Latency Ping Request every 20s to keep connection alive."""
        while self.connected:
            try:
                time.sleep(20) 
                if not self.connected: break
                ping_packet = compose_latency_ping_request(self.latency_ping_request_id)
                self.send_packet(ping_packet)
                self.latency_ping_request_id += 1
            except: self.connected = False; self.disconnect(); break

    def _send_login_details(self):
        """Sends the 3-packet login sequence: Version, UniqueID, SSO Ticket."""
        v = HabboPacket(const.Outgoing.VERSION_CHECK); v.write_integer(401); v.write_string("app:/"); v.write_string(const.EXTERNAL_VARIABLES_URL)
        self.send_packet(v)
        u = HabboPacket(const.Outgoing.UNIQUE_ID); u.write_string(const.generate_md5_fingerprint()); u.write_string(const.STATIC_PLATFORM_STRING)
        self.send_packet(u)
        sso = HabboPacket(const.Outgoing.SSO_TICKET); sso.write_string(self.sso_ticket); sso.write_integer(int(time.time()*1000)-self.start_time_ms)
        self.send_packet(sso)

    def _rsa_pad_and_encrypt(self, message_bytes: bytes) -> str:
        """Custom RSA padding (PKCS#1 v1.5 style) and encryption for the Handshake."""
        ps_len = self.rsa_key_size - len(message_bytes) - 3
        if ps_len < 8: raise ValueError("Msg too long")
        padding_string = b''; 
        while len(padding_string) < ps_len:
            rand_byte = secrets.token_bytes(1)
            if rand_byte != b'\x00': padding_string += rand_byte
        padded_message = b'\x00\x02' + padding_string + b'\x00' + message_bytes
        padded_message_int = int.from_bytes(padded_message, 'big')
        encrypted_int = pow(padded_message_int, self.rsa_key.e, self.rsa_key.n)
        return encrypted_int.to_bytes(self.rsa_key_size, 'big').hex()

    def _rsa_verify_and_unpad(self, encrypted_hex: str) -> int:
        """Decrypts and unpads RSA messages received during Handshake."""
        encrypted_int = int(encrypted_hex, 16)
        decrypted_int = pow(encrypted_int, self.rsa_key.e, self.rsa_key.n)
        padded_block = decrypted_int.to_bytes(self.rsa_key_size, 'big')
        try:
            separator_idx = padded_block.index(b'\x00', 2)
            message_bytes = padded_block[separator_idx + 1:]
            return int(message_bytes.decode('ascii'))
        except: raise ValueError("RSA Error")

    # -------------------------------------------------------------------------
    # GAMEPLAY API METHODS (Public)
    # -------------------------------------------------------------------------

    def join_room(self, room_id: int):
        """Resets room state and sends packets to enter a guest room."""
        self._in_room_event.clear()
        self.users_in_room.clear()
        self.room_map = RoomMap()
        self.pending_height_map_payload = None
        self.stop_random_walk()
        self._left_due_to_admin = False
        
        self.send_packet(compose_get_guest_room(room_id, 0, 1))
        self.send_packet(compose_avatar_effect_selected(-1)) # Remove effects
        self.send_packet(compose_get_interstitial())
        self.send_packet(compose_get_guest_room(room_id, 1, 0))

    def search_navigator(self, c, v=""): 
        """Searches the room navigator."""
        self.send_packet(compose_new_navigator_search(c, v))

    def shout(self, message: str, style: int = -1):
        """
        Shouts a message in the room.
        Auto-appends random characters to message to avoid spam filters/detection.
        """
        if style == -1:
            chosen_style = random.randint(0, 30)
        else:
            chosen_style = style

        if message.startswith(":") or message.startswith("/"):
            # Command processing
            final_msg = message
        else:
            # Generate 4 random uppercase letters (e.g., 'FASK') for anti-spam
            random_suffix = ''.join(random.choices(string.ascii_uppercase, k=4))
            random_prefix = ''.join(random.choices(string.ascii_uppercase, k=4))
            final_msg = f"{random_prefix} {message} {random_suffix}"
        
        self.send_packet(compose_shout(final_msg, chosen_style))

    def whisper(self, u, m, s=0): 
        """Sends a whisper to a user."""
        self.send_packet(compose_whisper(f"{u} {m}", s))

    def walk(self, x, y): 
        """Moves avatar to X, Y coordinates."""
        self.stop_random_walk()
        self.send_packet(compose_move_avatar(x, y))
    
    def walk_random(self, delay=1.0):
        """Starts a background thread that walks to random tiles."""
        if self._is_walking_randomly: return
        self.stop_random_walk()
        self._is_walking_randomly = True 
        self._random_walk_thread = threading.Thread(target=self._rand_walk, args=(delay,), daemon=True)
        self._random_walk_thread.start()
    
    def stop_random_walk(self): 
        """Stops the random walk thread."""
        self._is_walking_randomly = False

    def set_walk_room_aware(self, b): 
        """If True, random walk only picks valid walkable tiles from RoomMap."""
        self._walk_room_aware = bool(b)
    
    def _rand_walk(self, d):
        """Thread function for random walking."""
        while self._is_walking_randomly:
            try:
                if not self._walk_room_aware: 
                    # Blind random coordinate
                    self.send_packet(compose_move_avatar(random.randint(0,49), random.randint(0,49)))
                else:
                    # Smart walk using map data
                    if self.room_map and self.room_map.is_valid():
                        t = self.room_map.get_walkable_tiles()
                        if t: self.send_packet(compose_move_avatar(*random.choice(t)))
                time.sleep(d)
            except: time.sleep(d)

    def quit_room(self):
        """Exits current room by joining the default lobby (ID 80257391)."""
        self.join_room(80257391)

    def change_motto(self, m): self.send_packet(change_motto(m))
    def update_figure(self, g, f): self.send_packet(compose_update_figure(g, f))
    def request_friend(self, u): self.send_packet(compose_request_friend(u))
    def change_username(self, n): self.send_packet(compose_change_username(n))
    def dance(self, i): self.send_packet(compose_dance(i))
    def sign(self, i): self.send_packet(compose_sign(i))
    def change_posture(self, i): self.send_packet(compose_change_posture(i))
    def respect_user(self, i): self.send_packet(compose_respect_user(i))
    def replenish_respect(self): self.send_packet(compose_replenish_respect())
    def set_admin_auto_leave(self, b): self.admin_auto_leave_enabled = bool(b)
    
    def copy_user_looks(self, target: str):
        """
        Finds a user by Name or WebID in the current room and copies 
        their Figure, Gender, and Motto.
        """
        target = str(target).lower().strip()
        found_user = None

        # Search in local room cache
        for u in self.users_in_room.values():
            if u.name.lower() == target or str(u.web_id) == target:
                found_user = u
                break
        
        if found_user:
            self.send_packet(compose_update_figure(found_user.gender, found_user.figure))
            self.send_packet(change_motto(found_user.motto))

    def claim_rewards(self, reward_type=2):
        """
        Claims progression/daily rewards.
        Flow: Status Request -> Human Delay -> Claim Request.
        """
        self.log("Getting reward for with id " + str(reward_type))
        # 1. Open the window (Server check)
        self.send_packet(compose_income_reward_status())
        
        # 2. Critical Delay (Wait for window to 'load' server-side)
        time.sleep(1.0)
        
        # 3. Claim the reward
        self.send_packet(compose_income_reward_claim(reward_type))
            
    def purchase_item(self, page_id, item_id, extra_data="", amount=1):
        """Sends packet 3853 to buy an item from the catalog."""
        self.log("Getting item for")
        self.send_packet(compose_purchase_from_catalog(page_id, item_id, extra_data, amount))

    def enable_effect(self, effect_id: int):
        """
        Activates and then selects an Avatar Effect.
        Uses a delay to ensure server processes the activation first.
        """
        self.log("enabling effect")
        # 1. Tell server to Activate/Enable the effect (e.g. from inventory)
        self.send_packet(compose_avatar_effect_activated(effect_id))
        
        # ⚠️ CRITICAL DELAY: Server needs time to register the activation
        time.sleep(0.5) 
        
        # 2. Tell server to visually wear it

        self.send_packet(compose_avatar_effect_selected(effect_id))
