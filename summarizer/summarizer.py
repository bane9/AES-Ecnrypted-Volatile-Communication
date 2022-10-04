"""Event summarizer module for creating timeline graphs
"""

from enum import Enum, unique
import time
import datetime
import pickle
from .visualizer import Visualizer

class Summarizer:
    """Event summarizer class for creating timeline graphs
    """

    SAVE_FOLDER = "output/" + datetime.datetime.now().strftime("%H-%M-%S %d.%m.%Y")

    @unique
    class EventType(Enum):
        """Possible event types
        """

        BEGIN = 0
        END = 1
        PACKET_DROP = 2
        PACKET_RETRANSMIT = 3
        CONNECTION_RESET = 4
        PACKET_TRANSMIT = 5


    class Event:
        """A class containing all the info relevant to an event
        """

        def __init__(self, event_type: "Summarizer.EventType", timestamp: int = None, additional_data = ""):
            """
            Args:
                event_type (Summarizer.EventType): Type of the event
                timestamp (int, optional): Unix timestamp of when the event began. Defaults to None.
                additional_data (str, optional): Unix timestamp of when the event ended. Defaults to "".
            """

            self.timestamp = self.timestamp if timestamp is not None else Summarizer.get_current_time()
            self.end_timestamp = self.timestamp + 1
            self.event_type = event_type
            self.additional_data = additional_data

    current_aes_mode: str
    events: dict[str, list[Event]] = {}
    started_at: float

    BUSY_WAIT_AMOUNT_MS = 1.0

    @classmethod
    def start(cls, aes_mode: str):
        """Start the summarizer context

        Args:
            aes_mode (str): Name of the AES mode currently being tested
        """

        cls.current_aes_mode = aes_mode
        cls.events[cls.current_aes_mode] = []
        cls.started_at = time.perf_counter()


    @classmethod
    def _new_evt(cls, event_type: "Summarizer.EventType"):
        """Add an event to the event list

        Args:
            event_type (Summarizer.EventType): Type of the event
        """

        evt_list = cls.events[cls.current_aes_mode]

        if evt_list:
            last_evt = evt_list[-1]

            last_evt.end_timestamp = cls.get_current_time()

            if last_evt.event_type != event_type:
                evt_list.append(cls.Event(event_type))
        else:
            evt_list.append(cls.Event(event_type))

    @classmethod
    def _busy_wait(cls):
        """Used for adding a small delay after certain events happen.
        It fixes some events not lasting long enough to be properly
        rendered in the visualizer.
        """

        if not cls.BUSY_WAIT_AMOUNT_MS:
            return

        delay = time.perf_counter() + cls.BUSY_WAIT_AMOUNT_MS / 1000

        while time.perf_counter() < delay:
            pass

    @classmethod
    def on_begin(cls):
        """Create a begin event
        """

        # cls._new_evt(cls.EventType.BEGIN)

    @classmethod
    def on_dropped_packet(cls):
        """Create a dropped packet event
        """

        cls._new_evt(cls.EventType.PACKET_DROP)
        cls._busy_wait()

    @classmethod
    def on_packet_retransmit(cls):
        """Create a packet retransmit event
        """

        cls._new_evt(cls.EventType.PACKET_RETRANSMIT)
        cls._busy_wait()

    @classmethod
    def on_connection_reset(cls):
        """Create a connection reset event
        """

        cls._new_evt(cls.EventType.CONNECTION_RESET)
        cls._busy_wait()

    @classmethod
    def on_packet_transmit(cls):
        """Create a packet transmit event
        """

        cls._new_evt(cls.EventType.PACKET_TRANSMIT)

    @classmethod
    def end(cls, fail_rate: float = None):
        """End the summarizer contexr

        Args:
            fail_rate (float, optional): Measurer fail rate of the
            current test. Defaults to None.
        """

        # cls._new_evt(cls.EventType.END)

        cls._draw_timeline(fail_rate)
        cls.serialize()

    @classmethod
    def _draw_timeline(cls, fail_rate: float or None):
        """Sets up the Visualizer context and uses it to draw a timeline
        graph
        """

        Visualizer.begin(cls.SAVE_FOLDER + "/" + cls.current_aes_mode)

        evt_names = [
            cls.EventType.PACKET_TRANSMIT.name,
            cls.EventType.PACKET_DROP.name,
            cls.EventType.PACKET_RETRANSMIT.name,
            cls.EventType.CONNECTION_RESET.name
        ]

        Visualizer.add_all_event_names(evt_names)

        event_list = cls.events[cls.current_aes_mode]
        event_list[-1].end_timestamp = cls.get_current_time()

        for event in cls.events[cls.current_aes_mode]:
            Visualizer.add_event(event.timestamp, event.end_timestamp, event.event_type.name)

        plot_title = "AES mode: " + cls.current_aes_mode.upper() + "."

        if fail_rate:
            plot_title += f" Packet fail rate: {fail_rate:.2f}%."

        Visualizer.end(plot_title, f"Fail rate {fail_rate:.2f}%")


    @classmethod
    def serialize(cls):
        """_summary_
        """

        with open(cls.SAVE_FOLDER + "/data.pickle", "wb") as F:
            pickle.dump(cls.events, F)

    @classmethod
    def deserialize(cls, path: str):
        """_summary_

        Args:
            path (str): _description_
        """

        with open(path, "rb") as F:
            cls.events = pickle.load(F)

        for key in cls.events:
            cls.current_aes_mode = key
            cls._draw_timeline(None)

    @classmethod
    def get_current_time(cls) -> float:
        """_summary_

        Returns:
            float: _description_
        """

        return time.perf_counter() - cls.started_at
