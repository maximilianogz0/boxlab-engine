# acoustics.py
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

FMIN = 20.0
FMAX = 20000.0


def read_frd(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    f, mag, phase = [], [], []
    with p.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            s = line.strip()
            if not s or s[0] in ("*", "#", ";"):
                continue
            parts = s.replace(",", ".").split()
            if len(parts) < 2:
                continue
            try:
                freq = float(parts[0])
                m = float(parts[1])
                ph = float(parts[2]) if len(parts) > 2 else np.nan
            except Exception:
                continue
            f.append(freq); mag.append(m); phase.append(ph)

    f = np.asarray(f, dtype=float)
    mag = np.asarray(mag, dtype=float)
    phase = np.asarray(phase, dtype=float)

    if f.size > 1:
        idx = np.argsort(f)
        f, mag, phase = f[idx], mag[idx], phase[idx]

    # ← Filtra al rango 20 Hz – 20 kHz y descarta no finitos
    sel = (f >= FMIN) & (f <= FMAX) & np.isfinite(mag)
    f, mag = f[sel], mag[sel]
    phase = (phase[sel] if phase.size else phase)

    return f, mag, phase


class FRDPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("FRD (magnitud)"))
        self._fixed_ylim = None

        self.fig = Figure(figsize=(4, 2.8))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._init_axes()
        lay.addWidget(self.canvas)

    def _init_axes(self):
        self.ax.clear()
        self.ax.set_xscale("log")
        self.ax.set_xlim(20, 20000)
        self.ax.set_xlabel("Frecuencia [Hz]")
        self.ax.set_ylabel("Magnitud [dB]")
        if self._fixed_ylim:                  
            self.ax.set_ylim(*self._fixed_ylim)
        self.ax.grid(True, which="both", linewidth=0.3)
        
    def set_fixed_ylim(self, y_min: float, y_max: float):   # <— NUEVO
        self._fixed_ylim = (float(y_min), float(y_max))
        self.ax.set_ylim(self._fixed_ylim)
        self.canvas.draw_idle()    

    def clear(self, msg=""):
        self._init_axes()
        if msg:
            self.ax.text(0.5, 0.5, msg, ha="center", va="center", transform=self.ax.transAxes)
        self.canvas.draw_idle()

    def plot_frd(self, path: str):
        self._init_axes()
        if not path or not Path(path).exists():
            self.clear("Sin FRD")
            return
        try:
            f, mag, _ = read_frd(path)
        except Exception as e:
            self.clear(f"Error: {e}")
            return

        if f.size == 0:
            self.clear("FRD vacío")
            return

        # dentro de FRDPlot.plot_frd(), justo después de:
        self.ax.plot(f, mag, linewidth=0.9)

        if self._fixed_ylim:
            ymin, ymax = self._fixed_ylim
            dmin = float(np.nanmin(mag))
            dmax = float(np.nanmax(mag))
            # Expande si los datos exceden los límites fijos actuales
            if np.isfinite(dmin) and dmin < ymin:
                ymin = dmin - 0.5
            if np.isfinite(dmax) and dmax > ymax:
                ymax = dmax + 0.5
            self._fixed_ylim = (ymin, ymax)
            self.ax.set_ylim(self._fixed_ylim)
        else:
            y1 = float(np.nanpercentile(mag, 1))
            y2 = float(np.nanpercentile(mag, 99))
            if np.isfinite(y1) and np.isfinite(y2) and y2 > y1:
                pad = 0.1 * (y2 - y1)
                self.ax.set_ylim(y1 - pad, y2 + pad)

        self.fig.tight_layout()
        self.canvas.draw_idle()

        # <- SAFETY: garantiza que el ymax cubre el pico real
        try:
            dmax = float(np.nanmax(mag))
            ymin, ymax = self.ax.get_ylim()
            if np.isfinite(dmax) and dmax > ymax:
                self.ax.set_ylim(ymin, dmax + 0.5)
                self.canvas.draw_idle()
        except Exception:
            pass




# (fuera de la clase, al final del archivo)
def mag_limits_from_frd_paths(paths, pad_db=1.0):
    vals = []
    for p in paths:
        if not p:
            continue
        try:
            _, mag, _ = read_frd(p)
            if mag.size:
                vals.append(mag)
        except Exception:
            pass
    if not vals:
        return None
    mags = np.concatenate(vals)
    lo = float(np.nanmin(mags))
    hi = float(np.nanmax(mags))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return None
    return lo - pad_db, hi + pad_db
