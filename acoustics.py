# acoustics.py
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from matplotlib.ticker import FixedLocator, FuncFormatter


import matplotlib as mpl  # añadir si no está

# Tamaño global compacto
_BASE = 7  # cambia este número si quieres aún más pequeño

mpl.rcParams.update({
    "font.size":        _BASE,        # base global
    "axes.titlesize":   _BASE + 1,    # título de ejes
    "axes.labelsize":   _BASE,        # labels de ejes
    "xtick.labelsize":  _BASE - 1,    # ticks X
    "ytick.labelsize":  _BASE - 1,    # ticks Y
    "legend.fontsize":  _BASE - 1,    # leyendas
    "figure.titlesize": _BASE + 1,
})


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

def read_z(path: str):
    """Lee archivos ' - Z.txt': f[Hz], |Z|[ohm], fase[deg](opcional)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    f, zmag, zph = [], [], []
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
            f.append(freq); zmag.append(m); zph.append(ph)

    f = np.asarray(f, dtype=float)
    zmag = np.asarray(zmag, dtype=float)
    zph = np.asarray(zph, dtype=float)

    if f.size > 1:
        idx = np.argsort(f)
        f, zmag, zph = f[idx], zmag[idx], zph[idx]

    sel = (f >= FMIN) & (f <= FMAX) & np.isfinite(zmag)
    return f[sel], zmag[sel], zph[sel] if zph.size else zph


# acoustics.py
class FRDPlot(QWidget):
    def __init__(self, parent=None, *, reader=read_frd,
                 y_label="Magnitud [dB SPL]", title="FRD (magnitud)"):
        super().__init__(parent)
        self._reader = reader
        self._y_label = y_label
        lay = QVBoxLayout(self)
        self.title_label = QLabel(title)


        lay.addWidget(self.title_label)
        #self.title_label.setVisible(show_header)  # ← oculta por defecto

        lay.setContentsMargins(0, 0, 0, 0)   # ← sin márgenes
        lay.setSpacing(0)                    # ← sin espaciado
        self._fixed_ylim = None
        self._fnull_line = None
        self._fnull_text = None
        self._shade_patch = None
        self.shade_enabled = True
        self.shade_side = "right"
        self.shade_alpha = 0.18
        self.shade_color = "tab:blue"
        self._last_fnull = None
        # NUEVO: patches de sombreado por eje
        self._shade_mag = None
        self._shade_phase = None


        self.fig = Figure(figsize=(2, 2.8), constrained_layout=True)
        self.canvas = FigureCanvas(self.fig)
        # opcional: quitar márgenes internos del propio widget
        self.canvas.setContentsMargins(0, 0, 0, 0)

        gs = self.fig.add_gridspec(2, 1, height_ratios=[2.0, 1.2], hspace=0.05)
        self.ax_mag   = self.fig.add_subplot(gs[0])
        self.ax_phase = self.fig.add_subplot(gs[1], sharex=self.ax_mag)
        
        self._init_axes()
        lay.addWidget(self.canvas)

    def set_header_visible(self, visible: bool):
        self.title_label.setVisible(bool(visible))


    def _init_axes(self):
        # Magnitud
        self.ax_mag.clear()
        self.ax_mag.set_xlim(20, 20000)
        self.ax_mag.set_xscale("log")
        self.ax_mag.set_ylabel(self._y_label)
        if self._fixed_ylim:
            self.ax_mag.set_ylim(*self._fixed_ylim)
        self.ax_mag.grid(True, which="both", linewidth=0.3)

        # Fase
        self.ax_phase.clear()
        self.ax_phase.set_xlim(20, 20000)
        self.ax_phase.set_xscale("log")
        self.ax_phase.set_xlabel("Frecuencia [Hz]")
        self.ax_phase.set_ylabel("Fase [°]")
        self.ax_phase.set_ylim(-180, 180)   # límites fijos de fase
        # Ticks de fase cada 90° hasta ±180°, con símbolo de grados
        ticks = np.arange(-180, 181, 90)
        self.ax_phase.yaxis.set_major_locator(FixedLocator(ticks))
        self.ax_phase.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{int(v)}°"))

        self.ax_phase.grid(True, which="both", linewidth=0.3)

        # ocultar xlabels del eje superior
        for lb in self.ax_mag.get_xticklabels():
            lb.set_visible(False)

        
    def set_title(self, text: str):
        self.title_label.setText(str(text))

    def set_fixed_ylim(self, y_min: float, y_max: float):   # <— NUEVO
        self._fixed_ylim = (float(y_min), float(y_max))
        self.ax_mag.set_ylim(self._fixed_ylim)
        self.canvas.draw_idle()    

    def clear(self, msg=""):
        self._init_axes()
        if msg:
            self.ax_mag.text(0.5, 0.5, msg, ha="center", va="center", transform=self.ax_mag.transAxes)
        self.canvas.draw_idle()

    def plot_file(self, path: str):
        self._init_axes()
        if not path or not Path(path).exists():
            self.clear("Sin FRD")
            return
        try:
            f, mag, phase = self._reader(path)
            
            smoothing_window = 1
            mag = pd.Series(mag).rolling(window=smoothing_window, 
                                         center=True, 
                                         min_periods=1).mean().to_numpy()
            
            if phase.size and np.isfinite(phase).any():
                ph_u = np.unwrap(np.deg2rad(phase))
                ph_u = pd.Series(ph_u).rolling(window=7, 
                                               center=True, 
                                               min_periods=1).mean().to_numpy()
                phase = np.rad2deg(ph_u)
                # Mostrar fase acotada en [-180, 180]
                phase = ((phase + 180) % 360) - 180

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

            x0, x1 = self.ax_mag.get_xlim()

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

                patch = self.ax_mag.axvspan(xa, xb, color=color, alpha=alpha, zorder=z)
                self._shade_artists.append(patch)

            self.canvas.draw_idle()


        # dentro de FRDPlot.plot_frd(), justo después de:
        self.ax_mag.plot(f, mag, linewidth=0.9)
        
        if phase.size and np.isfinite(phase).any():
            self.ax_phase.plot(f, phase, linewidth=0.8)


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
            self.ax_mag.set_ylim(self._fixed_ylim)
        else:
            y1 = float(np.nanpercentile(mag, 1))
            y2 = float(np.nanpercentile(mag, 99))
            if np.isfinite(y1) and np.isfinite(y2) and y2 > y1:
                pad = 0.1 * (y2 - y1)
                self.ax_mag.set_ylim(y1 - pad, y2 + pad)
                
        if self._last_fnull is not None:
            self.mark_fnull(self._last_fnull)


        #self.fig.tight_layout()
        self.canvas.draw_idle()

        # <- SAFETY: garantiza que el ymax cubre el pico real
        try:
            dmax = float(np.nanmax(mag))
            ymin, ymax = self.ax_mag.get_ylim()
            if np.isfinite(dmax) and dmax > ymax:
                self.ax_mag.set_ylim(ymin, dmax + 0.5)
                self.canvas.draw_idle()
        except Exception:
            pass
    
    def plot_frd(self, path: str): #Alias por refactor
        self.plot_file(path)

    
    def mark_fnull(self, fnull_hz: float):
        if self._fnull_line is not None:
            try: self._fnull_line.remove()
            except Exception: pass
            self._fnull_line = None

        if self._fnull_text is not None:
            try: self._fnull_text.remove()
            except Exception: pass
            self._fnull_text = None

        self._fnull_line = self.ax_mag.axvline(fnull_hz, linestyle="--", linewidth=1.0, alpha=0.9)
        self.ax_phase.axvline(fnull_hz, linestyle="--", linewidth=1.0, alpha=0.6)

        
        """
        ymin, ymax = self.ax_mag.get_ylim()
        self._fnull_text = self.ax_mag.text(fnull_hz, 
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

        tag = getattr(self, "_fnull_label", "Woofer 1st_Null")   # ← usa _fnull_label si está seteado
        self._fnull_text = self.ax_mag.text(
            fnull_hz, 0.0,
            f"{tag}\n{_fmt_f(fnull_hz)}",
            transform=self.ax_mag.get_xaxis_transform(),
            ha="center", va="bottom",
            fontsize=8, alpha=0.9, rotation=0, clip_on=False
        )

        
        self._last_fnull = float(fnull_hz)

        # NUEVO: sombrear en ambos subplots (magnitud y fase)
        for attr in ("_shade_mag", "_shade_phase"):
            patch = getattr(self, attr, None)
            if patch is not None:
                try: patch.remove()
                except Exception: pass
                setattr(self, attr, None)

        if self.shade_enabled and np.isfinite(fnull_hz):
            for ax, attr in ((self.ax_mag, "_shade_mag"), (self.ax_phase, "_shade_phase")):
                x0, x1 = ax.get_xlim()
                if self.shade_side == "left":
                    xa, xb = x0, fnull_hz
                elif self.shade_side == "right":
                    xa, xb = fnull_hz, x1
                else:
                    xa = xb = None
                if xa is not None:
                    setattr(self, attr, ax.axvspan(
                        xa, xb, alpha=self.shade_alpha, color=self.shade_color, zorder=0.5
                    ))

        self.canvas.draw_idle()



class ImpedancePlot(FRDPlot):
    def __init__(self, parent=None):
        super().__init__(parent, reader=read_z,
                         y_label="Impedancia [Ω]",
                         title="Impedancia (|Z|)")




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

def z_limits_from_paths(paths, top_pad_ratio=0.05):
    """Devuelve (0, zmax*(1+pad)) a partir de archivos Z encontrados."""
    vals = []
    for p in paths:
        if not p:
            continue
        try:
            _, zmag, _ = read_z(p)
            if zmag.size:
                vals.append(zmag)
        except Exception:
            pass
    if not vals:
        return None
    z = np.concatenate(vals)
    hi = float(np.nanmax(z))
    if not np.isfinite(hi) or hi <= 0:
        return None
    return 0.0, hi * (1.0 + float(top_pad_ratio))
