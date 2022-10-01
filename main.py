"""AES Encrypted Volatile Communication main file.
"""

from communicator.comm_protocol import init_aes_txrx_pairs

def main():
    """AES Encrypted Volatile Communication entry point.
    """
    print(init_aes_txrx_pairs(b"0"))


if __name__ == "__main__":
    main()
