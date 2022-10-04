"""AES XTS Mode implementation.
"""

import os
from cryptography.hazmat.primitives.ciphers import Cipher, modes, CipherContext
from .aes import AES


class AES_XTS(AES):
    """AES XTS class.
    """

    # pylint: disable=super-init-not-called
    def __init__(self, key: bytes = None, mode = AES.AES_MODE.ENCRYPTOR):
        """AES XTS Mode initialization.

        Args:
            key (bytes, optional): AES key. It's length must be equal to AES.AES_BYTE_LENGTH
                                   or if None is supplied a new one will be automatically generated.
                                   Defaults to None.
            mode (AES.AES_MODE, optional): Sets the state of the AES instance. Defaults to AES_MODE.ENCRYPTOR.
        """

        self.tweak = os.urandom(16)
        self.key = key

        if not self.key:
            self.key = self.generate_secure_key()

        if len(self.key) == AES.AES_BYTE_LENGTH:
            self.key += os.urandom(len(self.key))

        self.cipher: Cipher = None
        self.context: CipherContext = None

        self.mode = mode

        # Added for consistency sake with the AES base class

        self.iv = self.generate_secure_iv()
        self.nonce = self.generate_secure_nonce()

        self.set_mode(self.mode)

    def set_mode(self, mode: AES.AES_MODE):
        """Set the AES mode to either Encryptor or Decryptor.

        Args:
            mode (AES_MODE): AES mode.
        """

        self.cipher = Cipher(self.CIPHER_ALGORITHM(self.key),
                             modes.XTS(self.tweak))

        super()._set_mode(mode)
