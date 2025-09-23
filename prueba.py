#prueba.py
import pandas as pd
import numpy as np
import os
import subprocess
import sys
import utility as ut
import user_settings_NEW as user
from PyDigitizer.PyDigitizer_script import DigitizerWindow
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QTextEdit, QLabel
from PySide6.QtCore import Qt
import math
import ANSI_colors as colors
from pathlib import Path
from ts_reader import read_ts_xlsx
from acoustics import FRDPlot, mag_limits_from_frd_paths



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

# al inicio del script
PREFIX = "loudspeaker_databases/dibirama_LOUDSPEAKER_DB/"


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
    
    def EdgeDiffraction(twtPos_x_mm:int, twtPos_y_mm:int):
        r_Horizontal_mm = min(abs(twtPos_x_mm), abs(ancho_mm - twtPos_x_mm))
        r_Vertical_mm   = min(abs(twtPos_y_mm), abs(alto_mm - twtPos_y_mm))
        f_b = user.c / (math.pi * min(ancho_mm,alto_mm)*1e-3) # Frecuencia Baffle Step
        
        if False:
            print(f"== Offset del tweeter al borde horizontales: {r_Horizontal_mm/10:.1f} cm ==")
            print(f"== Offset del tweeter al borde vertical: {r_Vertical_mm/10:.1f} cm ==")
            print()
        
        print(f"== Frecuencia Baffle Step: {f_b:.1f} Hz ==")
        print()

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
        
    #ESTO NO ESTA REVISADO, SOLO ES IA    
    def get_tweeter_min_freq_Hz(self, speaker:None) -> float:   
        diameter_m = NotImplemented
        if diameter_m is None or diameter_m <= 0:
            return float("nan")
        return speaker.fs_Hz * 3
    
    def get_woofer_beaming_freq_Hz(self, speaker:None) -> float:   
        diameter_m = NotImplemented
        if diameter_m is None or diameter_m <= 0:
            return float("nan")
        return user.c / (math.pi * diameter_m)
    
    def get_crossover_range_Hz(self, Woofer:None, Tweeter:None) -> tuple[float, float]:
        f_min_XOVER = self.get_woofer_beaming_freq_Hz(Woofer)
        f_max_XOVER = self.get_tweeter_min_freq_Hz(Tweeter)
        
        if math.isnan(f_min_XOVER) or math.isnan(f_max_XOVER):
            return (float("nan"), float("nan"))
        if f_min_XOVER >= f_max_XOVER:
            return (float("nan"), float("nan"))
        return (f_min_XOVER, f_max_XOVER)
    
    



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


    def ordenar_por_qtc(self, df,howManySpeakersToShow=5):
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
            
            # --- DESPUÉS (usa el que esté disponible y continúa si falta) ---
            d_in = row.get("Nominal diameter [″]")
            d_mm = row.get("Nominal diameter [mm]")
            if pd.isna(d_in) and not pd.isna(d_mm):
                d_in = float(d_mm)/25.4
            if pd.isna(d_mm) and not pd.isna(d_in):
                d_mm = float(d_in)*25.4
            if pd.isna(d_in) or pd.isna(d_mm):
                continue
            d_in = float(d_in); d_mm = float(d_mm); d_m = d_mm/1000.0

            
                      
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

        return sorted(resultados, key=lambda x: x["error"])[:howManySpeakersToShow]

# =============================================================
# Cargar base de datos y evaluar
# =============================================================
# Cargar base de datos según fuente seleccionada
# =============================================================
# Cargar base de datos y evaluar
# =============================================================
# Cargar base de datos según fuente seleccionada
if getattr(user, "DATA_SOURCE", "LSDB").upper() == "LSDB":
    df = pd.read_csv("loudspeaker_databases/LoudspeakerDatabase_v2.tsv", sep="\t")
    df["Path_TS"] = ""
    df["Path_FRD"] = ""
