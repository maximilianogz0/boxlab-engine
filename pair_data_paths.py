# pair_data_paths.py
# Python 3.10+
from __future__ import annotations
import re, unicodedata, shutil
from pathlib import Path
import pandas as pd
import argparse, random
import sys
import os
import utility as ut
import ANSI_colors as colors

os.system("clear"); print(f"{colors.GREEN}-> Iniciando el código...{colors.RESET} \n")
main_watch = ut.myTime.start()

# === Configuración ===
BASE_DB = Path("loudspeaker_databases/dibirama_LOUDSPEAKER_DB")

CARPETA_TS = BASE_DB / "TS_Params"  # Excel por modelo
FRD_ROOTS = [
    BASE_DB / "FULLRANGE_files",
    BASE_DB / "MIDWOOFER_files",
    BASE_DB / "WOOFER_files",
    BASE_DB / "TWEETER_files",
]  # se recorren todas

def to_rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(BASE_DB.resolve()))
    except Exception:
        return str(p)

def abs_from_rel(s: str) -> Path:
    p = Path(s)
    return (BASE_DB / p) if not p.is_absolute() else p

SALIDA_IDX_XLSX = Path("indice_TS_FRD.xlsx")
#SALIDA_IDX_CSV  = Path("indice_TS_FRD.csv")
SALIDA_PARES    = Path("pares_enlazados")
CREAR_SYMLINKS  = True

# Ajusta si quieres sesgo por categoría (primero FULLRANGE, luego MIDWOOFER, etc.)
PRIORIDAD_CARPETAS = {p.name.lower(): i for i, p in enumerate(FRD_ROOTS)}

# === Utilidades ===
TOKENS_BASURA = {
    "parametri","parametro","parametri_ts","ts_params","params","parameters",
    "thiele","small","ts","param","dati","data","misurati","misurato",
    "driver","speaker","woofer","tweeter","mid","fullrange"
}

# Variantes de símbolo de grado; incluye 'ų'
DEG_VARIANTS = "°º˚⁰" + "ų"

