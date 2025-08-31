import pandas as pd
import numpy as np
import os
import subprocess
import sys
import utility as ut
import user_settings_NEW as user
from PyDigitizer.PyDigitizer_script import DigitizerWindow
from PySide6.QtWidgets import QApplication
from PyDigitizer.PyDigitizer_script import DigitizerWindow


# =============================================================
# Instalar dependencias
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
os.system("clear"); print("-> Iniciando el código...\n")
main_watch = ut.myTime.start()

# =============================================================
# Parámetros definidos por el usuario
alto_mm, ancho_mm, fondo_mm = user.boxDims
Vb_m3 = (alto_mm * ancho_mm * fondo_mm) * 1e-9
Qtc_target = 1.1

Qtc_tolerance = 0.001
use_absorbing = True
howManySpeakersToShow = 5

# =============================================================
# Clase evaluadora
class SpeakerEvaluator:
    def __init__(self, Vb_m3):
        self.Vb_m3 = Vb_m3
        self.use_absorbing = use_absorbing
        self.qtc_target = Qtc_target
        self.qmc = self.get_Qmc(Vb_m3, use_absorbing)
        self.use_absorbing = use_absorbing
        self.qtc_target = Qtc_target

    def get_Qmc(self, Vb_m3, use_absorbing):
        Vb_L = Vb_m3 * 1000  # Convertir de m³ a L
        
        if Vb_L < 20:
            return 5 if use_absorbing else 10
        elif 20 <= Vb_L <= 200:
            return 3.5 if use_absorbing else 7.5
        else:
            return 2 if use_absorbing else 5

    def compute_qtc(self, speaker):
        d_m = speaker["d_m"]
        """Diámetro del altavoz en mm."""
        
        Vs_m3 = 0.41 * d_m**4
        """Volumen ocupado por altavoz, en metros cúbicos."""

        Vab_m3 = (self.Vb_m3 - Vs_m3) * 1.25 if self.use_absorbing else self.Vb_m3 - Vs_m3
        if Vab_m3 <= 0:
            return None

        Vas_m3 = speaker["Vas_m3"]
        Qes = speaker["Qes"]
        alpha = Vas_m3 / Vab_m3
        Qec = Qes * np.sqrt(1 + alpha)
        Qtc = (self.qmc * Qec) / (self.qmc + Qec)

        return {
            "Qtc_calc": Qtc,
            "alpha": alpha,
            "Qec": Qec,
            "Vab_m3": Vab_m3,
            "Vs_m3": Vs_m3,
            "Vb": self.Vb_m3,
            "error": abs(Qtc - self.qtc_target)
        }


    def ordenar_por_qtc(self, df, n=5):
        resultados = []
        for _, row in df.iterrows():
            try:
                Vas_m3 = float(row["Vas [L]"]) / 1000
                Qes = float(row["Qes"])
                d_m = float(row["Nominal diameter [mm]"]) / 1e3
            except (ValueError, KeyError):
                continue
            speaker = {
                "Vas_m3": Vas_m3,
                "Qes": Qes,
                "d_m": d_m,
                "Brand": row["Brand"],
                "Model": row["Model"]
            }
            resultado = self.compute_qtc(speaker)
            if resultado:
                resultados.append({**speaker, **resultado})

        return sorted(resultados, key=lambda x: x["error"])[:n]

# =============================================================
# Cargar base de datos y evaluar
df = pd.read_csv("LoudspeakerDatabase_v2.tsv", sep="\t")
evaluador = SpeakerEvaluator(Vb_m3)
mejores = evaluador.ordenar_por_qtc(df, n=howManySpeakersToShow)

# =============================================================
# Mostrar resultados
print(f"\n== Volumen deseado de la caja: {Vb_m3*1000:.2f} L ==")
print(f"== Dimensiones de la caja: {alto_mm/10:.1f} × {ancho_mm/10:.1f} × {fondo_mm/10:.1f} [cm] ==\n")

for altavoz in mejores:
    print(f"{altavoz['Brand']} {altavoz['Model']:20} | Qtc: {altavoz['Qtc_calc']:.3f} | "
          f"error: {altavoz['error']*100:.2f}% | α: {altavoz['alpha']:.3f} | "
          f"Vas_L: {altavoz['Vas_m3']*1000:.2f} L | Vs_L: {altavoz['Vs_m3']*1000:.2f} L | Vab_L: {altavoz['Vab_m3']*1000:.2f} L")

# =============================================================
# Mostrar detalles completos del mejor altavoz
mejor = mejores[0]
fila_original = df[(df["Brand"] == mejor["Brand"]) & (df["Model"] == mejor["Model"])].iloc[0]
print("\n=== Todos los datos del mejor altavoz ===")
for columna, valor in fila_original.items():
    print(f"{columna:25}: {valor}")

print("\n=== Datos computados del mejor altavoz ===")
for clave, valor in mejor.items():
    if clave == "Vas_m3":
        print(f"{'Vas_L':25}: {valor*1000:.2f} L")        # m³ → L
    elif clave == "Vab_m3":
        print(f"{'Vab_L':25}: {valor*1000:.2f} L")        # m³ → L        
    elif clave == "Vb":
        print(f"{'Vb_L':25}: {valor*1000:.2f} L")         # m³ → L
    elif clave == "Vs_m3":
        print(f"{'Vs_L':25}: {valor*1000:.2f} L")         # m³ → L
    elif clave == "error":
        print(f"{clave:25}: {valor*100:.4f} %")           # error absoluto → porcentaje
    elif clave == "Qtc_calc":
        print(f"{clave:25}: {valor:.3f}")                 # sin unidades
    elif clave == "Qec":
        print(f"{clave:25}: {valor:.3f}")                 # sin unidades
    elif clave == "alpha":
        print(f"{clave:25}: {valor:.3f}")                 # sin unidades
    elif clave == "d_mm":
        print(f"{clave:25}: {valor:.0f} mm")              # milímetros
        print(f"{clave:25}: {valor/25.4:.2f} inch")       # pulgadas
    elif clave in ["Brand", "Model"]:
        print(f"{clave:25}: {valor}")                     # texto
    elif clave == "Qes":
        print(f"{clave:25}: {valor:.3f}")                 # sin unidades
    else:
        print(f"{clave:25}: {valor}")                     # por defecto



app = QApplication(sys.argv)
digitizer = DigitizerWindow()
digitizer.show()
print("== Ventana de digitización abierta ==")
sys.exit(app.exec())







# =============================================================
# Detener cronómetro
ut.myTime.stop(main_watch)
