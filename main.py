"""AES Encrypted Volatile Communication main file.
"""

import argparse
from communicator import Communicator


def parse_args() -> argparse.Namespace:
    """_summary_

    Returns:
        argparse.ArgumentParser: _description_
    """

    arg = argparse.ArgumentParser()

    arg.add_argument("--fail_percent",
                    type=float,
                    help="Transmission failure percentage",
                    required=True)

    arg.add_argument("--image_path",
                    type=str,
                    help="Path to the image that will be transmitted",
                    required=False,
                    default="")

    arg.add_argument("--use_retransmission",
                    type=bool,
                    help="Use retransmission on packet failure. If set to false"
                    ", the missing packets will be padded with zero's",
                    required=False,
                    default=False)

    arg.add_argument("--aes_alg",
                    type=str,
                    help="AES algorithm to test",
                    action="append",
                    required=False)

    return arg.parse_args()

def main():
    """AES Encrypted Volatile Communication entry point.
    """

    args = parse_args()

    Communicator(message_fail_rate_percent=args.fail_percent,
                 aes_modes_to_test=args.aes_alg,
                 path_to_image=args.image_path,
                 use_retransmission=args.use_retransmission).test_aes_modes()

if __name__ == "__main__":
    main()
