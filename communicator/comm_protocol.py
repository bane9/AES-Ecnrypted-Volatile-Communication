"""_summary_
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
    """_summary_
    """

    def __init__(self, aes: AES, data_to_transmit: bytes,
                 aes_fields_on_init: list[str] = None, aes_fields_on_tx: list[str] = None):
        """_summary_

        Args:
            aes (AES): _description_
            data_to_transmit (bytes): _description_
            aes_fields_on_init (list[str], optional): _description_. Defaults to None.
            aes_fields_on_tx (list[str], optional): _description_. Defaults to None.
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
        """_summary_
        """

        self.aes.reset()
        self.data_idx = 0

        self.encrypted_data = self.data_to_transmit
        self.encrypted_data += b"0" * (self.data_size_padded - len(self.encrypted_data))

        self.encrypted_data = self.aes.update(self.encrypted_data) + self.aes.finalize()

        assert len(self.encrypted_data) == self.data_size_padded

    def gen_init_message(self) -> dict[str, int or str or bytes]:
        """_summary_

        Returns:
            dict[str, int or str or bytes]: _description_
        """

        self.reset()

        msg = {"message_size": len(self.data_to_transmit),
               "chunks": len(self.data_to_transmit) // AES.AES_BYTE_LENGTH}

        for field in self.fields_on_init:
            msg[field] = getattr(self.aes, field)

        return msg

    def gen_tx_message(self) -> dict[str, bytes] or None:
        """_summary_

        Returns:
            dict[str, bytes]: _description_
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
        """_summary_

        Args:
            chunk (int): _description_
        """

        self.data_idx = chunk * AES.AES_BYTE_LENGTH


class Receiver:
    """_summary_
    """

    class RxFailureException(Exception):
        """_summary_
        """

        @unique
        class ErrorProtocol(Enum):
            """_summary_
            """

            REINIT = 0
            RETRANSMIT = 1

        def __init__(self, error_protocol: ErrorProtocol,
                     chunk: int, message=""):
            """_summary_

            Args:
                error_protocol (ErrorProtocol): _description_
                chunk (int): _description_
                message (str, optional): _description_. Defaults to "".
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
                 aes_fields_on_rx: list[str] = None):
        """_summary_

        Args:
            aes (AES): _description_
            data_received_cb (Callable[[bytes, bytes, int]]): _description_
            error_protocol (RxFailureException.ErrorProtocol, optional): _description_. Defaults to None.
            aes_fields_on_init (list[str], optional): _description_. Defaults to None.
            aes_fields_on_rx (list[str], optional): _description_. Defaults to None.
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

        if self.fields_on_init is None:
            self.fields_on_init = []

        if self.fields_on_rx is None:
            self.fields_on_rx = []

    def reset(self):
        """_summary_
        """

        self.aes.reset()
        self.received_data = bytes()
        self.received_data_encrypted = bytes()
        self.data_size_to_receive = 0
        self.chunks_to_receive = 0
        self.current_chunk = 0

    def on_init_msg(self, init_msg: dict[str, int or str or bytes]):
        """_summary_

        Args:
            init_msg (dict[str, int or str or bytes]): _description_
        """

        self.data_size_to_receive = init_msg["message_size"]
        self.chunks_to_receive = init_msg["chunks"]

        for field in self.fields_on_init:
            setattr(self.aes, field, init_msg[field])

        self.aes.reset()

    def on_data_rx(self, rx_data: dict[str, int or bytes]):
        """_summary_

        Args:
            rx_data (dict[str, int or bytes]): _description_

        Raises:
            Receiver.RxFailureException: _description_
            Receiver.RxFailureException: _description_
        """

        if self.current_chunk + 1 != rx_data["chunk"]:
            raise Receiver.RxFailureException(self.error_protocol, self.current_chunk + 1, "Missing chunk")

        for field in self.fields_on_rx:
            setattr(self.aes, field, rx_data[field])

        data = self.aes.update(rx_data["data"])

        if not data:
            raise Receiver.RxFailureException(self.error_protocol, rx_data["chunk"], "Decryption failure")

        if len(self.received_data) + len(rx_data["data"]) >= self.data_size_to_receive:
            data += self.aes.finalize()

        self.received_data += data
        self.received_data_encrypted += rx_data["data"]
        self.current_chunk += 1

        # Remove final padding, if any
        if len(self.received_data) > self.data_size_to_receive:
            self.received_data = self.received_data[:self.data_size_to_receive]

        if self.data_received_cb is not None:
            bytes_remaining = self.data_size_to_receive - len(self.received_data)

            self.data_received_cb(self.received_data, data, bytes_remaining)

class TxRxPair:
    """_summary_
    """

    def __init__(self, transmitter: Transmitter, receiver: Receiver):
        """_summary_

        Args:
            transmitter (Transmitter): _description_
            receiver (Receiver): _description_
        """

        self.transmitter = transmitter
        self.receiver = receiver


def init_aes_txrx_pairs(data_to_transmit: bytes,
                        data_rx_cb: Callable[[bytes, bytes, int], None] = None) -> dict[str, TxRxPair]:
    """_summary_

    Args:
        data_to_transmit (bytes): _description_
        data_rx_cb (Callable[[bytes, bytes, int], None], optional): _description_. Defaults to None.

    Returns:
        dict[str, TxRxPair]: _description_
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
            error_protocol=Receiver.RxFailureException.ErrorProtocol.RETRANSMIT
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
            error_protocol=Receiver.RxFailureException.ErrorProtocol.REINIT,
            aes_fields_on_init=["iv"]
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
            aes_fields_on_init=["iv"]
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
            aes_fields_on_init=["nonce"]
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
            aes_fields_on_init=["iv"]
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
            error_protocol=Receiver.RxFailureException.ErrorProtocol.RETRANSMIT,
            aes_fields_on_init=["iv", "nonce"],
            aes_fields_on_rx=["tag"]
        )
    )

    return out
