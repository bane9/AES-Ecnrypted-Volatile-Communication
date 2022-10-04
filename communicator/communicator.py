"""AES Volatile Communicator module
"""

import random
from aes import AES
from summarizer import Summarizer, Visualizer
from image_helper import ImageHelper
from .comm_protocol import Receiver, TxRxPair, init_aes_txrx_pairs


class Communicator:
    """AES Volatile Communicator class
    """


    def __init__(self,
                 path_to_image = "",
                 aes_modes_to_test: list[str] = None,
                 message_fail_rate_percent = 1.0,
                 use_retransmission=False,
                 update_cipher_on_packet_drop=True):
        """
        Args:
            path_to_image (str, optional): Path to image that will be
            transmitted. If left empty, default one provided by the ImageHelper module
            will be used. Defaults to "".
            aes_modes_to_test (list[str], optional): List of aes modes to test.
            If left empty, all of them will be tested. Defaults to None.
            message_fail_rate_percent (float, optional): Message failure percentage
            that will be present during the communication. Defaults to 1.0.
            use_retransmission (bool, optional): Retransmit packets in case of their failure.
            Defaults to False.
            update_cipher_on_packet_drop (bool, optional): Update AES cipher contexts on failed packets.
            Defaults to True.
        """

        assert 0 <= message_fail_rate_percent <= 100

        self.message_fail_percent = int(message_fail_rate_percent * 1000)
        self.message_fail_count = 0
        if path_to_image:
            self.original_image = ImageHelper.load_image(path_to_image, True)
        else:
            self.original_image = ImageHelper.get_default_image()
        self.data_to_transfer = ImageHelper.image_to_bytes(self.original_image)
        self.tx_rx_pairs = \
            init_aes_txrx_pairs(self.data_to_transfer, self.on_data_rx, update_cipher_on_packet_drop)
        self.finished = False
        self.current_aes_mode_idx = 0

        self.use_retransmition = use_retransmission

        if not aes_modes_to_test:
            self.aes_modes_to_test = [*self.tx_rx_pairs.keys()]
        else:
            self.aes_modes_to_test = aes_modes_to_test

    def on_data_rx(self, all_received_data: bytes, _: bytes,
                   remaining_bytes_to_receive: int):
        """Callback tied to the Receiver class. It is used to process
        the received data.

        Args:
            all_received_data (bytes): All of the received decrypted data
            received_chunk (bytes): Current decrypted chunk
            remaining_bytes_to_receive (int): How many bytes receiver still has left
        """

        if len(all_received_data) % ((len(self.data_to_transfer) * 0.05)) == 0:
            percent_left = len(all_received_data) / (len(all_received_data) + remaining_bytes_to_receive)
            percent_left *= 100
            print(f"[{len(all_received_data)}/{len(all_received_data) + remaining_bytes_to_receive}]",
                  f"{percent_left:.1f}%")

        if remaining_bytes_to_receive == 0:
            receiver = self.tx_rx_pairs[self.aes_modes_to_test[self.current_aes_mode_idx]].receiver
            enc_image = receiver.received_data_encrypted

            img_path_enc = f"{self.aes_modes_to_test[self.current_aes_mode_idx]}/encrypted.png"
            img_path_dec = f"{self.aes_modes_to_test[self.current_aes_mode_idx]}/decrypted.png"

            ImageHelper.save_bytes_as_image(enc_image,
                                            img_path_enc,
                                            self.original_image.width,
                                            self.original_image.height,
                                            len(self.original_image.mode))

            ImageHelper.save_bytes_as_image(all_received_data,
                                            img_path_dec,
                                            self.original_image.width,
                                            self.original_image.height,
                                            len(self.original_image.mode))

            self.finished = True

    def test_aes_modes(self):
        """Test AES modes with settings provided in the constructor
        """

        i = 0
        while i < len(self.aes_modes_to_test):
            print("\n\nTesting AES mode:", self.aes_modes_to_test[i].upper(),
                  ", bit width:", AES.AES_BIT_LENGTH)

            self.current_aes_mode_idx = i

            Summarizer.start(self.aes_modes_to_test[i])
            self.message_fail_count = 0

            while True:
                self.finished = False
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

        Visualizer.generate_comparative_plot(f"AES bit length: {AES.AES_BIT_LENGTH} bits\n"
                                             f"Transmitted data size: {len(self.data_to_transfer)} bytes\n"
                                             f"Set fail rate: {self.message_fail_percent / 1000}%")

    def _test_aes_mode(self, txrx_pair: TxRxPair) -> bool:
        """Test a specific AES mode

        Args:
            txrx_pair (TxRxPair): TxRxPair with a specific AES instance

        Returns:
            bool: If False, then the same AES instance will be tested again.
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

                txrx_pair.receiver.on_data_rx(msg, not self.use_retransmition)
                Summarizer.on_packet_transmit()

            except Receiver.RxFailureException as e:
                self.message_fail_count += 1

                if e.error_protocol == Receiver.RxFailureException.ErrorProtocol.REINIT:
                    print("Data failure requiring re-initialization")
                    return False

                if self.use_retransmition:
                    print("Re-requesting chunk", e.chunk)

                    Summarizer.on_packet_retransmit()

                    txrx_pair.transmitter.set_chunk(e.chunk - 1)

                    msg = txrx_pair.transmitter.gen_tx_message()
                    txrx_pair.receiver.on_data_rx(msg)

        return True