else:
    # DIBIRAMA: construir df desde el índice TS↔FRD emitido por pair_data_paths.py
    BASE_DB = Path("loudspeaker_databases/dibirama_LOUDSPEAKER_DB")
    idx_path = None
    xlsx_candidate = Path(getattr(user, "DIBIRAMA_INDEX_XLSX", "indice_TS_FRD.xlsx"))
    csv_candidate  = Path(getattr(user, "DIBIRAMA_INDEX_CSV",  "indice_TS_FRD.csv"))
    if xlsx_candidate.exists():
        idx_path = xlsx_candidate
        idx = pd.read_excel(idx_path)
    elif csv_candidate.exists():
        idx_path = csv_candidate
        idx = pd.read_csv(idx_path)
    else:
        idx = pd.DataFrame(columns=["Modelo_base","Categoria_FRD","Ruta_TS","Ruta_FRD"])

    # Filtrar filas válidas (con TS presente)
    idx = idx[(idx["Ruta_TS"].notna()) & (idx["Ruta_TS"].ne(""))]

    TYPE_MAP = {
        "WOOFER_files":     "Woofer",
        "MIDWOOFER_files":  "Midwoofer",
        "TWEETER_files":    "Tweeter",
        "FULLRANGE_files":  "Fullrange",
    }

    rows = []
    
    def _num(v):
        try:
            if v is None:
                return float("nan")
            s = str(v).strip().replace(",", ".")
            return float(s)
        except Exception:
            return float("nan")

    
    for _, r in idx.iterrows():
        ruta_rel = str(r["Ruta_TS"])
        p_rel = Path(ruta_rel)
        xlsx_abs = p_rel if p_rel.is_absolute() else (BASE_DB / p_rel)
        if not xlsx_abs.exists():
            continue

        # 1) Intento con hoja preferida; 2) fallback a la primera hoja disponible
        sheet_pref = getattr(user, "DIBIRAMA_SHEET", None)
        try:
            ts_SI = read_ts_xlsx(str(xlsx_abs), sheet_name=sheet_pref)
        except Exception:
            try:
                sheets = pd.ExcelFile(xlsx_abs).sheet_names
                ts_SI = read_ts_xlsx(str(xlsx_abs), sheet_name=(sheets[0] if sheets else None))
            except Exception:
                continue

        # --- DESPUÉS (simple, con fallback básico) ---
        Vas_m3 = float(ts_SI.get("Vas_m3") or 0)
        if Vas_m3 <= 0:
            Vas_L = ts_SI.get("Vas_L") or ts_SI.get("Vas [L]")
            Vas_m3 = float(Vas_L)/1000.0 if Vas_L else float("nan")

        Qes = float(ts_SI.get("Qes") or ts_SI.get("Qe") or float("nan"))

        D_m = float(ts_SI.get("D_m") or 0)
        if D_m <= 0:
            D_mm = ts_SI.get("D_mm") or ts_SI.get("Nominal diameter [mm]")
            D_m = float(D_mm)/1000.0 if D_mm else float("nan")

        if not (Vas_m3 > 0 and Qes > 0 and D_m > 0):
            continue

        model = str(r.get("Modelo_base", xlsx_abs.stem)).replace("Parametri", "").replace("parametri", "").strip()
        cat_raw = str(r.get("Categoria_FRD", "") or "")
        tipo = TYPE_MAP.get(cat_raw, "Woofer")
        
        # ya tienes: xlsx_abs
        frd_rel = str(r.get("Ruta_FRD", "") or "")
        p_frd_rel = Path(frd_rel)
        frd_abs = p_frd_rel if p_frd_rel.is_absolute() else (BASE_DB / p_frd_rel)
        path_ts_str  = str(xlsx_abs)                       # existe por construcción
        path_frd_str = str(frd_abs) if frd_abs.exists() else ""
        
        def _to_mH(x):
            try:
                x = float(x)
                return x*1e3 if np.isfinite(x) else np.nan
            except Exception:
                return np.nan

        Le_H_1k  = ts_SI.get("Le_1k_H")   # preferente
        Le_H_gen = ts_SI.get("Le_H")      # respaldo si no hay @1 kHz
        Le_H_10k = ts_SI.get("Le_10k_H")  # secundario

        Le_mH      = _to_mH(Le_H_1k if Le_H_1k is not None else Le_H_gen)
        Le_10k_mH  = _to_mH(Le_H_10k)



        # Mms en gramos según clave, sin heurísticas por magnitud
        Mms_g = np.nan
        if "Mms_g" in ts_SI and pd.notna(ts_SI["Mms_g"]):
            Mms_g = float(ts_SI["Mms_g"])
        elif "Mms [g]" in ts_SI and pd.notna(ts_SI["Mms [g]"]):
            Mms_g = float(ts_SI["Mms [g]"])
        elif "Mms_kg" in ts_SI and pd.notna(ts_SI["Mms_kg"]):
            Mms_g = float(ts_SI["Mms_kg"]) * 1000.0
            
        """
        Le_mH      = _to_mH(ts_SI.get("Le_1k_H", ts_SI.get("Le_H")))
        Le_10k_mH  = _to_mH(ts_SI.get("Le_10k_H"))
        Cms_uN     = (float(ts_SI["Cms_m_per_N"])*1e6) if ("Cms_m_per_N" in ts_SI and np.isfinite(ts_SI["Cms_m_per_N"])) else np.nan
        Mms_g      = (float(ts_SI["Mms_kg"])*1000.0) if ("Mms_kg" in ts_SI and np.isfinite(ts_SI["Mms_kg"])) else (ts_SI.get("Mms_g") if np.isfinite(ts_SI.get("Mms_g", np.nan)) else np.nan)
        VC_d_mm    = (float(ts_SI["VC_d_m"])*1e3) if ("VC_d_m" in ts_SI and np.isfinite(ts_SI["VC_d_m"])) else np.nan
        Xmax_mm    = (float(ts_SI["Xmax_m"])*1e3) if ("Xmax_m" in ts_SI and np.isfinite(ts_SI["Xmax_m"])) else np.nan
        n0_pct     = (float(ts_SI["n0_ratio"])*100.0) if ("n0_ratio" in ts_SI and np.isfinite(ts_SI["n0_ratio"])) else np.nan

        """
        
        # Derivados simples y alias (mínimo necesario)
        Cms_uN = (
            float(ts_SI["Cms_m_per_N"])*1e6
            if ("Cms_m_per_N" in ts_SI and pd.notna(ts_SI["Cms_m_per_N"]))
            else _num(ts_SI.get("Cms_uN") or ts_SI.get("Cms [um/N]") or ts_SI.get("Cms_umN"))
        )
        VC_d_mm    = float(ts_SI["VC_d_m"])*1e3 if ("VC_d_m" in ts_SI and pd.notna(ts_SI["VC_d_m"])) else np.nan
        Xmax_mm    = float(ts_SI["Xmax_m"])*1e3 if ("Xmax_m" in ts_SI and pd.notna(ts_SI["Xmax_m"])) else np.nan
        n0_percent = float(ts_SI["n0_ratio"])*100.0 if ("n0_ratio" in ts_SI and pd.notna(ts_SI["n0_ratio"])) else np.nan

        SPL_1W1m_dB = _num(ts_SI.get("SPL_1W1m_dB") or ts_SI.get("Spl (1W/1m)"))
        SPL_2V83_dB = _num(ts_SI.get("SPL_2V83_dB") or ts_SI.get("Spl (2,83V/1m)"))

        P_nom_W = _num(ts_SI.get("P_nom_W") or ts_SI.get("P. nom"))
        P_max_W = _num(ts_SI.get("P_max_W") or ts_SI.get("P. max"))
        Power_W = P_nom_W   # alias legacy
        Pmax_W  = P_max_W   # alias legacy


        rows.append({
            # básicos que ya tenías
            "Brand": "-",
            "Model": model,
            "Type":  tipo,
            "Vas [L]": Vas_m3 * 1000.0,
            "Qes": Qes,
            "Nominal diameter [mm]": D_m * 1000.0,
            "Nominal diameter [″]":  D_m * 39.37007874015748,
            "URL": "",
            "Path_TS":  path_ts_str,
            "Path_FRD": path_frd_str,

            # —— TS esperados por ThieleSmall (alias simples) ——
            "Fs_Hz":  _num(ts_SI.get("Fs_Hz") or ts_SI.get("Fs") or ts_SI.get("Fs [Hz]")),
            "Qms":    _num(ts_SI.get("Qms")),
            "Qts":    _num(ts_SI.get("Qts")),
            "Re_ohm": _num(ts_SI.get("Re_Ohm") or ts_SI.get("Re") or ts_SI.get("Re [Ohm]")),
            "Z_ohm":  _num(ts_SI.get("Z_Ohm") or ts_SI.get("Z") or ts_SI.get("Z [Ohm]")),

            "Le_mH":     Le_mH,
            "Le_10k_mH": Le_10k_mH,


            # Sd (convierte si viene en m² o cm²)
            "Sd_cm2": (
                _num(ts_SI.get("Sd_cm2") or ts_SI.get("Sd [cm^2]"))
                if _num(ts_SI.get("Sd_cm2") or ts_SI.get("Sd [cm^2]")) > 0
                else (_num(ts_SI.get("Sd_m2") or ts_SI.get("Sd [m^2]")) * 1e4)
            ),

            "Mms_g":  Mms_g,
            
            
            #"Mmd_g":  _num(ts_SI.get("Mmd_g") or ts_SI.get("Mmd [g]")),
            #"Cms_uN": _num(ts_SI.get("Cms_uN") or ts_SI.get("Cms [um/N]") or ts_SI.get("Cms_umN")),
            "Cms_uN": Cms_uN,
            "Vas_L":  Vas_m3 * 1000.0,
            "Rms":    _num(ts_SI.get("Rms") or ts_SI.get("Rms [N·s/m]")),

            # campos adicionales comunes (opcionales)
            "SPL_dB": _num(ts_SI.get("Spl (1W/1m)") or ts_SI.get("Spl (2,83V/1m)") or ts_SI.get("SPL_dB")),
            "Power_W": _num(ts_SI.get("P. nom") or ts_SI.get("P_nom_W")),
            "Pmax_W":  _num(ts_SI.get("P. max") or ts_SI.get("P_max_W")),

            # duplicados con nombres que tu clase espera (por si luego haces merge por nombre)
            "Diameter_inch": D_m * 39.37007874015748,
            "Diameter_mm":   D_m * 1000.0,
            "VC_d_mm":      VC_d_mm,
            "Xmax_mm":      Xmax_mm,
            "n0_percent":   n0_percent,
            "SPL_1W1m_dB":  SPL_1W1m_dB,
            "SPL_2V83_dB":  SPL_2V83_dB,
            "P_nom_W":      P_nom_W,
            "P_max_W":      P_max_W,
            "EBP_Hz":       ts_SI.get("EBP_Hz"),
            #"FS_over_Qts":  ts_SI.get("FS_over_Qts"),
            "Bl_Tm":        ts_SI.get("Bl_Tm"),

            

        })

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Brand","Model","Type","Vas [L]","Qes","Nominal diameter [″]","URL"]
    )


