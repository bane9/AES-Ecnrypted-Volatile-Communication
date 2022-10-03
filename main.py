"""AES Encrypted Volatile Communication main file.
"""

from communicator import Communicator

def main():
    """AES Encrypted Volatile Communication entry point.
    """

    message_message_fail_rate_percent = 0.03

    aes_modes_to_test = []

    comm = Communicator(message_fail_rate_percent=message_message_fail_rate_percent,
                        aes_modes_to_test=aes_modes_to_test)

    comm.test_aes_modes()


if __name__ == "__main__":
    main()
