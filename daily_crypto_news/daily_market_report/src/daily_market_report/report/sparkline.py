from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sparkline_png_base64(values: list[float], width: float = 2.2, height: float = 0.45, dpi: int = 120) -> str:
    if not values:
        return ""
    fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
    ax.plot(range(len(values)), values, color="#16a34a", linewidth=1.2)
    ax.axis("off")
    for s in ax.spines.values():
        s.set_visible(False)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")
