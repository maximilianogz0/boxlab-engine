import pandas as pd
import numpy as np
import os
import subprocess
import sys
import utility as ut
import user_settings_NEW as user
from PyDigitizer.PyDigitizer_script import DigitizerWindow
from PySide6.QtWidgets import QApplication
import math
import ANSI_colors as colors

# =============================================================
# Instalar dependencias
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
os.system("clear"); print(f"{colors.GREEN}-> Iniciando el código...{colors.RESET} \n")
main_watch = ut.myTime.start()

# =============================================================
# Parámetros definidos por el usuario
alto_mm, ancho_mm, fondo_mm = user.boxDims
filter_LowDriver_by_Type = user.filter_LowDriver_by_Type
Vb_m3 = (alto_mm * ancho_mm * fondo_mm) * 1e-9
Qtc_target = 1/math.sqrt(2) # Ajuste B2
Qtc_tolerance = 0.001
use_absorbing = False
howManySpeakersToShow = 10

# =============================================================

# Utilidades
def resolve_type(row: dict, default: str = "-undefined-") -> str:
    return (str(row.get("Type", "")).strip() or default)

# Alias para mantener compatibilidad con llamadas existentes
def normalize_type_field(row: dict) -> str:
    return resolve_type(row)
filter_LowDriver_by_Type = user.filter_LowDriver_by_Type

def osc8(text, url): 
    return f"\033]8;;{url}\a{text}\033]8;;\a"

#@staticmethod
def norm_url(u):
    u = str(u or "")
    return u if u.startswith(("http://", "https://")) else (f"https://{u}" if u else "")


# Clase evaluadora
class SpeakerEvaluator:
    def __init__(self, Vb_m3):
        self.Vb_m3 = Vb_m3
        self.use_absorbing = use_absorbing
        self.qtc_target = Qtc_target
        self.qmc = self.get_Qmc(Vb_m3, use_absorbing)
        self.use_absorbing = use_absorbing
        self.qtc_target = Qtc_target
    

    @staticmethod    
    def first_null_threshold_hz(diameter_m: float) -> float:
        """
        Frecuencia umbral (Hz) del primer nulo de directividad para un pistón circular:
        f = (XI1 * c) / (pi * D), con XI1 = primera raíz positiva de J1.
        """
        XI1 = 3.8317059702075125
        if diameter_m is None or diameter_m <= 0:
            return float("nan")
        return XI1 * user.c / (math.pi * diameter_m)
        
        

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
        f_null = self.first_null_threshold_hz(d_m)

        return {
            "Qtc_calc": Qtc,
            "alpha": alpha,
            "Qec": Qec,
            "Vab_m3": Vab_m3,
            "Vs_m3": Vs_m3,
            "Vb": self.Vb_m3,
            "error": abs(Qtc - self.qtc_target),
            "f_null_hz": f_null
        }


    def ordenar_por_qtc(self, df, n=5):
        resultados = []
        for _, row in df.iterrows():
            try:
                Vas_m3 = float(row["Vas [L]"]) / 1000
                Qes = float(row["Qes"])
                #d_m = float(row["Nominal diameter [mm]"]) / 1e3
            except (ValueError, KeyError):
                continue
            
            #d_mm = pd.to_numeric(row.get("Nominal diameter [mm]"), errors="coerce")
            #d_in = pd.to_numeric(row.get("Nominal diameter [″]") or row.get("Nominal diameter [in]"), errors="coerce")

            
            # Tipo normalizado
            spk_type = normalize_type_field(row)

            # Filtro por tipo si corresponde
            if filter_LowDriver_by_Type and len(filter_LowDriver_by_Type) > 0:
                # comparación case-insensitive
                if spk_type.lower() not in {t.lower() for t in filter_LowDriver_by_Type}:
                    continue
            
            d_in = float(row["Nominal diameter [″]"])
            d_mm = d_in * 25.4
            d_m  = d_mm / 1000.0
            dmax_mm = min(ancho_mm, alto_mm) - 2*user.margin_baffle_mm
            if d_mm > dmax_mm:
                continue

            
                      
            # Filtro por dimensiones de la cara frontal (solo entre los ya filtrados por tipo)
            #if d_m * 1000 > max(0, min(ancho_mm, alto_mm) - 2*user.margin_baffle_mm):
            #    continue

            
            speaker = {
                "Vas_m3": Vas_m3,
                "Qes": Qes,
                "d_m": d_m,
                "Brand": row["Brand"],
                "Model": row["Model"],
                "Type": spk_type,
                "d_mm": d_mm,
                "d_in": float(row["Nominal diameter [″]"]),
                #"URL": row["URL"],
                "URL": norm_url(row["URL"])



            }
            resultado = self.compute_qtc(speaker)
            if resultado:
                resultados.append({**speaker, **resultado})

        return sorted(resultados, key=lambda x: x["error"])[:n]

