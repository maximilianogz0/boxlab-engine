#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ts_ocr_dats.py
Extracción de parámetros TS desde imagen (datasheet) y exportación a formatos:
- TXT estilo DATS (clave=valor; unidades estándar)
- VituixCAD Driver .txt
- JSON / CSV

Requisitos: tesseract, opencv-python, pillow, pytesseract, numpy, pandas
"""

import re, json, csv, math, pathlib
from typing import Dict, Tuple, Optional
import numpy as np
import cv2
from PIL import Image
import pytesseract

# ------------------ Normalización ------------------

# Alias de campos comunes -> clave estándar
ALIASES = {
    r'\bFs\b|resonance\s*frequency': 'Fs_Hz',
    r'\bRe\b|dcr|dc\s*resistance|voice\s*coil\s*resistance': 'Re_Ohm',
    r'\bLe\b|voice\s*coil\s*inductance': 'Le_H',
    r'\bQms\b': 'Qms',
    r'\bQes\b': 'Qes',
    r'\bQts\b': 'Qts',
    r'\bVas\b': 'Vas_m3',
    r'\bSd\b|effective\s*(piston|diaphragm)\s*area': 'Sd_m2',
    r'\bMms\b|moving\s*mass': 'Mms_kg',
    r'\bCms\b|compliance': 'Cms_mN-1',  # m/N
    r'\bRms\b|mechanical\s*loss': 'Rms_Ns_m',
    r'\bBl\b|force\s*factor': 'Bl_Tm',
    r'\bXmax\b': 'Xmax_m',
    r'\bXmech\b|xlim|xdamage': 'Xmech_m',
    r'\bPe\b|rated\s*power|power\s*handling': 'Pe_W',
    r'\bSPL\b|sensitivity': 'SPL',
    r'\bZnom\b|\bZ\b|nominal\s*impedance': 'Znom_Ohm',
    r'\bNo\b|reference\s*efficiency': 'No_percent',
    r'\bEBP\b': 'EBP',
    r'\bQtc\b': 'Qtc',
}

# Tabla de unidades -> (unidad_objetivo, factor)
UNIT_FACTORS = {
    # frecuencia
    'hz': ('Hz', 1.0),

    # resistencia
    'ohm': ('Ohm', 1.0), 'Ω': ('Ohm', 1.0),

    # inductancia
    'h': ('H', 1.0), 'mh': ('H', 1e-3), 'uh': ('H', 1e-6), 'µh': ('H', 1e-6),

    # Vas
    'm3': ('m3', 1.0), 'l': ('m3', 1e-3), 'liter': ('m3', 1e-3), 'litre': ('m3', 1e-3),
    'cm3': ('m3', 1e-6), 'ml': ('m3', 1e-6),

    # Sd
    'm2': ('m2', 1.0), 'cm2': ('m2', 1e-4), 'mm2': ('m2', 1e-6),

    # masa
    'kg': ('kg', 1.0), 'g': ('kg', 1e-3), 'mg': ('kg', 1e-6),

    # compliance
    'm/n': ('mN-1', 1.0), 'mm/n': ('mN-1', 1e-3), 'um/n': ('mN-1', 1e-6), 'µm/n': ('mN-1', 1e-6),

    # rozamiento mecánico
    'n*s/m': ('Ns_m', 1.0), 'n·s/m': ('Ns_m', 1.0), 'ns/m': ('Ns_m', 1.0),

    # excursión
    'm': ('m', 1.0), 'mm': ('m', 1e-3),

    # potencia
    'w': ('W', 1.0),

    # eficiencia
    '%': ('percent', 1.0),
}

# ------------------ Preproceso imagen ------------------

def _deskew(bw: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(bw > 0))
    if coords.size == 0:
        return bw
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = bw.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(bw, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def preprocess_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # filtro para reducir ruido manteniendo bordes de tabla
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    # binarización adaptativa
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 35, 11)
    bw = _deskew(bw)
    return bw

# ------------------ OCR ------------------

def ocr_text_from_bw(bw: np.ndarray) -> str:
    # psm 6: bloques uniformes; si la tabla es una sola columna, psm 4 puede ir mejor.
    config = "--oem 1 --psm 6 -l eng"
    pil = Image.fromarray(bw)
    return pytesseract.image_to_string(pil, config=config)

# ------------------ Parsing ------------------

def _norm_key(raw_key: str) -> Optional[str]:
    k = raw_key.lower()
    k = k.replace(':', ' ').replace('=', ' ').strip()
    for pattern, std in ALIASES.items():
        if re.search(pattern, k, flags=re.I):
            return std
    return None

def _parse_value_unit(token: str) -> Tuple[Optional[float], Optional[str]]:
    t = token.strip()
    # corrige coma decimal europea
    t = re.sub(r'(?<=\d),(?=\d)', '.', t)
    # caso sensibilidad con razón (dB/2.83V/m o dB/W/m)
    if re.search(r'db\s*/\s*2\.?83\s*v\s*/\s*m', t, flags=re.I) or '2.83' in t:
        num = re.findall(r'[-+]?\d+(?:\.\d+)?', t)
        return (float(num[0]) if num else None), 'dB_2p83V_m'
    if re.search(r'db\s*/\s*w\s*/\s*m|db\/1w\/1m', t, flags=re.I):
        num = re.findall(r'[-+]?\d+(?:\.\d+)?', t)
        return (float(num[0]) if num else None), 'dB_W_m'
    # patrón genérico número + unidad opcional
    m = re.match(r'^([+-]?\d+(?:\.\d+)?)(?:\s*([A-Za-zµμΩ/%\.\*\/]+))?$', t)
    if not m:
        # a veces viene “6.3Ω” pegado
        m2 = re.match(r'^([+-]?\d+(?:\.\d+)?)[\s]*([ΩOhmohms]+)$', t, flags=re.I)
        if m2:
            return float(m2.group(1)), 'ohm'
        return None, None
    val = float(m.group(1))
    unit_raw = (m.group(2) or '').strip()
    unit_raw = unit_raw.replace('Ω', 'ohm').replace('µ', 'u').replace('μ', 'u')
    unit_norm = unit_raw.lower()
    # normalizaciones típicas
    unit_norm = unit_norm.replace('ohms', 'ohm').replace('ohm/sq', 'ohm').replace('²', '2').replace('·', '*')
    unit_norm = unit_norm.replace('v/m', '2.83v/m')  # muchos datasheets omiten 2.83
    return val, unit_norm or None

def _convert_unit(val: float, unit_norm: Optional[str], target_hint: Optional[str]) -> Tuple[float, str]:
    if unit_norm and unit_norm in UNIT_FACTORS:
        target, factor = UNIT_FACTORS[unit_norm]
        return val * factor, target
    if unit_norm in ('db_w_m', 'db/1w/1m'):
        return val, 'dB_W_m'
    if unit_norm in ('db_2.83v_m', 'db/2.83v/m', 'db/2,83v/m'):
        return val, 'dB_2p83V_m'
    # sin unidad conocida: conservar pista de destino
    return val, (target_hint or (unit_norm or ''))

def parse_ts_text(text: str) -> Dict[str, Tuple[float, str]]:
    """
    Devuelve diccionario: clave_estandar -> (valor_SI, unidad_estandar)
    """
    lines = [re.sub(r'[^\S\r\n]+', ' ', ln).strip() for ln in text.splitlines()]
    kv: Dict[str, Tuple[float, str]] = {}
    for ln in lines:
        if not ln:
            continue
        # patrones “K: V U” o “K V U”
        m = re.match(r'^([A-Za-zµμΩ/ \.\-\(\)]+?)\s*[:=]?\s*([+-]?\d+(?:[.,]\d+)?(?:\s*[A-Za-zµμΩ/%\.\*\/]+)?)\b', ln)
        if not m:
            continue
        raw_k, raw_v = m.group(1), m.group(2)
        key = _norm_key(raw_k)
        if not key:
            continue
        val, unit_norm = _parse_value_unit(raw_v)
        if val is None:
            continue
        std_val, std_unit = _convert_unit(val, unit_norm, key.split('_')[-1])
        kv[key] = (std_val, std_unit)

    # Derivaciones/correcciones
    if 'Qts' not in kv and 'Qes' in kv and 'Qms' in kv:
        qes = kv['Qes'][0]; qms = kv['Qms'][0]
        kv['Qts'] = ((qes * qms) / (qes + qms), '')
    # Sensibilidad: si falta unidad, asumir dB/2.83V/m (lo más común en fichas modernas)
    if 'SPL' in kv:
        v, u = kv['SPL']
        if u == '':
            kv['SPL'] = (v, 'dB_2p83V_m')
    return kv

# ------------------ Exportadores ------------------

def export_json(ts: Dict[str, Tuple[float, str]], outpath: str) -> str:
    out = pathlib.Path(outpath)
    data = {
        "values": {k: v for k, (v, _) in ts.items()},
        "units":  {k: u for k, (_, u) in ts.items()}
    }
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return str(out)

def export_csv(ts: Dict[str, Tuple[float, str]], outpath: str) -> str:
    out = pathlib.Path(outpath)
    keys = list(ts.keys())
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['key'] + keys)
        w.writerow(['value'] + [ts[k][0] for k in keys])
        w.writerow(['unit'] + [ts[k][1] for k in keys])
    return str(out)

def export_dats_txt(ts: Dict[str, Tuple[float, str]], outpath: str,
                    meta: Optional[Dict[str, str]] = None) -> str:
    """
    TXT estilo DATS (sencillo, línea por parámetro):
    - Encabezados con '#'
    - Claves típicas: Re, Fs, Qes, Qms, Qts, Le, Vas, Mms, Cms, Rms, Bl, Sd, SPL, Znom, Xmax, Xmech, Pe
    - Unidades explícitas en comentarios.
    """
    out = pathlib.Path(outpath)
    # mapa desde claves estándar -> (nombre_salida, unidad_imprimible, formateo)
    MAP = {
        'Re_Ohm': ('Re', 'Ohm', '{:.3f}'),
        'Znom_Ohm': ('Znom', 'Ohm', '{:.0f}'),
        'Fs_Hz': ('Fs', 'Hz', '{:.2f}'),
        'Qes': ('Qes', '', '{:.4f}'),
        'Qms': ('Qms', '', '{:.4f}'),
        'Qts': ('Qts', '', '{:.4f}'),
        'Le_H': ('Le', 'H', '{:.6f}'),
        'Vas_m3': ('Vas', 'L', '{:.3f}'),   # imprimir en litros
        'Mms_kg': ('Mms', 'g', '{:.3f}'),   # imprimir en gramos
        'Cms_mN-1': ('Cms', 'mm/N', '{:.4f}'),  # imprimir en mm/N
        'Rms_Ns_m': ('Rms', 'N*s/m', '{:.3f}'),
        'Bl_Tm': ('Bl', 'Tm', '{:.3f}'),
        'Sd_m2': ('Sd', 'cm^2', '{:.2f}'),  # imprimir en cm^2
        'Xmax_m': ('Xmax', 'mm', '{:.2f}'),
        'Xmech_m': ('Xmech', 'mm', '{:.2f}'),
        'Pe_W': ('Pe', 'W', '{:.0f}'),
        'No_percent': ('No', '%', '{:.3f}'),
        'SPL': ('SPL', 'dB', '{:.1f}'),   # sólo número; unidad detallada en comentario
    }

    lines = []
    lines.append('# DATS-like TS parameter file')
    if meta:
        for k, v in meta.items():
            lines.append(f'# {k}: {v}')

    def _get(k):
        return ts[k][0] if k in ts else None

    # Conversiones a unidades “humanas” impresas
    def _as_liters(m3): return m3 * 1e3 if m3 is not None else None
    def _as_grams(kg): return kg * 1e3 if kg is not None else None
    def _as_mm_per_N(m_per_N): return m_per_N * 1e3 if m_per_N is not None else None
    def _as_cm2(m2): return m2 * 1e4 if m2 is not None else None
    def _as_mm(m): return m * 1e3 if m is not None else None

    # Construcción en orden típico
    order = [
        'Re_Ohm','Znom_Ohm','Fs_Hz','Qes','Qms','Qts','Le_H','Vas_m3','Mms_kg',
        'Cms_mN-1','Rms_Ns_m','Bl_Tm','Sd_m2','Xmax_m','Xmech_m','Pe_W','No_percent','SPL'
    ]
    for key in order:
        if key not in MAP or key not in ts:
            continue
        name, unit_print, fmt = MAP[key]
        val = _get(key)
        # aplicar conversiones “de impresión”
        if key == 'Vas_m3': val = _as_liters(val)
        elif key == 'Mms_kg': val = _as_grams(val)
        elif key == 'Cms_mN-1': val = _as_mm_per_N(val)
        elif key == 'Sd_m2': val = _as_cm2(val)
        elif key in ('Xmax_m','Xmech_m'): val = _as_mm(val)
        if val is None: 
            continue
        # sensibilidad: agregar unidad completa en comentario si es dB/W/m o dB/2.83V/m
        if key == 'SPL':
            spl_unit = ts['SPL'][1] if 'SPL' in ts else ''
            comment_unit = 'dB/2.83V/m' if '2p83' in spl_unit.lower() else ('dB/W/m' if 'w' in spl_unit.lower() else 'dB')
            lines.append(f'{name}={fmt.format(val)}    # {comment_unit}')
        else:
            lines.append(f'{name}={fmt.format(val)}    # {unit_print}')

    out.write_text('\n'.join(lines), encoding='utf-8')
    return str(out)

def export_vituixcad_driver(ts: Dict[str, Tuple[float, str]], outpath: str,
                            meta: Optional[Dict[str, str]] = None) -> str:
    """
    Exporta un archivo Driver para VituixCAD (subset de parámetros).
    Formato: 'Parameter = Value' con encabezados.
    """
    out = pathlib.Path(outpath)
    L = []
    L.append('[Driver]')
    if meta:
        if 'Brand' in meta: L.append(f'Brand = {meta["Brand"]}')
        if 'Model' in meta: L.append(f'Model = {meta["Model"]}')
        if 'Notes' in meta: L.append(f'Notes = {meta["Notes"]}')

    def _g(k): return ts[k][0] if k in ts else None

    # Conversión a unidades que espera Vituix (comunes)
    Vas_l = _g('Vas_m3'); Vas_l = Vas_l*1e3 if Vas_l is not None else None
    Sd_cm2 = _g('Sd_m2'); Sd_cm2 = Sd_cm2*1e4 if Sd_cm2 is not None else None
    Mms_g = _g('Mms_kg'); Mms_g = Mms_g*1e3 if Mms_g is not None else None
    Cms_mmN = _g('Cms_mN-1'); Cms_mmN = Cms_mmN*1e3 if Cms_mmN is not None else None
    Xmax_mm = _g('Xmax_m'); Xmax_mm = Xmax_mm*1e3 if Xmax_mm is not None else None
    Xmech_mm = _g('Xmech_m'); Xmech_mm = Xmech_mm*1e3 if Xmech_mm is not None else None
    Le_mH = _g('Le_H'); Le_mH = Le_mH*1e3 if Le_mH is not None else None

    pairs = {
        'Z': _g('Znom_Ohm'),
        'Re': _g('Re_Ohm'),
        'Fs': _g('Fs_Hz'),
        'Qms': _g('Qms'),
        'Qes': _g('Qes'),
        'Qts': _g('Qts'),
        'Le': Le_mH,
        'Vas': Vas_l,
        'Sd': Sd_cm2,
        'Mms': Mms_g,
        'Cms': Cms_mmN,
        'Rms': _g('Rms_Ns_m'),  # Ns/m
        'Bl': _g('Bl_Tm'),
        'Xmax': Xmax_mm,
        'Xlim': Xmech_mm,
        'Pe': _g('Pe_W'),
    }
    for k, v in pairs.items():
        if v is None: 
            continue
        # decimales razonables por campo
        if k in ('Fs','Sd','Vas','Mms','Cms','Xmax','Xlim','Le'):
            L.append(f'{k} = {v:.3f}')
        elif k in ('Qms','Qes','Qts'):
            L.append(f'{k} = {v:.4f}')
        elif k in ('Z','Re','Pe','Bl','Rms'):
            L.append(f'{k} = {v:.3f}')
        else:
            L.append(f'{k} = {v}')
    out.write_text('\n'.join(L), encoding='utf-8')
    return str(out)

# ------------------ API de alto nivel ------------------

def extract_ts_from_image(image_path: str) -> Dict[str, Tuple[float, str]]:
    """
    Procesa una imagen de datasheet y retorna dict de parámetros TS normalizados:
    clave_estandar -> (valor_SI, unidad_estandar)
    """
    bw = preprocess_image(image_path)
    text = ocr_text_from_bw(bw)
    ts = parse_ts_text(text)
    return ts

def process_image_to_files(image_path: str,
                           outbase: Optional[str] = None,
                           meta: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Ejecuta OCR+parsing y exporta JSON, CSV, DATS-like .txt y VituixCAD driver .txt.
    Devuelve rutas a archivos generados.
    """
    p = pathlib.Path(image_path)
    if outbase is None:
        outbase = p.with_suffix('').as_posix()

    ts = extract_ts_from_image(image_path)
    if not ts:
        raise RuntimeError("No se detectaron parámetros TS en el OCR.")

    paths = {}
    paths['json'] = export_json(ts, outbase + '.ts.json')
    paths['csv'] = export_csv(ts, outbase + '.ts.csv')
    paths['dats'] = export_dats_txt(ts, outbase + '.dats.txt', meta=meta)
    paths['vituixcad'] = export_vituixcad_driver(ts, outbase + '.vituix_driver.txt', meta=meta)
    return paths

# ------------------ CLI mínima ------------------

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Uso: python ts_ocr_dats.py imagen.[jpg|png|tif] [Brand] [Model]")
        sys.exit(1)
    img = sys.argv[1]
    meta = {}
    if len(sys.argv) >= 3: meta['Brand'] = sys.argv[2]
    if len(sys.argv) >= 4: meta['Model'] = sys.argv[3]
    out = process_image_to_files(img, meta=meta)
    for k, v in out.items():
        print(f"{k}: {v}")
