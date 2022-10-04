"""Unit tests for all of the AES Mode implementations.
"""

import os
from ..aes import AES
from ..aes_ecb import AES_ECB
from ..aes_cbc import AES_CBC
from ..aes_ctr import AES_CTR
from ..aes_gcm import AES_GCM
from ..aes_cfb import AES_CFB
from ..aes_ofb import AES_OFB
from ..aes_xts import AES_XTS

PLAIN_TEXT = os.urandom(AES.AES_BYTE_LENGTH * 12)

PLAIN_TEXT_DOUBLE = PLAIN_TEXT * 2

def aes_algorithms_test():
    """Group test for all of the AES classes.
    """
    assert len(PLAIN_TEXT) % AES.AES_BYTE_LENGTH == 0
    assert len(PLAIN_TEXT_DOUBLE) % AES.AES_BYTE_LENGTH == 0

    aes_algorithms: list[AES] = [AES_ECB, AES_CBC, AES_CTR, AES_CFB, AES_OFB, AES_GCM, AES_XTS]

    for algorithm in aes_algorithms:
        # Single pass
        print(f"Testing {algorithm.__name__} single pass")

        aes: AES = algorithm(mode=AES.AES_MODE.ENCRYPTOR)

        encrypted = aes.update(PLAIN_TEXT) + aes.finalize()

        aes.set_mode(AES.AES_MODE.DECRYPTOR)

        decrypted = aes.update(encrypted) + aes.finalize()
        assert decrypted == PLAIN_TEXT

        # Double pass
        print(f"Testing {algorithm.__name__} double pass")

        aes: AES = algorithm(mode=AES.AES_MODE.ENCRYPTOR)

        encrypted = aes.update(PLAIN_TEXT)
        encrypted += aes.update(PLAIN_TEXT)
        encrypted += aes.finalize()

        aes.set_mode(AES.AES_MODE.DECRYPTOR)

        decrypted = aes.update(encrypted) + aes.finalize()

        if algorithm != AES_XTS:
            assert decrypted == PLAIN_TEXT_DOUBLE

def test_aes_128():
    """Test all of the AES classes with a 128 bit length.
    """
    AES.set_bit_length(128)
    aes_algorithms_test()


def test_aes_256():
    """Test all of the AES classes with a 256 bit length.
    """
    AES.set_bit_length(256)
    aes_algorithms_test()
