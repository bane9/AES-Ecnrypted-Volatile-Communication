"""_summary_
"""

import os
import pickle
from matplotlib import pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.lines as mlines
from matplotlib.figure import figaspect
import numpy as np


class Visualizer:
    """_summary_
    """

    IMAGE_FILENAME = "timeline.png"

    data: dict[str, list[float]]
    save_path: str

    @classmethod
    def begin(cls, save_folder_path: str):
        """_summary_

        Args:
            save_folder_path (str): _description_
        """

        cls.save_path = save_folder_path + "/" + cls.IMAGE_FILENAME
        cls.data = {}
        cls.data["evt_start"] = []
        cls.data["evt_end"] = []
        cls.data["evt_name"] = []
        cls.data["evt_color_map"] = {}

    @classmethod
    def add_all_event_names(cls, event_names: list[str]):
        """_summary_

        Args:
            event_names (list[str]): _description_
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
        """_summary_

        Args:
            event_begin (int): _description_
            event_end (int): _description_
            event_name (str): _description_
        """

        cls.data["evt_start"].append(event_begin)
        cls.data["evt_end"].append(event_end)
        cls.data["evt_name"].append(event_name)

    @classmethod
    def _generate_bar_plot(cls, data: dict[str, float or str], y_offset=0.0) -> PolyCollection:
        """_summary_

        Args:
            data (dict[str, float or str]): _description_
            y_offset (float, optional): _description_. Defaults to 0.0.

        Returns:
            PolyCollection: _description_
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
        """_summary_

        Args:
            plot_title (str, optional): _description_. Defaults to "".
            additional_data (str, optional): _description_. Defaults to "".
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
            plt.rcParams['axes.titley'] = 1.1
            ax.set_title(plot_title)

        ax.set_xlabel("Time since stream start [s]")
        ax.axes.get_yaxis().set_visible(False)

        with open(os.path.dirname(cls.save_path) + "/events.pickle", "wb") as F:
            pickle.dump(cls.data, F)

        plt.savefig(cls.save_path, dpi=300, bbox_inches='tight')

    @classmethod
    def generate_comparative_plot(cls):
        """_summary_
        """

        path = os.path.dirname(cls.save_path)
        path = os.path.join(path, "../")

        data_list: dict[str, float or str] = {}

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

        for k, v in data_list[aes]["evt_color_map"].items():
            k = k.replace("_", " ").title()

            handles.append(mlines.Line2D([], [], color=v, label=k))

        ax.legend(handles=handles, loc="upper center",
                  ncol=len(data_list[aes]["evt_color_map"]),
                  bbox_to_anchor=(0.5, 1.1125),
                  fancybox=True, shadow=True)

        ax.axes.get_yaxis().set_visible(False)

        time_diffs = [(x["evt_end"][-1] - x["evt_start"][0]) for x in data_list.values()]

        ax.set_xlabel(f"Time since stream start [s].\nDuration mean {np.mean(time_diffs):.2f}s"
                      f"\nDuration median {np.median(time_diffs):.2f}s")

        ax.autoscale()

        plt.rcParams['axes.titley'] = 1.122
        ax.set_title("Timeline comparative graph")

        plt.savefig(os.path.join(path, "comparative.png"), dpi=600, bbox_inches='tight')
