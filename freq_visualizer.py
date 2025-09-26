#freq_visualizer.py
import os
import glob
import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter


# ---------------------------------------------------------------------
# Configuración de origen de datos
# Define las carpetas de cada lista de drivers (pueden ser iguales)
# ---------------------------------------------------------------------
DIR_LISTA_1 = "data/lista1"   # p.ej. "./frd/woofers"
DIR_LISTA_2 = "data/lista2"   # p.ej. "./frd/tweeters"

# Rango y malla común de frecuencias para graficar (log)
F_COMMON = np.logspace(np.log10(20), np.log10(40000.0), 2400)

# ---------------------------------------------------------------------
# Lectura e interpolación de FRD
# ---------------------------------------------------------------------
def read_frd(path):
    """
    Lee archivo .frd con: freq[Hz], spl[dB], phase[deg].
    Ignora líneas que comienzan con #, ;, * o vacías.
    Devuelve dict con arrays: f, mag_db, phase_deg.
    """
    f = []
    mag = []
    ph = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line[0] in ("#", ";", "*"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                fi = float(parts[0])
                mi = float(parts[1])
                pi = float(parts[2])
            except ValueError:
                continue
            if fi > 0:
                f.append(fi)
                mag.append(mi)
                ph.append(pi)
    if len(f) == 0:
        raise ValueError(f"FRD vacío o inválido: {path}")
    f = np.array(f, dtype=float)
    mag = np.array(mag, dtype=float)
    ph = np.array(ph, dtype=float)
    # Ordenar por frecuencia ascendente (por si el archivo no viene ordenado)
    idx = np.argsort(f)
    return {
        "f": f[idx],
        "mag_db": mag[idx],
        "phase_deg": ph[idx],
        "path": path,
    }

def unwrap_deg(phase_deg):
    """Desenvuelve fase en grados manteniendo continuidad."""
    return np.rad2deg(np.unwrap(np.deg2rad(phase_deg)))

def interp_logx(x_src, y_src, x_tgt, fill_value=np.nan):
    """
    Interpolación 1D sobre eje de frecuencias logarítmico.
    x_src, x_tgt > 0. Interpola y en función de log10(x).
    """
    xs = np.log10(x_src)
    xt = np.log10(x_tgt)
    # np.interp fuera de rango usa los extremos; control explícito con máscara
    y = np.interp(xt, xs, y_src)
    # Opcional: enmascarar fuera de rango para evitar extrapolación implícita
    mask = (x_tgt < np.min(x_src)) | (x_tgt > np.max(x_src))
    if np.isnan(fill_value):
        y[mask] = np.nan
    else:
        y[mask] = fill_value
    return y

def build_H_from_frd(frd_dict, f_tgt):
    """
    Reconstruye H(f) complejo a malla f_tgt.
    Interpola magnitud en dB y fase desenvuelta en grados, ambos en log-f.
    Fuera de rango retorna NaN (que no se grafica si se usa máscara).
    """
    f_src = frd_dict["f"]
    mag_db_src = frd_dict["mag_db"]
    phase_deg_src = unwrap_deg(frd_dict["phase_deg"])

    mag_db = interp_logx(f_src, mag_db_src, f_tgt, fill_value=np.nan)
    phase_deg = interp_logx(f_src, phase_deg_src, f_tgt, fill_value=np.nan)

    # Construcción de H evitando NaN en exponenciales
    amp = np.where(np.isnan(mag_db), np.nan, 10.0**(mag_db/20.0))
    ang = np.where(np.isnan(phase_deg), np.nan, np.deg2rad(phase_deg))
    H = amp * np.exp(1j * ang)
    return H

# ---------------------------------------------------------------------
# Descubrimiento de drivers en carpetas y caché de FRD
# ---------------------------------------------------------------------
def scan_frd(dirpath):
    paths = sorted(glob.glob(os.path.join(dirpath, "*.frd")))
    names = [os.path.splitext(os.path.basename(p))[0] for p in paths]
    return dict(zip(names, paths))

FRD_MAP_1 = scan_frd(DIR_LISTA_1)  # nombre -> ruta
FRD_MAP_2 = scan_frd(DIR_LISTA_2)

# Caché: ruta -> dict frd leído
_FRD_CACHE = {}

def get_frd(path):
    if path not in _FRD_CACHE:
        _FRD_CACHE[path] = read_frd(path)
    return _FRD_CACHE[path]

# ---------------------------------------------------------------------
# Utilidades de presentación
# ---------------------------------------------------------------------
def mag_db_from_H(H):
    return 20.0 * np.log10(np.abs(H))

def phase_deg_from_H(H):
    return np.rad2deg(np.unwrap(np.angle(H)))

# ---------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Vista de respuesta FRD: Magnitud y Fase (log)")
        self.geometry("1080x720")

        # Variables de selección y sombreado
        lista1_names = list(FRD_MAP_1.keys()) if FRD_MAP_1 else []
        lista2_names = list(FRD_MAP_2.keys()) if FRD_MAP_2 else []

        if not lista1_names or not lista2_names:
            raise RuntimeError("No se encontraron archivos .frd en DIR_LISTA_1 o DIR_LISTA_2.")

        self.driver1 = tk.StringVar(value=lista1_names[0])
        self.driver2 = tk.StringVar(value=lista2_names[0])
        self.f_low   = tk.DoubleVar(value=800.0)
        self.f_high  = tk.DoubleVar(value=3500.0)

        # Panel superior de controles
        ctrl = ttk.Frame(self, padding=8)
        ctrl.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(ctrl, text="Lista 1:").grid(row=0, column=0, sticky="w")
        self.cb1 = ttk.Combobox(ctrl, textvariable=self.driver1, values=lista1_names, state="readonly", width=28)
        self.cb1.grid(row=0, column=1, padx=6)
        self.cb1.bind("<<ComboboxSelected>>", self._on_change)

        ttk.Label(ctrl, text="Lista 2:").grid(row=0, column=2, sticky="w")
        self.cb2 = ttk.Combobox(ctrl, textvariable=self.driver2, values=lista2_names, state="readonly", width=28)
        self.cb2.grid(row=0, column=3, padx=6)
        self.cb2.bind("<<ComboboxSelected>>", self._on_change)

        ttk.Label(ctrl, text="f_low [Hz]:").grid(row=0, column=4, sticky="e")
        e1 = ttk.Entry(ctrl, textvariable=self.f_low, width=10)
        e1.grid(row=0, column=5, padx=4)

        ttk.Label(ctrl, text="f_high [Hz]:").grid(row=0, column=6, sticky="e")
        e2 = ttk.Entry(ctrl, textvariable=self.f_high, width=10)
        e2.grid(row=0, column=7, padx=4)

        self.btn_update = ttk.Button(ctrl, text="Actualizar", command=self.update_plot)
        self.btn_update.grid(row=0, column=8, padx=8)

        # Figura
        self.fig = Figure(figsize=(9, 6), dpi=100)
        self.ax_mag = self.fig.add_subplot(2, 1, 1)
        self.ax_ph  = self.fig.add_subplot(2, 1, 2)
        self.fig.tight_layout(pad=2.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.update_plot()

    def _on_change(self, _evt=None):
        self.update_plot()

    def _plot_driver_from_frd(self, driver_name, frd_map, ax_mag, ax_ph, label):
        path = frd_map[driver_name]
        frd = get_frd(path)
        H = build_H_from_frd(frd, F_COMMON)

        # Enmascarar NaN fuera de rango
        mask = ~np.isnan(np.real(H))
        f_plot = F_COMMON[mask]
        H_plot = H[mask]

        ax_mag.plot(f_plot, mag_db_from_H(H_plot), label=label, linewidth=1.2)
        ax_ph.plot(f_plot, phase_deg_from_H(H_plot), label=label, linewidth=1.0)

    def _shade_band(self, ax):
        f1 = float(self.f_low.get())
        f2 = float(self.f_high.get())
        if f2 < f1:
            f1, f2 = f2, f1
        ax.axvspan(f1, f2, alpha=0.2)

    def update_plot(self):
        self.ax_mag.clear()
        self.ax_ph.clear()

        self.ax_mag.set_xscale("log")
        self.ax_ph.set_xscale("log")
        
        self.ax_mag.set_xlim(20, 20000)
        self.ax_ph.set_xlim(20, 20000)

        
        # Definir ticks típicos de audio
        xticks_audio = [20, 31.5, 40, 63, 80, 100, 125, 160, 200, 250, 315,
                        400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500,
                        3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000,
                        20000]
        xlabels_audio = [str(f) if f < 1000 else f"{int(f/1000)}k" for f in xticks_audio]

        self.ax_mag.set_xticks(xticks_audio)
        self.ax_mag.set_xticklabels(xlabels_audio)
        self.ax_ph.set_xticks(xticks_audio)
        self.ax_ph.set_xticklabels(xlabels_audio)

        from matplotlib.ticker import LogLocator
        minor = LogLocator(base=10, subs=(2, 3, 5))
        self.ax_mag.xaxis.set_minor_locator(minor)
        self.ax_ph.xaxis.set_minor_locator(minor)


        self._plot_driver_from_frd(self.driver1.get(), FRD_MAP_1, self.ax_mag, self.ax_ph, f"{self.driver1.get()}")
        self._plot_driver_from_frd(self.driver2.get(), FRD_MAP_2, self.ax_mag, self.ax_ph, f"{self.driver2.get()}")

        self.ax_mag.set_ylabel("Magnitud [dB]")
        self.ax_ph.set_ylabel("Fase [°]")
        self.ax_ph.set_xlabel("Frecuencia [Hz]")

        self.ax_mag.grid(True, which="both", linewidth=0.4, alpha=0.5)
        self.ax_ph.grid(True, which="both", linewidth=0.4, alpha=0.5)

        self.ax_mag.legend(loc="best", fontsize=9)
        self.ax_ph.legend(loc="best", fontsize=9)

        self._shade_band(self.ax_mag)
        self._shade_band(self.ax_ph)

        self.fig.tight_layout(pad=2.0)
        self.canvas.draw_idle()

# ---------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()