evaluador = SpeakerEvaluator(Vb_m3)
mejores = evaluador.ordenar_por_qtc(df)


# --- reemplazo de la función ---
def print_filter_summary():
    if df is None or df.empty:
        print("== No hay altavoces válidos tras la selección de fuente de datos.\n")
        return pd.DataFrame(), 0

    source_label = (user.LSDB_CONTACT if getattr(user, "DATA_SOURCE", "LSDB").upper() == "LSDB"
                    else "Dibirama (índice TS↔FRD)")

    if filter_LowDriver_by_Type:
        tipos_lower = [t.lower() for t in filter_LowDriver_by_Type]
        total = len(df)
        mask_types = df["Type"].fillna("").str.lower().isin(tipos_lower)
        total_tipo = int(mask_types.sum())

        if len(filter_LowDriver_by_Type) > 1:
            cats = ", ".join(filter_LowDriver_by_Type[:-1]) + " y " + filter_LowDriver_by_Type[-1]
        else:
            cats = filter_LowDriver_by_Type[0]

        print("== " +
              f"Fueron filtrados {total_tipo} de {total} altavoces de las categorías {cats} " +
              f"desde la base de datos {source_label}.")

        df_types = df.loc[mask_types]
        dmax_mm = max(0, min(ancho_mm, alto_mm) - 2*user.margin_baffle_mm)

        if "Nominal diameter [mm]" in df_types.columns:
            diam_mm_series = pd.to_numeric(df_types["Nominal diameter [mm]"], errors="coerce")
        else:
            diam_in_series = pd.to_numeric(
                df_types.get("Nominal diameter [″]", pd.Series(index=df_types.index)),
                errors="coerce"
            )
            diam_mm_series = diam_in_series * 25.4

        fit_mask = diam_mm_series <= dmax_mm
        filtrados_dim = int(fit_mask.sum())
        df_final = df_types.loc[fit_mask]

        print("== " +
              f"Fueron filtrados {filtrados_dim} de {total_tipo} altavoces podrían caber adecuadamente en su caja.\n")

        return df_final, filtrados_dim

    return df, len(df)






