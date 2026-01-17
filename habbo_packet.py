import struct

# -----------------------------------------------------------------------------
# HABBO PACKET (OUTGOING)
# -----------------------------------------------------------------------------
class HabboPacket:
    """
    Represents an OUTGOING packet destined for the Habbo server.
    
    The Habbo protocol uses Big-Endian (Network Byte Order) encoding.
    Structure:
    [4 bytes: Total Length] [2 bytes: Header/ID] [Body...]
    
    This class handles the construction of the Body and the Header, 
    and prepends the Length upon finalization in `get_bytes()`.
    """

    def __init__(self, packet_id, *args):
        """
        Initialize a packet with a specific Header ID.
        
        :param packet_id: The Short (2-byte) ID of the outgoing packet.
        :param args: Optional list of arguments to write immediately.
        """
        self._id = packet_id
        self._buffer = bytearray()
        
        # Write the Packet ID (Header) first
        self.write_short(packet_id)
        
        # Write any extra arguments passed during initialization
        for arg in args:
            self._write_arg(arg)

    def _write_arg(self, arg):
        """
        Helper to automatically detect type and write it.
        Useful for quick packet composition.
        """
        if isinstance(arg, str): self.write_string(arg)
        elif isinstance(arg, int): self.write_integer(arg)
        elif isinstance(arg, bool): self.write_boolean(arg)
        else: raise TypeError(f"Unsupported type for packet argument: {type(arg)}")

    def get_bytes(self):
        """
        Finalizes the packet for sending over the socket.
        
        Calculates the total length of the buffer (Header + Body) and 
        prepends it as a 4-byte Integer.
        
        Format: [Length (4 bytes)] + [Existing Buffer]
        """
        length = len(self._buffer)
        # Pack length as Big-Endian Unsigned Int (>I)
        return struct.pack('>I', length) + self._buffer

    def write_string(self, s: str):
        """
        Writes a string to the buffer.
        Format: [2 bytes: Length of string] [N bytes: UTF-8 Characters]
        """
        encoded = s.encode('utf-8')
        self.write_short(len(encoded))
        self._buffer.extend(encoded)

    def write_short(self, val: int):
        """
        Writes a 2-byte Short integer.
        Format code: >H (Big-Endian Unsigned Short)
        """
        self._buffer.extend(struct.pack('>H', val))

    def write_integer(self, val: int):
        """
        Writes a 4-byte Integer.
        Format code: >i (Big-Endian Signed Integer)
        """
        self._buffer.extend(struct.pack('>i', val))
        
    def write_boolean(self, val: bool):
        """
        Writes a 1-byte Boolean.
        Format code: >? (1 byte) -> 0x01 (True) or 0x00 (False)
        """
        self._buffer.extend(struct.pack('>?', val))

    def write_byte(self, val: int):
        """
        Writes a raw single byte (8-bit integer).
        Used for specific protocol structures (like {b:2}).
        Format code: >B (Unsigned Char / 1 byte)
        """
        self._buffer.extend(struct.pack('>B', val))


# -----------------------------------------------------------------------------
# BUFFER CLASS (INCOMING)
# -----------------------------------------------------------------------------
class Buffer:
    """
    Represents the content of an INCOMING packet.
    
    Used to parse raw bytes received from the socket into Python types.
    Maintains a cursor position (`self.pos`) to read sequentially.
    """
    
    def __init__(self, data: bytes):
        self.buffer = data
        self.pos = 0 # Current cursor position

    def read_short(self) -> int:
        """Reads 2 bytes as a Short (Big-Endian)."""
        if self.pos + 2 > len(self.buffer): return 0
        val = struct.unpack('>H', self.buffer[self.pos:self.pos+2])[0]
        self.pos += 2
        return val

    def read_integer(self) -> int:
        """Reads 4 bytes as an Integer (Big-Endian)."""
        if self.pos + 4 > len(self.buffer): return 0
        val = struct.unpack('>I', self.buffer[self.pos:self.pos+4])[0]
        self.pos += 4
        return val

    def read_string(self) -> str:
        """
        Reads a String.
        1. Reads 2 bytes to get the length (L).
        2. Reads L bytes.
        3. Decodes as UTF-8.
        """
        length = self.read_short()
        end_pos = self.pos + length
        
        # Safety check to prevent IndexOutOfBounds
        if end_pos > len(self.buffer):
            end_pos = len(self.buffer)
            
        raw = self.buffer[self.pos:end_pos]
        self.pos = end_pos
        
        try:
            return raw.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback for weird characters
            return raw.decode('utf-8', errors='replace')

    def read_boolean(self) -> bool:
        """Reads 1 byte as a Boolean."""
        if self.pos + 1 > len(self.buffer): return False
        val = struct.unpack('>?', self.buffer[self.pos:self.pos+1])[0]
        self.pos += 1
        return val

    def read_bytes(self, length: int) -> bytes:
        """Reads N raw bytes from the current position."""
        val = self.buffer[self.pos:self.pos+length]
        self.pos += length
        return val

    def get_remaining_bytes(self) -> bytes:
        """Returns all bytes from current cursor to the end."""
        return self.buffer[self.pos:]