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
    def __init__(self, save_path: str = None, fig_width: int = 20, fig_height: int = 10):
        self.save_path = Path(save_path) if save_path else None
        self.colors = ['steelblue', 'coral', 'seagreen', 'gold', 'teal', 'tomato', 'slategray', 'plum', 'salmon',
                       'pink', 'purple', 'red']
        self.file_name = None
        self.fig_size = (fig_width, fig_height)

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
        plt.figure(figsize=self.fig_size)
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
                        x_label: str = "",  y_label: str = "", pdf: bool = False, file_name: str = None):
        bins = np.linspace(interval[0], interval[1], bins_size)
        plt.figure(figsize=self.fig_size)
        for i, (lst, label) in enumerate(zip(data, labels)):
            n, x, _ = plt.hist(lst, bins=bins, label=label, alpha=0.8, density=pdf, color=self.colors[i])
            if pdf:
                density = stats.gaussian_kde(lst)
                plt.plot(x, density(x), color=self.colors[-(i+1)], label=f"{label}_kde")
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.legend(loc='upper right')
        self.file_name = "histogram" if not file_name else file_name
        self.show()

    def subplots(self, x_data: List, y_data: List[List[List]], fig_title: str, x_label: str, y_labels: List[AnyStr],
                 legend: List):
        nrows = len(y_data)
        fig, rows = plt.subplots(nrows, 1)
        fig.suptitle(fig_title)
        fig.set_size_inches(self.fig_size[0], self.fig_size[1], forward=True)

        for y, row, y_label in zip(y_data, rows, y_labels):
            for line in y:
                row.plot(x_data, line, '.-')
            row.set_ylabel(y_label)
            row.legend(legend, loc='best')
            # row.tick_params(labelrotation=20)

        rows[-1].set_xlabel(x_label)

        self.file_name = "subplots"
        self.show()

    # source https://stackoverflow.com/a/18975065
    def bars(self, data: List[int], index: List[AnyStr], bar_label: str, y_label: str):
        s = pd.Series(data, index=index)

        # Set descriptions:
        plt.ylabel(y_label)
        plt.xlabel(bar_label)
        plt.figure(figsize=self.fig_size)

        # Plot the data:
        s.plot.bar(color=self.colors, alpha=0.7)
        self.file_name = "bars"
        self.show()

    def show(self):
        # Shows plot or saves it in the plots folder
        if self.save_path:
            plt.savefig(f"{self.save_path / Path(self.file_name)}")
            plt.clf()
        else:
            plt.show()