def strip_accents_lower(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.lower()

def normalize_for_match(s: str) -> str:
    # Reemplaza grados ANTES de eliminar acentos/ASCII, para capturar '°', 'º', '˚', '⁰' y 'ų'
    s = re.sub(rf"[{re.escape(DEG_VARIANTS)}]\s*", " deg ", s)
    s = strip_accents_lower(s)
    s = s.replace("-", " ").replace("_", " ").replace("/", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def model_key_from_ts_filename(stem: str) -> str:
    base = normalize_for_match(stem)
    words = [w for w in base.split() if w not in TOKENS_BASURA]
    alnum = [w for w in words if re.search(r"[a-z]", w) and re.search(r"\d", w)]
    if alnum:
        return "".join(alnum)
    return "".join(words)

def is_0deg_right(filename: str) -> bool:
    """
    Acepta: ' - 0°.txt', ' - 0u╠¿.txt', ' - 0°.frd', ' - 0u╠¿ R.txt',
            ' - R 0°.txt', ' - 1m 0°.txt', etc.
    """
    name = filename
    # 1) Mojibake típico '0u╠¿' → '0deg'
    name = re.sub(r"(\d)\s*u[^\w\d]{1,3}", r"\1deg", name, flags=re.IGNORECASE)
    # 2) Grados estándar → 'deg'
    name = re.sub(rf"[{re.escape(DEG_VARIANTS)}]\s*", "deg", name)
    # 3) Normalización ASCII y espacios
    name = strip_accents_lower(name)
    name = re.sub(r"\s+", " ", name).strip()
    # 4) 0deg con 'R' opcional antes o después; extensión .txt/.frd opcionalmente con punto
    return bool(re.search(r"(?:^|[\s\-])(?:r\s*)?0\s*deg(?:\s*r)?\s*(?:\.?(?:txt|frd))?$", name))



def collect_frd_candidates(roots: list[Path]) -> list[Path]:
    cands = []
    for root in roots:
        if root.exists():
            cands += list(root.rglob("*.txt"))
            cands += list(root.rglob("*.frd"))
    return [p for p in cands if p.is_file()]

def best_match_frd(model_key: str, frd_list: list[Path]) -> Path | None:
    cands = []
    for p in frd_list:
        ctx = f"{p.parents[1].name} {p.parent.name} {p.stem}" if len(p.parents) >= 2 else f"{p.parent.name} {p.stem}"
        ctx_norm = normalize_for_match(ctx).replace(" ", "")
        score = 0
        if model_key and model_key in ctx_norm:
            score += 3
        if is_0deg_right(p.name):
            score += 5
        # dentro de best_match_frd, deja una sola penalización a 'Z' y que cubra .txt/.frd
        # en best_match_frd deja una sola penalización y hazla dominante
        if re.search(r"\s+z\.(?:txt|frd)$", normalize_for_match(p.name)):
            score -= 12


        carpeta = p.parents[0].name.lower()
        score += max(0, 2 - PRIORIDAD_CARPETAS.get(carpeta, 99))
        path_penalty = len(str(p))
        cands.append((score, -path_penalty, p))
    cands = [c for c in cands if c[0] > 0]
    if not cands:
        return None
    cands.sort(reverse=True)
    return cands[0][2]



def model_key_in_path(model_key: str, path_str: str) -> bool:
    p = Path(path_str)
    ctx = f"{p.parent.name} {p.stem}"
    ctx_norm = normalize_for_match(ctx).replace(" ", "")
    return bool(model_key) and (model_key in ctx_norm)

def check_random_pairs(df: pd.DataFrame, n: int) -> None:
    sub = df[df["Ruta_FRD"].ne("")]
    if sub.empty:
        print("\n=== Verificación: 0 pares disponibles ===")
        return
    n = min(int(n), len(sub))
    sample = sub.sample(n, random_state=None)
    print(f"\n=== Verificación aleatoria de {n} pares TS↔FRD ===")
    for _, r in sample.iterrows():
        modelo = r["Modelo_base"]
        key = r["Modelo_key"]
        frd = r["Ruta_FRD"]
        cat = r.get("Categoria_FRD", "")
        ok_key = model_key_in_path(key, frd)
        ok_0deg = is_0deg_right(Path(frd).name)
        print(f"=> {modelo}") # | cat:{cat} | 0deg:{'OK' if ok_0deg else 'NO'} | key_in_path:{'OK' if ok_key else 'NO'}")
        print(f"  || TS  || {r['Ruta_TS']}")
        print(f"  || frd || {frd}")
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", type=int, default=0, help="Muestra N pares aleatorios en terminal")
    args = parser.parse_args()

    
    FRD_ALL = collect_frd_candidates(FRD_ROOTS)

    filas = []
    ts_files = sorted(list(CARPETA_TS.glob("*.xls*")))
    for f in ts_files:
        stem = f.stem
        model_key = model_key_from_ts_filename(stem)
        frd = best_match_frd(model_key, FRD_ALL)
        filas.append({
            "Modelo_base": stem,
            "Modelo_key": model_key,
            "Categoria_FRD": frd.parents[0].name if frd else "",
            "Ruta_TS": to_rel(f),
            "Ruta_FRD": to_rel(frd) if frd else "",
            "FRD_0deg_R": bool(frd and is_0deg_right(frd.name))
        })        

    df = pd.DataFrame(filas)
    df["__has_FRD"] = df["Ruta_FRD"].ne("")
    df = df.sort_values(["__has_FRD","Modelo_base"], ascending=[False, True], kind="stable").drop(columns="__has_FRD")

    # Salidas
    try:
        df.to_excel(SALIDA_IDX_XLSX, index=False)  # requiere openpyxl
    except Exception:
        pass
    #df.to_csv(SALIDA_IDX_CSV, index=False)

    if CREAR_SYMLINKS:
        SALIDA_PARES.mkdir(parents=True, exist_ok=True)
        for i, r in df.iterrows():
            modelo_slug = re.sub(r"[^A-Za-z0-9]+", "_", r["Modelo_base"]).strip("_")
        if r["Ruta_TS"]:
            dst_ts = SALIDA_PARES / f"{i:04d}_{modelo_slug}_TS.xlsx"
            src_ts = abs_from_rel(r["Ruta_TS"])
            if dst_ts.exists() or dst_ts.is_symlink():
                dst_ts.unlink()
            try:
                dst_ts.symlink_to(src_ts.resolve())
            except OSError:
                shutil.copy2(src_ts, dst_ts)
        if r["Ruta_FRD"]:
            dst_frd = SALIDA_PARES / f"{i:04d}_{modelo_slug}_FRD{Path(r['Ruta_FRD']).suffix}"
            src_frd = abs_from_rel(r["Ruta_FRD"])
            if dst_frd.exists() or dst_frd.is_symlink():
                dst_frd.unlink()
            try:
                dst_frd.symlink_to(src_frd.resolve())
            except OSError:
                shutil.copy2(src_frd, dst_frd)

    if len(sys.argv) == 1:
        sys.argv += ["--check", "3"]  # ajusta N
        args = parser.parse_args()
    
    if args.check > 0:
        check_random_pairs(df, args.check)


if __name__ == "__main__":
    main()
    # =============================================================
    # Detener cronómetro
    ut.myTime.stop(main_watch)