# =============================================================
# Mostrar resultados
print(f"== Dimensiones de la caja elegida: {alto_mm/10:.1f} × {ancho_mm/10:.1f} × {fondo_mm/10:.1f} [cm] ==")
print(f"== Posición del tweeter desde la esquina superior izquierda: {user.tweeterPosition_mm[0]/10:.1f} × {user.tweeterPosition_mm[1]/10:.1f} [cm] ==")
print(f"== Volumen resultante de la caja elegida: {Vb_m3*1000:.2f} L ==\n")

SpeakerEvaluator.EdgeDiffraction(user.tweeterPosition_mm[0], user.tweeterPosition_mm[1])

#print_filter_summary()


if show_Qtc_sorting_results:=False:
    howManySpeakersToShow = 3
    header = (
        f"{'Modelo':{25}} "
        f"{'Tipo':{12}} "
        f"{'Qtc':>3} {'err%':>7} {'α':>3} {'Vas[L]':>11} {'Vs[L]':>7} "
        f"{'Vab[L]':>7} {'Vb_real[L]':>11} {'f_null[Hz]':>1} Link"
    )
    
    link_sheet_margin = 15
    print("-" * (len(header) + link_sheet_margin))
    print(colors.BLUE, header, colors.RESET)
    print("-" * (len(header) + link_sheet_margin))
    print()
    for a in mejores:
        vb_real = (a['Vab_m3'] + a['Vs_m3']) * 1000
        model = f"{a['Brand']} {a['Model']}"
        tipo  = f"{a['Type']} ({a['d_in']:.0f}\")"
        link = osc8("↗", a["URL"]) if a.get("URL") else ""

        print(
            f"{model:<{25}.{25}} "
            f"{tipo:<{12}.{12}} "
            f"{a['Qtc_calc']:4.3f} {a['error']*100:5.2f} {a['alpha']:7.3f} "
            f"{a['Vas_m3']*1000:6.2f} {a['Vs_m3']*1000:8.2f} {a['Vab_m3']*1000:7.2f} "
            f"{vb_real:7.2f} {round(a['f_null_hz']):9.0f}       {a.get('URL',''):>30}"
        )
    print("-" * (len(header) + link_sheet_margin))




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


