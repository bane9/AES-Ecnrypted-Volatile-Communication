"""AES Encrypted Volatile Communication main file.
"""

import os
from communicator import Communicator

def main():
    """AES Encrypted Volatile Communication entry point.
    """

    data_to_transfer = os.urandom(1_000_00)
    message_message_fail_rate_percent = 0.05

    aes_modes_to_test = []

    comm = Communicator(data_to_transfer=data_to_transfer,
                        message_fail_rate_percent=message_message_fail_rate_percent,
                        aes_modes_to_test=aes_modes_to_test)

    comm.test_aes_modes()


if __name__ == "__main__":
    main()
