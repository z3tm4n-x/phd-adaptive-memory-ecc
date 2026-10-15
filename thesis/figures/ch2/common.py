"""Общие настройки схем главы 2: векторный SVG, чёрно-белая читаемость, детерминированный вывод."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.linewidth": 0.6,
    "svg.fonttype": "path", "svg.hashsalt": "thesis-ch2", "lines.linewidth": 0.8,
})
CM = 1 / 2.54


def save(fig, stem, preview=None):
    fig.savefig(f"{stem}.svg", metadata={"Date": None, "Creator": "thesis/figures/ch2"})
    if preview:
        fig.savefig(preview, dpi=200)