class SpeakerListWindow(QWidget):
    def __init__(self, speakers, filtrados_dim):
        super().__init__()
        self.setWindowTitle("Altavoces Seleccionables")
        self.layout = QVBoxLayout(self)
        # después de: self.layout = QVBoxLayout(self)
        speakers = [
            s for s in speakers
            if (str(s.get("Path_TS","")).strip() and Path(str(s.get("Path_TS"))).exists())
            and (str(s.get("Path_FRD","")).strip() and Path(str(s.get("Path_FRD"))).exists())
        ]

        self.speakers = speakers


        self.count_label = QLabel(f"Altavoces que cumplen parámetros ajustados: {len(self.speakers)}")
        self.layout.addWidget(self.count_label)

        self.label = QLabel("Selecciona un altavoz:")
        self.layout.addWidget(self.label)

        self.list_widget = QListWidget()
        for spk in self.speakers:
            brand = spk.get("Brand", "-")
            model = spk.get("Model", "-")

            z = spk.get("Z_ohm", None)
            z_str = "" if (z is None or pd.isna(z) or float(z) <= 0) else f"{int(float(z))} Ω"

            di = spk.get("Nominal diameter [″]", None)
            di_str = "" if (di is None or pd.isna(di) or float(di) <= 0) else f"({float(di):.1f}\")"

            label = " ".join(p for p in [f"{model}", z_str, di_str] if p)
            self.list_widget.addItem(label)
        self.layout.addWidget(self.list_widget)


        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.layout.addWidget(self.details)

        self.list_widget.currentRowChanged.connect(self.show_details)
        #self.speakers = speakers
        
        self.frd_plot = FRDPlot(self)
        self.layout.addWidget(self.frd_plot)


    # dentro de class SpeakerListWindow(QWidget):
    def set_always_on_top(self, enabled=True):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.show()  # reaplica flags

    def report_geometry(self, enabled:bool=True):
        if not enabled:
            return
        scr = (self.screen().availableGeometry()
            if self.screen() else QApplication.primaryScreen().availableGeometry())
        geo = self.geometry()
        frame = self.frameGeometry()
        print(f"geom: {geo.width()}x{geo.height()} @ ({geo.x()},{geo.y()})")
        print(f"frame: {frame.width()}x{frame.height()} @ ({frame.x()},{frame.y()})")
        print(f"screen: {scr.width()}x{scr.height()} @ ({scr.x()},{scr.y()})")

    def resizeEvent(self, e):
        self.report_geometry(False)
        super().resizeEvent(e)

    def moveEvent(self, e):
        self.report_geometry(False)
        super().moveEvent(e)

    
    
    def show_details(self, idx):
        if idx < 0 or idx >= len(self.speakers):
            self.details.setText("")
            return

        spk = self.speakers[idx]

        def fnum(key, default=np.nan):
            v = spk.get(key, default)
            try:
                return float(v)
            except Exception:
                return default

        # Re (1 decimal)
        re_val = fnum("Re_ohm")
        re_disp = f"{re_val:.1f} Ω" if np.isfinite(re_val) else "—"

        # Z nominal = potencia de 2 >= ceil(Re)
        z_disp = "—"
        if np.isfinite(re_val) and re_val > 0:
            target = math.ceil(re_val)
            z_nom = 1
            while z_nom < target:
                z_nom <<= 1
            z_disp = f"{z_nom} Ω"

        # Diámetro en pulgadas a pasos de 0.5
        d_in = fnum("Nominal diameter [″]")
        diam_disp = f'{(round(d_in * 2) / 2):.1f}"' if np.isfinite(d_in) else "—"

        # Sd (1 decimal)
        sd = fnum("Sd_cm2")
        sd_disp = f"{sd:.1f} cm²" if np.isfinite(sd) else "—"

        # Fs (1 decimal)
        fs = fnum("Fs_Hz")
        fs_disp = f"{fs:.1f} Hz" if np.isfinite(fs) else "—"

        # Q's (2 decimales)
        qms = fnum("Qms"); qes = fnum("Qes"); qts = fnum("Qts")
        qms_disp = f"{qms:.2f}" if np.isfinite(qms) else "—"
        qes_disp = f"{qes:.2f}" if np.isfinite(qes) else "—"
        qts_disp = f"{qts:.2f}" if np.isfinite(qts) else "—"

        # Rms (2 decimales)
        rms = fnum("Rms")
        rms_disp = f"{rms:.2f}" if np.isfinite(rms) else "—"

        # Vas (2 decimales) ya en L
        vas = fnum("Vas [L]")
        vas_disp = f"{vas:.2f} L" if np.isfinite(vas) else "—"

        # Cms (1 decimal, uN)
        cms = fnum("Cms_uN")
        cms_disp = f"{cms:.1f} uN" if np.isfinite(cms) else "—"

        # Mms (2 decimales)
        mms = fnum("Mms_g")
        mms_disp = f"{mms:.2f} g" if np.isfinite(mms) else "—"

        # SPL 1W/1m (1 decimal; fallback SPL_dB)
        spl = fnum("SPL_1W1m_dB")
        if not np.isfinite(spl):
            spl = fnum("SPL_dB")
        spl_disp = f"{spl:.1f} dB" if np.isfinite(spl) else "—"

        # Le (2 decimales, mH)
        le = fnum("Le_mH")
        le_disp = f"{le:.2f} mH" if np.isfinite(le) else "—"

        # Potencias (1 decimal)
        p_nom = fnum("Power_W")
        p_max = fnum("Pmax_W")
        p_nom_disp = f"{p_nom:.1f} W" if np.isfinite(p_nom) else "—"
        p_max_disp = f"{p_max:.1f} W" if np.isfinite(p_max) else "—"

        # Rutas acortadas solo para mostrar
        def trim_path(k):
            s_raw = str(spk.get(k, "") or "")
            if not s_raw:
                return ""
            s = s_raw.replace("\\", "/")
            pos = s.lower().find(PREFIX.lower())
            return s[pos+len(PREFIX):] if pos != -1 else s

        lines = [
            f"Model: {spk.get('Model')}",
            f"{diam_disp} - {z_disp}",            
            "",
            f"Re: {re_disp}",
            f"Sd: {sd_disp}",
            f"fs: {fs_disp}",
            f"Qms: {qms_disp}",
            f"Qes: {qes_disp}",
            f"Qts: {qts_disp}",
            f"Rms: {rms_disp}",
            f"Vas: {vas_disp}",
            f"Cms: {cms_disp}",
            f"Mms: {mms_disp}",
            f"Le: {le_disp}",
            "",
            f"Sensitivity (1W@1m): {spl_disp} SPL",
            f"Power: {p_nom_disp}",
            f"Pmax: {p_max_disp}",
            "",
            #f"URL: {spk.get('URL','')}",
            f"Path_TS: {trim_path('Path_TS')}",
            f"Path_FRD: {trim_path('Path_FRD')}",
        ]
        self.details.setPlainText("\n".join(lines))
        frd_path = str(spk.get("Path_FRD", "")).strip()
        self.frd_plot.plot_frd(frd_path)




        # lines = []
        # for k in main_keys:
        #     if k in spk:
        #         lines.append(f"{k}: {spk[k]}")        
        # self.details.setPlainText("\n".join(lines))
        
        # for k in ("Path_TS", "Path_FRD"):
        #     s_raw = str(spk.get(k, ""))
        #     if not s_raw:
        #         continue
        #     s = s_raw.replace("\\", "/")
        #     pos = s.lower().find(PREFIX.lower())
        #     shown = s[pos+len(PREFIX):] if pos != -1 else s
        #     lines.append(f"{k}: {shown}")


        
    # en SpeakerListWindow
    def snap_right_fullheight(self):
        scr = QApplication.primaryScreen().availableGeometry()
        self.resize(self.width(), scr.height())           # conserva ancho actual, alto = máximo disponible
        self.move(scr.x() + scr.width() - self.width(),  # completamente a la derecha
                scr.y())                                # arriba





