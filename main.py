"""AES Encrypted Volatile Communication main file.
"""

import argparse
from communicator import Communicator
from aes import AES


def parse_args() -> argparse.Namespace:
    """_summary_

    Returns:
        argparse.ArgumentParser: _description_
    """

    arg = argparse.ArgumentParser()

    arg.add_argument("--fail-percent",
                    type=float,
                    help="Transmission failure percentage",
                    required=True)

    arg.add_argument("--image-path",
                    type=str,
                    help="Path to the image that will be transmitted",
                    required=False,
                    default="")

    arg.add_argument("--use-retransmission",
                    type=bool,
                    help="Use retransmission on packet failure. If set to false"
                    ", the missing packets will be padded with zero's",
                    required=False,
                    default=False)

    arg.add_argument("--update-cipher-on-packet-drop",
                    type=bool,
                    help="Enable or disable the receiver updating it's"
                    " cipher with zero's when a dropped packet is detected",
                    required=False,
                    default=True)

    arg.add_argument("--aes-bit-length",
                    type=int,
                    help="AES bit length",
                    choices=[128, 256],
                    required=False,
                    default=256)

    arg.add_argument("--aes-alg",
                    type=str,
                    help="AES algorithm to test",
                    action="append",
                    required=False)

    return arg.parse_args()

def main():
    """AES Encrypted Volatile Communication entry point.
    """

    args = parse_args()

    AES.set_bit_length(args.aes_bit_length)

    Communicator(message_fail_rate_percent=args.fail_percent,
                 aes_modes_to_test=args.aes_alg,
                 path_to_image=args.image_path,
                 use_retransmission=args.use_retransmission,
                 update_cipher_on_packet_drop=args.update_cipher_on_packet_drop).test_aes_modes()

if __name__ == "__main__":
    main()
