"""_summary_
"""

import os
import pickle
from matplotlib import pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.lines as mlines
from matplotlib.figure import figaspect


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
    def add_event(cls, event_begin: int, event_end: int, event_name: str):
        """_summary_

        Args:
            event_begin (int): _description_
            event_end (int): _description_
            event_name (str): _description_
        """

        available_colors = (
            "tab:blue",
            "tab:orange",
            "tab:green",
            "tab:red",
            "tab:purple",
            "tab:brown",
        )

        cls.data["evt_start"].append(event_begin)
        cls.data["evt_end"].append(event_end)
        cls.data["evt_name"].append(event_name)

        if event_name not in cls.data["evt_color_map"]:
            cls.data["evt_color_map"][event_name] = available_colors[len(cls.data['evt_color_map'])]

    @classmethod
    def end(cls, plot_title=""):
        """_summary_

        Args:
            plot_title (str, optional): _description_. Defaults to "".
        """

        os.makedirs(os.path.dirname(cls.save_path), exist_ok=True)

        start = cls.data["evt_start"]
        end = cls.data["evt_end"]
        events = cls.data["evt_name"]
        color_map: dict = cls.data["evt_color_map"]

        verticies = []
        colors = []

        vert_side = 0.1

        for start_, end_, evt_name, i in zip(start, end, events, range(len(end))):
            if i + 1 < len(end):
                end_ = end[i + 1]

            vert = [(start_, -vert_side),
                    (start_, vert_side),
                    (end_, vert_side),
                    (end_, -vert_side),
                    (start_, -vert_side)]

            verticies.append(vert)
            colors.append(color_map[evt_name])

        bars = PolyCollection(verticies, facecolors=colors)

        _, ax = plt.subplots(figsize=figaspect(9 / 20))
        ax.add_collection(bars)
        ax.autoscale()

        handles = []

        for k, v in color_map.items():
            k = k.replace("_", " ").title()

            handles.append(mlines.Line2D([], [], color=v, label=k))

        ax.legend(handles=handles, loc="upper center", ncol=len(color_map), bbox_to_anchor=(0.5, 1.1),
                  fancybox=True, shadow=True)

        plt.rcParams['axes.titley'] = 1.1

        if plot_title:
            ax.set_title(plot_title)

        ax.set_xlabel("Time since stream start [ns]")
        ax.axes.get_yaxis().set_visible(False)

        with open(os.path.dirname(cls.save_path) + "/figure.pickle", "wb") as F:
            pickle.dump(plt.gcf(), F)

        plt.savefig(cls.save_path, dpi=300, bbox_inches='tight')
