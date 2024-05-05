import base64
import json

from Crypto.Cipher import PKCS1_v1_5

from src.api.dmzj.Key import Key


class RSAUtil:
    def __init__(self):
        self._private_key = Key().pk

    def decrypt(self, content):
        """
        Directly input encrypted string and return decrypted string.
        """
        input_stream = base64.b64decode(content)
        output_stream = bytearray()
        cipher = PKCS1_v1_5.new(self._private_key)

        for i in range(0, len(input_stream), 128):
            block = input_stream[i:i + 128]
            output_stream += cipher.decrypt(block, sentinel = None)

        return json.loads(output_stream)
