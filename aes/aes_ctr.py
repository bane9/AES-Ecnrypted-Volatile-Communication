"""AES CTR Mode implementation.
"""

from cryptography.hazmat.primitives.ciphers import Cipher, modes
from .aes import AES


class AES_CTR(AES):
    """AES CTR class.
    """

    def __init__(self, key: bytes = None, nonce: bytes = None, mode = AES.AES_MODE.ENCRYPTOR):
        """AES CTR initialization.

        Args:
            key (bytes, optional): AES key. It's length must be equal to AES.AES_BYTE_LENGTH
                                   or if None is supplied a new one will be automatically generated.
                                   Defaults to None.
            nonce (bytes, optional): AES nonce. It's length must be equal to AES.AES_NONCE_BYTE_LENGTH
                                     or if None is supplied a new one will be automatically generated.
                                     Defaults to None.
            mode (AES.AES_MODE, optional): Sets the state of the AES instance. Defaults to AES_MODE.ENCRYPTOR.
        """

        super().__init__(key, None, nonce, mode)

    def set_mode(self, mode: AES.AES_MODE):
        """Set the AES mode to either Encrypor or Decryptor.

        Args:
            mode (AES_MODE): AES mode.
        """

        self.cipher = Cipher(self.CIPHER_ALGORITHM(self.key), modes.CTR(self.nonce))

        super()._set_mode(mode)
