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
        
        self._fnull_line = None
        self._fnull_text = None
        self._shade_patch = None
        self.shade_enabled = True
        self.shade_side = "right"   # "left" o "right"
        self.shade_alpha = 0.18
        self.shade_color = "tab:blue"
        self._last_fnull = None




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
        
        def _render_shades(self):
            # limpiar artistas previos
            for art in self._shade_artists:
                try: art.remove()
                except Exception: pass
            self._shade_artists = []

            x0, x1 = self.ax.get_xlim()

            for spec in getattr(self, "_shade_regions", []):
                if not spec.get("enabled", True):
                    continue

                # resolver referencia en Hz
                if "x" in spec and np.isfinite(spec["x"]):
                    xref = float(spec["x"])
                elif spec.get("ref") == "fnull":
                    xref = float(self._last_fnull) if self._last_fnull is not None else np.nan
                else:
                    xref = np.nan
                if not np.isfinite(xref):
                    continue

                # lado o rango explícito
                side = spec.get("side", None)  # "left" | "right" | None
                rng  = spec.get("range", None) # (xa, xb) opcional

                # estilo
                color = spec.get("color", "tab:red")
                alpha = float(spec.get("alpha", 0.15))
                z     = float(spec.get("zorder", 2.0))

                # decidir intervalos
                if isinstance(rng, (tuple, list)) and len(rng) == 2 and all(np.isfinite(rng)):
                    xa, xb = float(rng[0]), float(rng[1])
                elif side == "left":
                    xa, xb = x0, xref
                elif side == "right":
                    xa, xb = xref, x1
                else:
                    # por defecto: nada si no hay side ni range válido
                    continue

                patch = self.ax.axvspan(xa, xb, color=color, alpha=alpha, zorder=z)
                self._shade_artists.append(patch)

            self.canvas.draw_idle()


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
                
        if self._last_fnull is not None:
            self.mark_fnull(self._last_fnull)


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
    
    def mark_fnull(self, fnull_hz: float):
        if self._fnull_line is not None:
            try: self._fnull_line.remove()
            except Exception: pass
            self._fnull_line = None

        if self._fnull_text is not None:
            try: self._fnull_text.remove()
            except Exception: pass
            self._fnull_text = None

        self._fnull_line = self.ax.axvline(fnull_hz, linestyle="--", linewidth=1.0, alpha=0.9)
        
        """
        ymin, ymax = self.ax.get_ylim()
        self._fnull_text = self.ax.text(fnull_hz, 
                                        ymax, 
                                        "f_null", 
                                        rotation=90,
                                        va="top", 
                                        ha="right", 
                                        fontsize=8, 
                                        alpha=0.9)
        """

        def _fmt_f(f):
            return f"{f/1000:.2f} kHz" if f >= 1000 else f"{int(round(f))} Hz"

        self._fnull_text = self.ax.text(
            fnull_hz, 0.0,                         # en el borde inferior del eje
            f"Woofer_1st_Null\n{_fmt_f(fnull_hz)}",         # nombre + valor
            transform=self.ax.get_xaxis_transform(),  # y en coords de eje
            ha="center", va="bottom",
            fontsize=8, alpha=0.9, rotation=0,
            clip_on=False
        )

        
        self._last_fnull = float(fnull_hz)

        if self._shade_patch is not None:
            try: self._shade_patch.remove()
            except Exception: pass
            self._shade_patch = None

        if self.shade_enabled and np.isfinite(fnull_hz):
            x0, x1 = self.ax.get_xlim()
            if self.shade_side == "left":
                xa, xb = x0, fnull_hz
            elif self.shade_side == "right":
                xa, xb = fnull_hz, x1
            else:
                xa = xb = None

            if xa is not None:
                self._shade_patch = self.ax.axvspan(
                    xa, xb, alpha=self.shade_alpha, color=self.shade_color, zorder=0.5
                )

        self.canvas.draw_idle()






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
