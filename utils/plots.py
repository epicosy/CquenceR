from pathlib import Path
from typing import List, AnyStr, Tuple

from pylab import *
import numpy as np
import pandas as pd
from scipy import stats

plt.style.use('seaborn-dark')


def scatter(x: list, y: list, x_label: str, y_label: str):
    colors = np.random.rand(len(x))
    plt.scatter(x, y, c=colors, alpha=0.8)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()


class Plotter:
    def __init__(self, save_path: str = None):
        self.save_path = Path(save_path) if save_path else None
        self.colors = ['steelblue', 'coral', 'seagreen', 'tomato', 'gold', 'plum', 'slategray', 'purple', 'teal', 'salmon']
        self.file_name = None

        if self.save_path and not self.save_path.exists():
            self.save_path.mkdir()

    def zipf_log(self, labels: List, values: List):
        # TODO: refactor this method
        # sort values in descending order
        idx_sort = np.argsort(values)[::-1]

        # rearrange data
        tokens = np.array(labels)[idx_sort]
        counts = np.array(values)[idx_sort]

        # source https://towardsdatascience.com/another-twitter-sentiment-analysis-with-python-part-3-zipfs-law-data-visualisation-fc9eadda71e7
        ranks = arange(1, len(counts) + 1)
        idxs = argsort(-counts)
        frequencies = counts[idxs]
        plt.figure(figsize=(8, 6))
        plt.ylim(1, 10 ** 6)
        plt.xlim(1, 10 ** 6)
        loglog(ranks, frequencies, marker=".")
        plt.plot([1, frequencies[0]], [frequencies[0], 1], color='r')
        title("Zipf plot for dataset tokens")
        xlabel("Frequency rank of token")
        ylabel("Absolute frequency of token")
        grid(True)

        for n in list(logspace(-0.5, log10(len(counts) - 2), 25).astype(int)):
            dummy = text(ranks[n], frequencies[n], " " + tokens[idxs[n]],
                         verticalalignment="bottom",
                         horizontalalignment="left")

        self.file_name = "zipf_log"
        self.show()

    def multi_histogram(self, data: List[List], labels: List[AnyStr], interval: Tuple[int, int], bins_size: int = 100,
                        x_label: str = "",  y_label: str = "", pdf: bool = False):
        bins = np.linspace(interval[0], interval[1], bins_size)
        for lst, label in zip(data, labels):
            n, x, _ = plt.hist(lst, bins=bins, label=label, alpha=0.8, density=pdf)
            if pdf:
                density = stats.gaussian_kde(lst)
                plt.plot(x, density(x), color='r')
        plt.ylabel(x_label)
        plt.xlabel(y_label)
        plt.legend(loc='upper right')
        self.file_name = "histogram"
        self.show()

    # source https://stackoverflow.com/a/18975065
    def bars(self, data: List[int], index: List[AnyStr], bar_label: str, y_label: str):
        s = pd.Series(data, index=index)

        # Set descriptions:
        plt.ylabel(y_label)
        plt.xlabel(bar_label)

        # Plot the data:
        s.plot.bar(color=self.colors, alpha=0.7)
        self.file_name = "bars"
        self.show()

    def color_map(self, values: list):
        # generate 2 2d grids for the x & y bounds
        size = len(values)
        y, x = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
        c = plt.pcolormesh(x, y, values, cmap='RdBu', vmin=min(values), vmax=max(values))
        # set the limits of the plot to the limits of the data
        plt.axis([x.min(), x.max(), y.min(), y.max()])
        plt.colorbar(c)

        self.file_name = "color_map"
        self.show()

    def show(self):
        # Shows plot or saves it in the plots folder
        if self.save_path:
            plt.savefig(f"{self.save_path / Path(self.file_name)}")
            plt.clf()
        else:
            plt.show()
