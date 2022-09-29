"""AES GCM Mode implementation.
"""

from cryptography.hazmat.primitives.ciphers import Cipher, modes
from .aes import AES


class AES_GCM(AES):
    """AES GCM class.
    """

    def __init__(self, key: bytes = None, iv: bytes = None,
                 nonce: bytes = None, mode = AES.AES_MODE.ENCRYPTOR,
                 tag: bytes = None):
        """AES GCM Mode initialization.

        Args:
            key (bytes, optional): AES key. It's length must be equal to AES.AES_BYTE_LENGTH
                                   or if None is supplied a new one will be automatically generated.
                                   Defaults to None.
            iv (bytes, optional): AES IV. It's length must be equal to AES.AES_IV_BYTE_LENGTH
                                  or if None is supplied a new one will be automatically generated.
                                  Defaults to None.
            nonce (bytes, optional): AES nonce. It's length must be equal to AES.AES_NONCE_BYTE_LENGTH
                                     or if None is supplied a new one will be automatically generated.
                                     Defaults to None.
            mode (AES.AES_MODE, optional): Sets the state of the AES instance. Defaults to AES_MODE.ENCRYPTOR.
        """

        super().__init__(key, iv, nonce, mode)
        self.tag: bytes = tag

    def set_mode(self, mode: AES.AES_MODE):
        """Set the AES mode to either Encryptor or Decryptor.

        Args:
            mode (AES_MODE): AES mode.
        """

        if mode == AES.AES_MODE.ENCRYPTOR:
            self.tag = None

        self.cipher = Cipher(self.CIPHER_ALGORITHM(self.key),
                             modes.GCM(self.iv, self.tag))

        super()._set_mode(mode)

    def finalize(self) -> bytes:
        """AES context finalization. If the class is in
        Encryptor mode, the final tag will be saved in the class instance.

        Returns:
            bytes: finalized data.
        """
        finalized = super().finalize()

        if self.mode == AES.AES_MODE.ENCRYPTOR:
            self.tag = self.context.tag

        return finalized

    def set_tag(self, tag: bytes):
        """Set the tag for the GCM instance.

        Args:
            tag (bytes): AES GCM tag.
        """

        self.tag = tag

    def get_tag(self) -> bytes or None:
        """Get the tag for the GCM instance.

        Returns:
            bytes or None: AES GCM tag.
        """

        return self.tag