# Para mostrar la ventana con los altavoces resultantes:
# --- uso en la ventana (corrige los argumentos del constructor) ---
df_filtrado, filtrados_dim = print_filter_summary()
# === Exportar a CSV rápido para depuración ===
df_filtrado.to_csv("debug_altavoces.csv", index=False)
print("== Se exportó df_filtrado a debug_altavoces.csv ==")






if visual_check_image := True:
    app = QApplication(sys.argv)
    window = SpeakerListWindow(df_filtrado.to_dict(orient="records"), filtrados_dim)

    # calcular y-lims usando solo los FRD visibles y existentes
    frd_paths_visibles = [
        str(s.get("Path_FRD")) for s in window.speakers
        if s.get("Path_FRD") and Path(str(s.get("Path_FRD"))).exists()
    ]
    ylims = mag_limits_from_frd_paths(frd_paths_visibles)
    if ylims:
        window.frd_plot.set_fixed_ylim(*ylims)

    window.resize(335, 400)
    window.snap_right_fullheight()     # fija posición y alto
    window.set_always_on_top(True)     # stay on top
    window.report_geometry(False)      # reporta geometría inicial
    window.show()
    print(f"\n{colors.GREEN}== Ventana de altavoces abierta... =={colors.RESET} \n")
    sys.exit(app.exec())



# =============================================================
# Detener cronómetro
ut.myTime.stop(main_watch)