# =============================================================
# Cargar base de datos y evaluar
df = pd.read_csv("loudspeaker_databases/LoudspeakerDatabase_v2.tsv", sep="\t")
evaluador = SpeakerEvaluator(Vb_m3)
mejores = evaluador.ordenar_por_qtc(df, n=howManySpeakersToShow)

def print_filter_summary():
    if filter_LowDriver_by_Type:
        # Filtro 1: por categorías
        tipos_lower = [t.lower() for t in filter_LowDriver_by_Type]
        mask_types = df["Type"].fillna("").str.lower().isin(tipos_lower)
        total = len(df)
        total_tipo = int(mask_types.sum())

        # Armado de la lista de categorías en español
        if len(filter_LowDriver_by_Type) > 1:
            cats = ", ".join(filter_LowDriver_by_Type[:-1]) + " y " + filter_LowDriver_by_Type[-1]
        else:
            cats = filter_LowDriver_by_Type[0]

        print("== " +
              f"Fueron filtrados {total_tipo} de {total} altavoces de las categorías {cats} " +
              f"desde la base de datos {user.LSDB_CONTACT}.")

        # Filtro 2: entre los resultantes, quepa en la cara frontal
        df_types = df.loc[mask_types]
        dmax_mm = min(ancho_mm, alto_mm) - 2*user.margin_baffle_mm
        fit_mask = df_types["Nominal diameter [mm]"] <= dmax_mm

        filtrados_dim = int(fit_mask.sum())
        print("== " +
              f"De los resultantes, {filtrados_dim} altavoces podrían caber adecuadamente en su caja.\n")



# =============================================================
# Mostrar resultados
print(f"== Dimensiones de la caja elegida: {alto_mm/10:.1f} × {ancho_mm/10:.1f} × {fondo_mm/10:.1f} [cm] ==")
print(f"== Volumen resultante de la caja elegida: {Vb_m3*1000:.2f} L ==\n")
print_filter_summary()

# Anchos fijos coherentes
MODEL_W = 25
TYPE_W  = 12
header = (
    f"{'Modelo':{MODEL_W}} "
    f"{'Tipo':{TYPE_W}} "
    f"{'Qtc':>3} {'err%':>7} {'α':>3} {'Vas[L]':>11} {'Vs[L]':>7} "
    f"{'Vab[L]':>7} {'Vb_real[L]':>11} {'f_null[Hz]':>1} Link"
)

print("-" * len(header))
print(colors.BLUE, header, colors.RESET)
print("-" * len(header))

for a in mejores:
    vb_real = (a['Vab_m3'] + a['Vs_m3']) * 1000
    model = f"{a['Brand']} {a['Model']}"
    tipo  = f"{a['Type']} ({a['d_in']:.0f}\")"
    link = osc8("↗", a["URL"]) if a.get("URL") else ""

    print(
        f"{model:<{MODEL_W}.{MODEL_W}} "
        f"{tipo:<{TYPE_W}.{TYPE_W}} "
        f"{a['Qtc_calc']:4.3f} {a['error']*100:5.2f} {a['alpha']:7.3f} "
        f"{a['Vas_m3']*1000:6.2f} {a['Vs_m3']*1000:7.2f} {a['Vab_m3']*1000:7.2f} "
        f"{vb_real:7.2f} {round(a['f_null_hz']):9.0f}       {a.get('URL',''):>30}"
    )





# =============================================================
# Mostrar detalles completos del mejor altavoz
if show_BestSpeakerDetails := False:
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
        elif clave in ["Brand", "Model", "Type"]:
            print(f"{clave:25}: {valor}")                     # texto
        elif clave == "Qes":
            print(f"{clave:25}: {valor:.3f}")                 # sin unidades
        else:
            print(f"{clave:25}: {valor}")                     # por defecto

if run_Digitizer:= False:
    app = QApplication(sys.argv)
    digitizer = DigitizerWindow()
    digitizer.show()
    print("== Ventana de digitización abierta ==")
    sys.exit(app.exec())

if run_Tesseract_OCR := False:
    from ts_ocr_dats import extract_ts_from_image, export_dats_txt, export_vituixcad_driver, process_image_to_files
    # 1) Obtener dict normalizado
    ts = extract_ts_from_image("loudspeaker_databases/dibirama_LOUDSPEAKER_DB/FULLRANGE_files/audax_13lb25al/audax_13lb25al_par.jpg")  # {'Fs_Hz': (36.9,'Hz'), 'Re_Ohm': (6.3,'Ohm'), ...}
    # 2) Escribir TXT estilo DATS
    export_dats_txt(ts, "mi_driver.dats", meta={"Brand":"Dayton","Model":"RS180-8"})
    # 3) Escribir driver VituixCAD
    # export_vituixcad_driver(ts, "mi_driver.vituix.txt", meta={"Brand":"SB","Model":"SB17NRX2C30-8"})

# =============================================================
# Detener cronómetro
ut.myTime.stop(main_watch)
