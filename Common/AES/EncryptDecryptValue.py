from base64 import b64encode, b64decode
from hashlib import md5
from Crypto.Cipher import DES3
from AES.Encrypt_Decrypt_Value import Encrypt_Decrypt_Value

class EncryptDecryptValue(Encrypt_Decrypt_Value):
    CRYPTOKEY = "Change this shit!!"  # Ensure this is the correct key

    def encrypt_js_value(self, password: str) -> str:
        return self.encrypt(password)

    def encrypt(self, plain_text: str) -> str:
        """
        Encrypts the given plaintext using Triple DES (3DES) with a fixed IV.
        """
        key = md5(self.CRYPTOKEY.encode('ascii')).digest()  # MD5 hash of key
        iv = b64decode("6K3eYwavgo4=")  # Decode the IV from Base64

        cipher = DES3.new(key[:24], DES3.MODE_CBC, iv)  # Ensure key is 24 bytes
        padded_text = self._pad(plain_text)  # Padding to match block size

        encrypted_bytes = cipher.encrypt(padded_text.encode('utf-8'))
        return b64encode(encrypted_bytes).decode('utf-8')

    def _pad(self, text: str) -> str:
        """Pads the text to be a multiple of 8 bytes (DES block size)."""
        pad_len = 8 - (len(text) % 8)
        return text + (chr(pad_len) * pad_len)