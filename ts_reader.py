# === [AÑADIR] Conversión de unidades TS desde Excel ==========================
import re
import pandas as pd

_UN_ALIASES = {
    "hz":   "Hz", 
    "khz":  "kHz", 
    "ohm":  "Ω", 
    "Ω":    "Ω", 
    "ohms": "Ω",
    "l":    "L", 
    "ml":   "mL", 
    "m3":   "m³", 
    "m^3":  "m³",
    "mm":   "mm", 
    "cm":   "cm", 
    "m":    "m",
    "mm2":  "mm²", 
    "cm2":  "cm²", 
    "m2":   "m²",
    "mh":   "mH", 
    "uh":   "µH", 
    "µh":   "µH", 
    "h":    "H",
    "g":    "g", 
    "kg":   "kg",
    "tm":   "Tm",
    "mm/n": "mm/N", 
    "m/n":  "m/N",
    "dm3":  "L",  
    "dm^3": "L",
    "dm³":  "L",
    "kg/s": "kg/s",
    "kgs/s":"kg/s",
    "um":   "µm",
    "μm":   "µm",
    "um/n": "µm/N",
    "µm/n": "µm/N",
    "cm/n": "cm/N"    
}

def _norm_unit(u: str) -> str:
    if not u: return ""
    u = str(u).strip()
    u = re.sub(r"\s+", "", u)
    key = u.lower()
    return _UN_ALIASES.get(key, u)

def _ensure_float(x):
    try:
        if isinstance(x, str):
            x = x.replace(",", ".")
        return float(x)
    except Exception:
        return float("nan")

def _to_SI(key: str, val, unit: str) -> float:
    v = _ensure_float(val)
    u = _norm_unit(unit)

    if u == "kHz":  return v * 1e3
    if u == "Hz":   return v
    if u == "mH":   return v * 1e-3
    if u == "µH":   return v * 1e-6
    if u == "H":    return v
    if u == "Ω":    return v
    if u == "g":    return v * 1e-3
    if u == "kg":   return v
    if u == "kg/s": return v
    if u == "L":    return v * 1e-3
    if u == "mL":   return v * 1e-6
    if u == "m³":   return v
    if u == "mm":   return v * 1e-3
    if u == "µm":   return v * 1e-6
    if u == "cm":   return v * 1e-2
    if u == "mm²":  return v * 1e-6
    if u == "cm²":  return v * 1e-4
    if u == "Tm":   return v
    if u in ("mm/N", "m/N", "cm/N", "µm/N"):
        return {
            "m/N":   v,
            "cm/N":  v * 1e-2,
            "mm/N":  v * 1e-3,
            "µm/N":  v * 1e-6,
        }[u]
    if u in ("dB", "W", ""):  return v
    if u == "%":  return v / 100.0
    return v


def _canon_key(raw: str) -> str:
    s = str(raw).strip()
    sl = s.lower().replace("(", "").replace(")", "")
    if "/" in sl or "\\" in sl:
        return raw
    if re.fullmatch(r"(fs|f0)", sl): return "Fs_Hz"
    if sl.startswith("re") or "dc resistance" in sl: return "Re_Ohm"
    if re.fullmatch(r"qes", sl): return "Qes"
    if re.fullmatch(r"qms", sl): return "Qms"
    if re.fullmatch(r"qts", sl): return "Qts"
    if "vas" in sl: return "Vas_m3"
    if re.fullmatch(r"sd", sl): return "Sd_m2"
    if re.fullmatch(r"bl", sl): return "Bl_Tm"
    if re.fullmatch(r"(x-?max|xmax)", sl): return "Xmax_m"
    if re.fullmatch(r"(n0|η0|eta0)", sl): return "n0_ratio"
    if "spl" in sl and "1w" in sl: return "SPL_1W1m_dB"
    if "spl" in sl and ("2,83" in sl or "2.83" in sl): return "SPL_2V83_dB"
    if sl.startswith("le"):
        if "10" in sl and "khz" in sl: return "Le_10k_H"
        if "1" in sl and "khz" in sl:  return "Le_1k_H"
        return "Le_H"
    if "diameter" in sl or "nominal diameter" in sl or "diametro" in sl: return "D_m"
    if "bobina" in sl or "voice coil" in sl: return "VC_d_m"
    if re.fullmatch(r"mms", sl): return "Mms_kg"
    if re.fullmatch(r"cms", sl): return "Cms_m_per_N"
    if re.fullmatch(r"ebp", sl): return "EBP_Hz"
    #if "fs/qts" in sl: return "FS_over_Qts"
    if re.fullmatch(r"p\.?\s*nom", sl): return "P_nom_W"
    if re.fullmatch(r"p\.?\s*max\*?", sl): return "P_max_W"
    if re.fullmatch(r"z", sl) or "impedance" in sl: return "Z_Ohm"
    return raw


# DESPUÉS
def read_ts_xlsx(xlsx_path: str, sheet_name=None) -> dict:
    xls = pd.ExcelFile(xlsx_path)
    sheets = xls.sheet_names
    if isinstance(sheet_name, int) and 0 <= sheet_name < len(sheets):
        chosen = sheets[sheet_name]
    elif isinstance(sheet_name, str) and sheet_name in sheets:
        chosen = sheet_name
    else:
        chosen = sheets[0]
    sh = pd.read_excel(xls, sheet_name=chosen, header=None)

    def _detect_cols(sh):
        # busca la fila que contiene los rótulos; si no, usa posiciones por defecto
        for r in range(min(10, len(sh))):
            row = sh.iloc[r].astype(str).str.strip().str.lower().tolist()
            if ("dichiarati" in row) and ("misurati" in row):
                decl_v = row.index("dichiarati")
                misu_v = row.index("misurati")
                return r, decl_v, decl_v + 1, misu_v, misu_v + 1
        # Fallback por posición (B=1, C=2, E=4, F=5). Nunca uses "Scarto".
        # return -1, 1, 2, 4, 5


    out = {}
    for _, row in sh.iterrows():
        # Nombre en columna B
        if row.shape[0] <= 1 or pd.isna(row.iloc[1]):
            continue
        name = str(row.iloc[1]).strip()

        # Medido: G (valor) y H (unidad)
        # Medido: G (valor) y H (unidad)
        mis_val  = row.iloc[6] if row.shape[0] > 6 else None
        mis_unit = row.iloc[7] if row.shape[0] > 7 else ""

        # Declarado: C (valor) y D (unidad)
        dec_val  = row.iloc[2] if row.shape[0] > 2 else None
        dec_unit = row.iloc[3] if row.shape[0] > 3 else ""

        # Prioriza "Misurati" solo si NO es NaN ni string vacío; si no, usa "Dichiarati".
        use_mis = pd.notna(mis_val) and str(mis_val).strip() != ""
        val, unit = (mis_val, mis_unit) if use_mis else (dec_val, dec_unit)
        unit = "" if pd.isna(unit) else unit

        key = _canon_key(name)
        out[key] = _to_SI(key, val, unit)



    # Derivaciones mínimas
    if "Qts" not in out and "Qes" in out and "Qms" in out:
        try:
            Qes, Qms = float(out["Qes"]), float(out["Qms"])
            out["Qts"] = (Qes*Qms)/(Qes+Qms)
        except Exception:
            pass

    if "D_m" not in out and "Sd_m2" in out:
        try:
            import math
            out["D_m"] = 2.0 * math.sqrt(float(out["Sd_m2"]) / math.pi)
        except Exception:
            pass

    return out

# ============================================================================
