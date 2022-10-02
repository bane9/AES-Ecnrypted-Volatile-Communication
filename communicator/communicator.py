"""_summary_
"""

import random
from aes import AES
from summarizer import Summarizer
from .comm_protocol import Receiver, TxRxPair, init_aes_txrx_pairs


class Communicator:
    """_summary_
    """

    def __init__(self,
                 data_to_transfer: bytes,
                 aes_modes_to_test: list[str] = None,
                 message_fail_rate_percent = 1.0):
        """_summary_

        Args:
            data_to_transfer (bytes): _description_
            aes_modes_to_test (list[str], optional): _description_. Defaults to None.
            message_fail_rate_percent (float, optional): _description_. Defaults to 5.0.
        """

        assert 0 <= message_fail_rate_percent <= 100

        self.message_fail_percent = int(message_fail_rate_percent * 1000)
        self.message_fail_count = 0
        self.data_to_transfer = data_to_transfer
        self.tx_rx_pairs = init_aes_txrx_pairs(data_to_transfer, self.on_data_rx)
        self.finished = False

        if not aes_modes_to_test:
            self.aes_modes_to_test = [*self.tx_rx_pairs.keys()]
        else:
            self.aes_modes_to_test = aes_modes_to_test

    def on_data_rx(self, all_received_data: bytes, _: bytes,
                   remaining_bytes_to_receive: int):
        """_summary_

        Args:
            all_received_data (bytes): _description_
            received_chunk (bytes): _description_
            remaining_bytes_to_receive (int): _description_

        Raises:
            ValueError: _description_
        """

        if len(all_received_data) % ((len(self.data_to_transfer) * 0.05)) == 0:
            percent_left = len(all_received_data) / (len(all_received_data) + remaining_bytes_to_receive)
            percent_left *= 100
            print(f"[{len(all_received_data)}/{len(all_received_data) + remaining_bytes_to_receive}]",
                  f"{percent_left:.1f}%")

        if remaining_bytes_to_receive == 0:
            if all_received_data != self.data_to_transfer:
                raise ValueError("Received data does not match the provided data")
            self.finished = True

    def test_aes_modes(self):
        """_summary_
        """

        i = 0
        while i < len(self.aes_modes_to_test):
            print("\n\nTesting AES mode:", self.aes_modes_to_test[i].upper(),
                  ", bit width:", AES.AES_BIT_LENGTH)

            Summarizer.start(self.aes_modes_to_test[i])

            while True:
                self.finished = False
                self.message_fail_count = 0
                res = self._test_aes_mode(self.tx_rx_pairs[self.aes_modes_to_test[i]])

                message_fail_rate = \
                    self.message_fail_count / (len(self.data_to_transfer) // AES.AES_BYTE_LENGTH)

                message_fail_rate = round(message_fail_rate * 100, 4)

                print("Test",
                    "passed" if res else "failed",
                    f"({self.aes_modes_to_test[i].upper()})",
                    f"\nMessage fail rate: {message_fail_rate}%")

                if res:
                    Summarizer.end(message_fail_rate)
                    i += 1
                    break
                else:
                    Summarizer.on_connection_reset()
                    self.tx_rx_pairs[self.aes_modes_to_test[i]].transmitter.reset()
                    self.tx_rx_pairs[self.aes_modes_to_test[i]].receiver.reset()

    def _test_aes_mode(self, txrx_pair: TxRxPair) -> bool:
        """_summary_

        Args:
            txrx_pair (TxRxPair): _description_

        Returns:
            bool: _description_
        """

        init_msg = txrx_pair.transmitter.gen_init_message()
        txrx_pair.receiver.on_init_msg(init_msg)

        while not self.finished:
            try:
                msg = txrx_pair.transmitter.gen_tx_message()

                if random.randint(0, 100_000) < self.message_fail_percent:
                    print("Dropping chunk", msg["chunk"])
                    Summarizer.on_dropped_packet()
                    continue

                Summarizer.on_packet_transmit()
                txrx_pair.receiver.on_data_rx(msg)

            except Receiver.RxFailureException as e:
                self.message_fail_count += 1

                if e.error_protocol == Receiver.RxFailureException.ErrorProtocol.REINIT:
                    print("Data failure requiring re-initialization")
                    return False

                print("Re-requesting chunk", e.chunk)

                Summarizer.on_packet_retransmit()

                txrx_pair.transmitter.set_chunk(e.chunk - 1)

                msg = txrx_pair.transmitter.gen_tx_message()
                txrx_pair.receiver.on_data_rx(msg)

        return True
