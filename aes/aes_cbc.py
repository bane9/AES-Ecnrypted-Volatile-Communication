"""AES CBC Mode implementation.
"""

from cryptography.hazmat.primitives.ciphers import Cipher, modes
from .aes import AES


class AES_CBC(AES):
    """AES CBC class.
    """

    def __init__(self, key: bytes = None, iv: bytes = None, mode = AES.AES_MODE.ENCRYPTOR):
        """AES CBC initialization.

        Args:
            key (bytes, optional): AES key. It's length must be equal to AES.AES_BYTE_LENGTH
                                   or if None is supplied a new one will be automatically generated.
                                   Defaults to None.
            iv (bytes, optional): AES IV. It's length must be equal to AES.AES_IV_BYTE_LENGTH
                                  or if None is supplied a new one will be automatically generated.
                                  Defaults to None.
            mode (AES.AES_MODE, optional): Sets the state of the AES instance. Defaults to AES_MODE.ENCRYPTOR.
        """

        super().__init__(key, iv, None, mode)

    def set_mode(self, mode: AES.AES_MODE):
        """Set the AES mode to either Encryptor or Decryptor.

        Args:
            mode (AES_MODE): AES mode.
        """

        self.cipher = Cipher(self.CIPHER_ALGORITHM(self.key), modes.CBC(self.iv))

        super()._set_mode(mode)
