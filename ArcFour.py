# Create or replace your ArcFour.py with this file.
# Let's call it HabboArcFour.py to avoid confusion.

class ArcFour:
    """
    Implements the asymmetric RC4-like stream cipher used by the Habbo client.
    - Encryption (outgoing) uses a standard RC4 keystream generation.
    - Decryption (incoming) uses a non-standard double S-box lookup.
    """
    def __init__(self, key: bytes):
        """Initializes the cipher state with the given key."""
        self._s = list(range(256))
        j = 0
        
        # Standard RC4 Key-Scheduling Algorithm (KSA)
        for i in range(256):
            j = (j + self._s[i] + key[i % len(key)]) % 256
            self._s[i], self._s[j] = self._s[j], self._s[i]
        
        self._i = 0
        self._j = 0

    def _apply_cipher(self, data: bytes, is_decrypt: bool) -> bytes:
        """
        Internal method to apply the cipher. Switches algorithm based on direction.
        """
        result = bytearray()
        for byte in data:
            # Advance the state (this is identical for both algorithms)
            self._i = (self._i + 1) % 256
            self._j = (self._j + self._s[self._i]) % 256
            self._s[self._i], self._s[self._j] = self._s[self._j], self._s[self._i]
            
            # --- KEY ALGORITHM DIFFERENCE ---
            index1 = (self._s[self._i] + self._s[self._j]) % 256
            
            if is_decrypt:
                # NON-STANDARD: Double S-box lookup for incoming data
                index2 = self._s[index1]
                keystream_byte = self._s[index2]
            else:
                # STANDARD: Single S-box lookup for outgoing data
                keystream_byte = self._s[index1]

            result.append(byte ^ keystream_byte)
            
        return bytes(result)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypts data using the STANDARD (single-lookup) RC4 algorithm."""
        return self._apply_cipher(data, is_decrypt=False)

    def decrypt(self, data: bytes) -> bytes:
        """Decrypts data using the NON-STANDARD (double-lookup) RC4 algorithm."""
        return self._apply_cipher(data, is_decrypt=True)