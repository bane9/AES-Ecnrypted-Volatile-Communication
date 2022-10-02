"""Generic AES interface module.
"""

import os
from abc import ABC, abstractmethod
from enum import Enum, unique
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, CipherContext


class AES(ABC):
    """Generic AES interface.
    """

    AES_BIT_LENGTH: int
    AES_BYTE_LENGTH: int
    CIPHER_ALGORITHM: algorithms.AES128 or algorithms.AES256

    AES_IV_BYTE_LENGTH = 16
    AES_NONCE_BYTE_LENGTH = 16

    @unique
    class AES_MODE(Enum):
        """Used to set the AES class into either Encryptor or Decryptor mode.
        """
        ENCRYPTOR = 0
        DECRYPTOR = 1

    def __init__(self, key: bytes = None, iv: bytes = None, nonce: bytes = None, mode = AES_MODE.ENCRYPTOR):
        """AES generic interface initialization.

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
        if key is None:
            key = self.generate_secure_key()
        else:
            assert len(key) == self.AES_BYTE_LENGTH

        if iv is None:
            iv = self.generate_secure_iv()
        else:
            assert len(iv) == self.AES_BYTE_LENGTH

        if nonce is None:
            nonce = self.generate_secure_nonce()
        else:
            assert len(nonce) == self.AES_BYTE_LENGTH

        self.key = key
        self.iv = iv
        self.nonce = nonce

        self.data: bytes = None

        self.cipher: Cipher = None
        self.context: CipherContext = None

        self.mode = mode

        self.set_mode(mode)


    @abstractmethod
    def set_mode(self, mode: AES_MODE):
        """Set the AES mode to either Encryptor or Decryptor.

        Args:
            mode (AES_MODE): AES mode.
        """

    def _set_mode(self, mode: AES_MODE):
        """Generic function for initializing an AES context.
        Note that this function resets the previous state of the class (if present).

        Args:
            mode (AES_MODE): AES mode.
        """

        if mode == AES.AES_MODE.ENCRYPTOR:
            self.context = self.cipher.encryptor()
        elif mode == AES.AES_MODE.DECRYPTOR:
            self.context = self.cipher.decryptor()

        self.data = bytes()

        self.mode = mode

    def update(self, data: bytes) -> bytes:
        """AES context update.

        Args:
            data (bytes): data to encrypt or decrypt.

        Returns:
            bytes: processed data.
        """

        return self.context.update(data)

    def finalize(self) -> bytes:
        """AES context finalization.

        Returns:
            bytes: finalized data.
        """

        return self.context.finalize()

    def reset(self):
        """Resets the current instance of the class.
        """

        self.set_mode(self.mode)

    @classmethod
    def generate_secure_key(cls) -> bytes:
        """Generate an AES key with byte length equal to AES.AES_BYTE_LENGTH.

        Returns:
            bytes: random bytes array.
        """

        return os.urandom(cls.AES_BYTE_LENGTH)

    @classmethod
    def generate_secure_iv(cls) -> bytes:
        """Generate an AES IV with byte length equal to AES.AES_IV_BYTE_LENGTH.

        Returns:
            bytes: random IV array.
        """

        return os.urandom(cls.AES_IV_BYTE_LENGTH)

    @classmethod
    def generate_secure_nonce(cls) -> bytes:
        """Generate an AES key with byte length equal to AES.AES_NONCE_BYTE_LENGTH.

        Returns:
            bytes: random nonce array.
        """

        return os.urandom(cls.AES_NONCE_BYTE_LENGTH)

    @classmethod
    def set_bit_length(cls, bit_length: int):
        """Set the global bit length of the AES class. Must be called before any instantiation
        of this class and it's derivatives.

        Args:
            bit_length (int): Desired bit length. Must be either 128 or 256.

        Raises:
            ValueError: Raised if the supplied bit length is neither 128 nor 256.
        """
        cls.AES_BYTE_LENGTH = bit_length // 8

        if bit_length == 128:
            cls.CIPHER_ALGORITHM = algorithms.AES128
        elif bit_length == 256:
            cls.CIPHER_ALGORITHM = algorithms.AES256
        else:
            raise ValueError(f"Invalid AES bit length configuration {bit_length}. "
                             "Supported bit lengths are 128 and 256.")

        cls.AES_BIT_LENGTH = bit_length

AES.set_bit_length(128)
