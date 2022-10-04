"""AES communication configuration module
"""

from enum import Enum, unique
from typing import Callable

from aes import AES
from aes import AES_ECB
from aes import AES_CBC
from aes import AES_CFB
from aes import AES_CTR
from aes import AES_GCM
from aes import AES_OFB


class Transmitter:
    """AES communication transmitter class
    """

    def __init__(self, aes: AES, data_to_transmit: bytes,
                 aes_fields_on_init: list[str] = None, aes_fields_on_tx: list[str] = None):
        """
        Args:
            aes (AES): AES instance in encryptor mode that will be used.
            data_to_transmit (bytes): Data that will be transmitted.
            aes_fields_on_init (list[str], optional): Which fields
            from the AES instance will be used when creating a initialization
            message. Defaults to None.
            aes_fields_on_tx (list[str], optional): Which fields
            from the AES instance will be used when creating a tx message. Defaults to None.
        """

        self.aes = aes
        self.data_to_transmit = data_to_transmit
        self.data_idx = 0
        self.fields_on_init = aes_fields_on_init
        self.fields_on_tx = aes_fields_on_tx

        self.data_size_padded = ((len(data_to_transmit) // AES.AES_BYTE_LENGTH) + 1) * AES.AES_BYTE_LENGTH

        self.encrypted_data: bytes = None

        if self.fields_on_init is None:
            self.fields_on_init = []

        if self.fields_on_tx is None:
            self.fields_on_tx = []

    def reset(self):
        """Reset the transmitter instance
        """

        self.aes.reset()
        self.data_idx = 0

        self.encrypted_data = self.data_to_transmit
        self.encrypted_data += b"0" * (self.data_size_padded - len(self.encrypted_data))

        self.encrypted_data = self.aes.update(self.encrypted_data) + self.aes.finalize()

        assert len(self.encrypted_data) == self.data_size_padded

    def gen_init_message(self) -> dict[str, int or str or bytes]:
        """Generate an initialization message for the receiver

        Returns:
            dict[str, int or str or bytes]: Initialization message
        """

        self.reset()

        msg = {"message_size": len(self.data_to_transmit),
               "chunks": len(self.data_to_transmit) // AES.AES_BYTE_LENGTH}

        for field in self.fields_on_init:
            msg[field] = getattr(self.aes, field)

        return msg

    def gen_tx_message(self) -> dict[str, bytes] or None:
        """Generate an TX message for the receiver

        Returns:
            dict[str, bytes]: TX message
        """

        chunk_size = AES.AES_BYTE_LENGTH

        if self.data_idx > self.data_size_padded:
            raise IndexError("No more data to transmit")

        data = self.encrypted_data[self.data_idx : self.data_idx + chunk_size]

        self.data_idx += len(data)

        msg = {"data": data, "chunk": self.data_idx // chunk_size}

        for field in self.fields_on_tx:
            msg[field] = getattr(self.aes, field)

        return msg

    def set_chunk(self, chunk: int):
        """Set the chunk to be re-transmitted

        Args:
            chunk (int): Chunk to be set
        """

        self.data_idx = chunk * AES.AES_BYTE_LENGTH


class Receiver:
    """AES communication receiver class
    """

    class RxFailureException(Exception):
        """Exception thrown when the receiver detects communication
        discrepancies
        """

        @unique
        class ErrorProtocol(Enum):
            """Types of discrepancies the receiver class can detect
            """

            REINIT = 0
            RETRANSMIT = 1

        def __init__(self, error_protocol: ErrorProtocol,
                     chunk: int, message=""):
            """
            Args:
                error_protocol (ErrorProtocol): Type of detected discrepancy
                chunk (int): Chunk where the discrepancy was found
                message (str, optional): Any additional message
                to add to the error. Defaults to "".
            """

            self.error_protocol = error_protocol
            self.chunk = chunk
            self.message = f"RX failure on chunk {chunk}."

            if message:
                self.message += " Additional info: " + message

            super().__init__(self.message)

    def __init__(self,
                 aes: AES,
                 data_received_cb: Callable[[bytes, bytes, int], None],
                 error_protocol: RxFailureException.ErrorProtocol = None,
                 aes_fields_on_init: list[str] = None,
                 aes_fields_on_rx: list[str] = None,
                 update_cipher_on_packet_drop=True):
        """
        Args:
            aes (AES): AES instance in decryptor mode that will be used.
            data_received_cb (Callable[[bytes, bytes, int], None]): Callback instance
            that will receive the decrypted data.
            error_protocol (RxFailureException.ErrorProtocol, optional): What course
            of action will the receiver class perform in the case it detects a discrepancy.
            Defaults to None.
            aes_fields_on_init (list[str], optional): Which fields to set
            to the AES instance from fields available in the init message. Defaults to None.
            aes_fields_on_rx (list[str], optional): Which fields to set
            to the AES instance from fields available in the init message. Defaults to None.
            Defaults to None.
            update_cipher_on_packet_drop (bool, optional): If set to true and in the case of a
            detected discrepancy, the AES context will be provided with chunks of zero's
            to decrypt for as many chunks as are detected to be missing. Defaults to True.
        """

        self.aes = aes
        self.received_data = bytes()
        self.received_data_encrypted = bytes()
        self.data_received_cb = data_received_cb
        self.data_size_to_receive = 0
        self.chunks_to_receive = 0
        self.current_chunk = 0
        self.fields_on_init = aes_fields_on_init
        self.fields_on_rx = aes_fields_on_rx
        self.error_protocol = error_protocol

        self.update_cipher_on_packet_drop = update_cipher_on_packet_drop

        if self.fields_on_init is None:
            self.fields_on_init = []

        if self.fields_on_rx is None:
            self.fields_on_rx = []

    def reset(self):
        """Reset the receiver context
        """

        self.aes.reset()
        self.received_data = bytes()
        self.received_data_encrypted = bytes()
        self.data_size_to_receive = 0
        self.chunks_to_receive = 0
        self.current_chunk = 0

    def on_init_msg(self, init_msg: dict[str, int or str or bytes]):
        """Process the init message from the transmitter

        Args:
            init_msg (dict[str, int or str or bytes]): Init message
        """

        self.data_size_to_receive = init_msg["message_size"]
        self.chunks_to_receive = init_msg["chunks"]

        for field in self.fields_on_init:
            setattr(self.aes, field, init_msg[field])

        self.aes.reset()

    def _append_data(self, data: bytes, data_encrypted: bytes):
        """Append decrypted data (or zero padding)

        Args:
            data (bytes): Data chunk to be appended
            data_encrypted (bytes): Encrypted chunk to be appended
        """

        self.received_data += data
        self.received_data_encrypted += data_encrypted
        self.current_chunk += 1

        # Remove final padding, if any
        if len(self.received_data) > self.data_size_to_receive:
            self.received_data = self.received_data[:self.data_size_to_receive]

        if self.data_received_cb is not None:
            bytes_remaining = self.data_size_to_receive - len(self.received_data)

            self.data_received_cb(self.received_data, data, bytes_remaining)

    def _recover_by_padding(self, rx_data: dict[str, int or bytes], already_decrypted: bool):
        """Pad the buffers (and the cipher context if self.update_cipher_on_packet_drop == True)
        with chunks filled with zero's

        Args:
            rx_data (dict[str, int or bytes]): TX message
            already_decrypted (bool): Flag to know if the cipher context was already updated or not
        """
        chunks_missing = rx_data["chunk"] - self.current_chunk
        last_chunk = self.current_chunk + chunks_missing == self.data_size_to_receive // AES.AES_BYTE_LENGTH

        zerod_chunk = b"0" * AES.AES_BYTE_LENGTH

        if already_decrypted:
            self._append_data(zerod_chunk, zerod_chunk)
            return

        for i in range(chunks_missing):
            if i < chunks_missing - 1:
                if self.update_cipher_on_packet_drop:
                    self.aes.update(zerod_chunk)
                self._append_data(zerod_chunk, zerod_chunk)
            else:
                decrypted = self.aes.update(rx_data["data"])

                if last_chunk:
                    decrypted += self.aes.finalize()

                self._append_data(decrypted, rx_data["data"])

    def on_data_rx(self, rx_data: dict[str, int or bytes], pad_on_failure=False):
        """Process a TX message from the transmitter

        Args:
            rx_data (dict[str, int or bytes]): TX message
            pad_on_failure (bool, optional): Add zero padding in the case
            a discrepancy is detected. Defaults to False.

        Raises:
            Receiver.RxFailureException: In the case chunks are detected missing
            Receiver.RxFailureException: In the case the decrypted data is detected
            to be invalid
        """

        try:
            if self.current_chunk + 1 != rx_data["chunk"]:
                raise Receiver.RxFailureException(self.error_protocol, self.current_chunk + 1)

            for field in self.fields_on_rx:
                setattr(self.aes, field, rx_data[field])

            data = self.aes.update(rx_data["data"])

            if len(self.received_data) + len(rx_data["data"]) >= self.data_size_to_receive:
                data += self.aes.finalize()

            if not data:
                if pad_on_failure:
                    self._recover_by_padding(rx_data, True)
                else:
                    raise Receiver.RxFailureException(self.error_protocol, rx_data["chunk"])

            self._append_data(data, rx_data["data"])
        except Receiver.RxFailureException as e:
            if not pad_on_failure or e.error_protocol == Receiver.RxFailureException.ErrorProtocol.REINIT:
                raise

            self._recover_by_padding(rx_data, False)

            raise

class TxRxPair:
    """A pair of Transmitter and Receiver classes with the same
    AES class mode that share the same key
    """

    def __init__(self, transmitter: Transmitter, receiver: Receiver):
        """
        Args:
            transmitter (Transmitter): Transmitter instance
            receiver (Receiver): Receiver instance
        """

        self.transmitter = transmitter
        self.receiver = receiver


def init_aes_txrx_pairs(data_to_transmit: bytes,
                        data_rx_cb: Callable[[bytes, bytes, int], None] = None,
                        update_cipher_on_packet_drop: bool = True) -> dict[str, TxRxPair]:
    """Initialize TxRxPair instances with all implemented AES classes

    Args:
        data_to_transmit (bytes): data that will be transmitted between
        Transmitters and Receivers
        data_rx_cb (Callable[[bytes, bytes, int], None], optional): Callback
        that will be used for the Receiver. Defaults to None.
        update_cipher_on_packet_drop (bool, optional): If the receiver
        should update the cipher it's cipher context in the case it
        detects discrepancies. Defaults to True.

    Returns:
        dict[str, TxRxPair]: Dictionary will key being the name of the
        AES class and the value being the relevant TxRx instance
    """

    out = {}
    key = AES.generate_secure_key()

    out["ecb"] = TxRxPair(
        Transmitter(
            aes=AES_ECB(key=key, mode=AES.AES_MODE.ENCRYPTOR),
            data_to_transmit=data_to_transmit
        ),
        Receiver(
            aes=AES_ECB(key=key, mode=AES.AES_MODE.DECRYPTOR),
            data_received_cb=data_rx_cb,
            error_protocol=Receiver.RxFailureException.ErrorProtocol.RETRANSMIT,
            update_cipher_on_packet_drop=update_cipher_on_packet_drop
        )
    )

    out["cbc"] = TxRxPair(
        Transmitter(
            aes=AES_CBC(key=key, mode=AES.AES_MODE.ENCRYPTOR),
            data_to_transmit=data_to_transmit,
            aes_fields_on_init=["iv"]
        ),
        Receiver(
            aes=AES_CBC(key=key, mode=AES.AES_MODE.DECRYPTOR),
            data_received_cb=data_rx_cb,
            error_protocol=Receiver.RxFailureException.ErrorProtocol.RETRANSMIT,
            aes_fields_on_init=["iv"],
            update_cipher_on_packet_drop=update_cipher_on_packet_drop
        )
    )

    out["cfb"] = TxRxPair(
        Transmitter(
            aes=AES_CFB(key=key, mode=AES.AES_MODE.ENCRYPTOR),
            data_to_transmit=data_to_transmit,
            aes_fields_on_init=["iv"]
        ),
        Receiver(
            aes=AES_CFB(key=key, mode=AES.AES_MODE.DECRYPTOR),
            data_received_cb=data_rx_cb,
            error_protocol=Receiver.RxFailureException.ErrorProtocol.RETRANSMIT,
            aes_fields_on_init=["iv"],
            update_cipher_on_packet_drop=update_cipher_on_packet_drop
        )
    )

    out["ctr"] = TxRxPair(
        Transmitter(
            aes=AES_CTR(key=key, mode=AES.AES_MODE.ENCRYPTOR),
            data_to_transmit=data_to_transmit,
            aes_fields_on_init=["nonce"]
        ),
        Receiver(
            aes=AES_CTR(key=key, mode=AES.AES_MODE.DECRYPTOR),
            data_received_cb=data_rx_cb,
            error_protocol=Receiver.RxFailureException.ErrorProtocol.RETRANSMIT,
            aes_fields_on_init=["nonce"],
            update_cipher_on_packet_drop=update_cipher_on_packet_drop
        )
    )

    out["ofb"] = TxRxPair(
        Transmitter(
            aes=AES_OFB(key=key, mode=AES.AES_MODE.ENCRYPTOR),
            data_to_transmit=data_to_transmit,
            aes_fields_on_init=["iv"]
        ),
        Receiver(
            aes=AES_OFB(key=key, mode=AES.AES_MODE.DECRYPTOR),
            data_received_cb=data_rx_cb,
            error_protocol=Receiver.RxFailureException.ErrorProtocol.RETRANSMIT,
            aes_fields_on_init=["iv"],
            update_cipher_on_packet_drop=update_cipher_on_packet_drop
        )
    )

    out["gcm"] = TxRxPair(
        Transmitter(
            aes=AES_GCM(key=key, mode=AES.AES_MODE.ENCRYPTOR),
            data_to_transmit=data_to_transmit,
            aes_fields_on_init=["iv", "nonce"],
            aes_fields_on_tx=["tag"]
        ),
        Receiver(
            aes=AES_GCM(key=key, mode=AES.AES_MODE.DECRYPTOR),
            data_received_cb=data_rx_cb,
            error_protocol=Receiver.RxFailureException.ErrorProtocol.REINIT,
            aes_fields_on_init=["iv", "nonce"],
            aes_fields_on_rx=["tag"],
            update_cipher_on_packet_drop=update_cipher_on_packet_drop
        )
    )

    return out
