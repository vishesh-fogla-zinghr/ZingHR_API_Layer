import base64
from Crypto.Hash import MD5
from Crypto.Cipher import DES3
from Common.AES.Encrypt_Decrypt_Value import Encrypt_Decrypt_Value

class EncryptDecryptValue(Encrypt_Decrypt_Value):
    # Ensure this is the correct key

    def __init__(self):
        super().__init__()

    def encrypt_js_value(self, password: str) -> str:
        return self.encrypt(password)
    
    
    def pkcs7_pad(self, data: bytes, block_size: int = 8) -> bytes:
        pad_len = block_size - (len(data) % block_size)
        return data + bytes([pad_len] * pad_len)

    def encrypt(self, plain_text: str) -> str:
        
        CRYPTOKEY = "CHANGE THIS SHIT !"
        
        # Convert the plaintext to bytes
        des_pwd = plain_text.encode('utf-8')
        
        # Generate the key using MD5 hash of the CRYPTOKEY (encoded as ASCII)
        md5 = MD5.new(CRYPTOKEY.encode('ascii'))
        key = md5.digest()
        
        # Define the IV from the base64 string
        iv = base64.b64decode("6K3eYwavgo4=")
        
        # Create the DES3 cipher in CBC mode
        cipher = DES3.new(key, DES3.MODE_CBC, iv)
        
        # Pad the plaintext to a multiple of DES3 block size (8 bytes)
        padded_data = self.pkcs7_pad(des_pwd, DES3.block_size)
        
        # Encrypt the padded plaintext
        encrypted_bytes = cipher.encrypt(padded_data)
        
        # Return the ciphertext as a base64-encoded string
        return base64.b64encode(encrypted_bytes).decode('utf-8')