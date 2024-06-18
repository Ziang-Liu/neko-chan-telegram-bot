import base64
from threading import Lock

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding


class Crypto:
    def __init__(self):
        self._key_raw = (b"MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBAK8nNR1lTnIfIes6oRWJNj3mB6OssDGx0uGMpgpbVCp"
                         b"f6+VwnuI2stmhZNoQcM417Iz7WqlPzbUmu9R4dEKmLGEEqOhOdVaeh9Xk2IPPjqIu5TbkLZRxkY3dJM1htbz57d/roe"
                         b"sJLkZXqssfG5EJauNc+RcABTfLb4IiFjSMlTsnAgMBAAECgYEAiz/pi2hKOJKlvcTL4jpHJGjn8+lL3wZX+LeAHkXDo"
                         b"TjHa47g0knYYQteCbv+YwMeAGupBWiLy5RyyhXFoGNKbbnvftMYK56hH+iqxjtDLnjSDKWnhcB7089sNKaEM9Ilil6u"
                         b"xWMrMMBH9v2PLdYsqMBHqPutKu/SigeGPeiB7VECQQDizVlNv67go99QAIv2n/ga4e0wLizVuaNBXE88AdOnaZ0LOTe"
                         b"niVEqvPtgUk63zbjl0P/pzQzyjitwe6HoCAIpAkEAxbOtnCm1uKEp5HsNaXEJTwE7WQf7PrLD4+BpGtNKkgja6f6F4l"
                         b"d4QZ2TQ6qvsCizSGJrjOpNdjVGJ7bgYMcczwJBALvJWPLmDi7ToFfGTB0EsNHZVKE66kZ/8Stx+ezueke4S556XplqO"
                         b"flQBjbnj2PigwBN/0afT+QZUOBOjWzoDJkCQClzo+oDQMvGVs9GEajS/32mJ3hiWQZrWvEzgzYRqSf3XVcEe7PaXSd8"
                         b"z3y3lACeeACsShqQoc8wGlaHXIJOHTcCQQCZw5127ZGs8ZDTSrogrH73Kw/HvX55wGAeirKYcv28eauveCG7iyFR0PF"
                         b"B/P/EDZnyb+ifvyEFlucPUI0+Y87F")
        self._private_key_bytes = base64.b64decode(self._key_raw)
        self._private_key = serialization.load_der_private_key(
            self._private_key_bytes,
            password = None,
            backend = default_backend()
        )

    def _get_key(self):
        lock = Lock()

        with lock:
            return self._private_key

    def decrypt(self, encrypted: bytes) -> bytes:
        result = bytearray()
        encrypted_data = base64.b64decode(encrypted)

        for i in range(0, len(encrypted_data), 128):
            chunk = encrypted_data[i:i + 128]
            dec = self._get_key().decrypt(
                chunk,
                padding.PKCS1v15()
            )
            result.extend(dec)

        return bytes(result)
