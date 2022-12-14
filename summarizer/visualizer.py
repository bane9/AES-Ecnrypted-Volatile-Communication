"""Visualizer module for creating timeline graphs
"""

import os
import pickle
from matplotlib import pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.lines as mlines
from matplotlib.figure import figaspect
from sortedcontainers import SortedDict


class Visualizer:
    """Visualizer class for creating timeline graphs
    """

    IMAGE_FILENAME = "timeline.png"

    data: dict[str, list[float]]
    save_path: str

    @classmethod
    def begin(cls, save_folder_path: str):
        """Initialize a new visualization context

        Args:
            save_folder_path (str): Path to the folder which
            the visualization graph image will be saved.
            The folder will be created if it doesn't exist.
        """

        cls.save_path = save_folder_path + "/" + cls.IMAGE_FILENAME
        cls.data = {}
        cls.data["evt_start"] = []
        cls.data["evt_end"] = []
        cls.data["evt_name"] = []
        cls.data["evt_color_map"] = {}

    @classmethod
    def add_all_event_names(cls, event_names: list[str]):
        """Add event names so they can be mapped to certain colors.
        The current color mapping is:
        event_names[0] = blue
        event_names[1] = orange
        event_names[2] = green
        event_names[3] = red
        event_names[4] = purple
        event_names[5] = brown

        If len(event_names) is larger than 6, an error will be thrown

        Args:
            event_names (list[str]): List of event names
        """

        available_colors = (
            "tab:blue",
            "tab:orange",
            "tab:green",
            "tab:red",
            "tab:purple",
            "tab:brown",
        )

        for i, x in enumerate(event_names):
            cls.data["evt_color_map"][x] = available_colors[i]

    @classmethod
    def add_event(cls, event_begin: int, event_end: int, event_name: str):
        """Add an event to the event context

        Args:
            event_begin (int): Timestamp of when the event began
            event_end (int): Timestamp of when the event ended
            event_name (str): Name of the event
        """

        cls.data["evt_start"].append(event_begin)
        cls.data["evt_end"].append(event_end)
        cls.data["evt_name"].append(event_name)

    @classmethod
    def _generate_bar_plot(cls, data: dict[str, float or str], y_offset=0.0) -> PolyCollection:
        """Generate a collection of polygons that represent the timeline
        of events

        Args:
            data (dict[str, float or str]): Events to be plotted
            y_offset (float, optional): y offset in the graph for the bar plot. Defaults to 0.0.

        Returns:
            PolyCollection: Collection of polygons to be drawn
        """

        start = data["evt_start"]
        end = data["evt_end"]
        events = data["evt_name"]
        color_map: dict = data["evt_color_map"]

        verticies = []
        colors = []

        vert_side = 0.3

        for start_, end_, evt_name, i in zip(start, end, events, range(len(end))):
            if i + 1 < len(end):
                end_ = end[i + 1]

            vertex = [(start_, y_offset - vert_side),
                      (start_, y_offset + vert_side),
                      (end_, y_offset + vert_side),
                      (end_, y_offset - vert_side),
                      (start_, y_offset - vert_side)]

            verticies.append(vertex)
            colors.append(color_map[evt_name])

        return PolyCollection(verticies, facecolors=colors)

    @classmethod
    def end(cls, plot_title="", additional_data=""):
        """End the visualization context. It will draw the timeline plot
        with given events and other data.

        Args:
            plot_title (str, optional): Title of the plot. Defaults to "".
            additional_data (str, optional): Any additional data
            relevant to the plot. Defaults to "".
        """

        os.makedirs(os.path.dirname(cls.save_path), exist_ok=True)

        cls.data["additional_data"] = additional_data

        events = cls.data["evt_name"]
        color_map: dict = cls.data["evt_color_map"]

        bars = cls._generate_bar_plot(cls.data)

        _, ax = plt.subplots(figsize=figaspect(9 / 20))
        ax.add_collection(bars)
        ax.autoscale()

        handles = []

        available_events = set(events)

        for k, v in color_map.items():
            if k in available_events:
                k = k.replace("_", " ").title()

                handles.append(mlines.Line2D([], [], color=v, label=k))

        ax.legend(handles=handles, loc="upper center", ncol=len(color_map), bbox_to_anchor=(0.5, 1.1),
                  fancybox=True, shadow=True)

        if plot_title:
            plt.rcParams["axes.titley"] = 1.1
            ax.set_title(plot_title)

        ax.set_xlabel("Time since stream start [s]")
        ax.axes.get_yaxis().set_visible(False)

        with open(os.path.dirname(cls.save_path) + "/events.pickle", "wb") as F:
            pickle.dump(cls.data, F)

        plt.savefig(cls.save_path, dpi=300, bbox_inches="tight")

    @classmethod
    def generate_comparative_plot(cls, additional_data=""):
        """Takes all generated plots saved in the current output folder
        and combines them into one plot.

        Args:
            additional_data (str, optional): Any additional data relevant
            the the shared plot. Defaults to "".
        """

        path = os.path.dirname(cls.save_path)
        path = os.path.join(path, "../")

        data_list: SortedDict[str, float or str] = SortedDict()

        for root, subdirs, _ in os.walk(path):
            for directory in subdirs:
                newdirectory = os.path.join(root, directory)
                for root1, _, files in os.walk(newdirectory):
                    for file in files:
                        file: str
                        if file.endswith(".pickle"):
                            with open(os.path.join(root1, file), "rb") as F:
                                data_list[directory] = pickle.load(F)

        plt.cla()
        plt.clf()
        plt.close("all")

        _, ax = plt.subplots(figsize=figaspect(9 / 20))
        aes: str

        for i, (aes, events) in enumerate(data_list.items()):
            y_offset = i
            bars = cls._generate_bar_plot(events, y_offset=y_offset)
            ax.add_collection(bars)

            text = aes.upper()

            if data_list[aes]["additional_data"]:
                text += f" ({data_list[aes]['additional_data']})"

            text += " " * 8

            ax.text(x=0.00,
                    y=y_offset,
                    s=text,
                    horizontalalignment="right",
                    fontsize=11.3, fontweight="bold")

        handles = []

        event_types = set(data_list[aes]["evt_name"])

        for x in data_list.values():
            event_types.update(x["evt_name"])

        for k, v in data_list[aes]["evt_color_map"].items():
            if k in event_types:
                k = k.replace("_", " ").title()

                handles.append(mlines.Line2D([], [], color=v, label=k))

        ax.legend(handles=handles, loc="upper center",
                  ncol=len(data_list[aes]["evt_color_map"]),
                  bbox_to_anchor=(0.5, 1.1125),
                  fancybox=True, shadow=True)

        ax.axes.get_yaxis().set_visible(False)

        xlabel = "Time since stream start [s]"

        if additional_data:
            xlabel += "\n\n" + additional_data

        ax.set_xlabel(xlabel)

        ax.autoscale()

        plt.rcParams["axes.titley"] = 1.122
        ax.set_title("Timeline comparative graph")

        plt.savefig(os.path.join(path, "comparative.png"), dpi=600, bbox_inches="tight")
