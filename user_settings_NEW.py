# Parametros ambientales
rho0_kgm3   = 1.2 # Densidad Aire
c           = 343 # Velocidad Aire

# Parametros ajustables
Qmc = NotImplemented    # Con material absorbente?
Qtc = NotImplemented    # Ajuste
Rg_ohm = 0.12   # Resistencia CC del amplificador

DATA_SOURCE = "DIBIRAMA"   # "LSDB" | "DIBIRAMA"
DIBIRAMA_INDEX_XLSX = "indice_TS_FRD.xlsx"
#DIBIRAMA_INDEX_CSV  = "indice_TS_FRD.csv"
#DIBIRAMA_SHEET      = "prueba"


# Parámetros carpinteria
wood_thickness_mm   :int = 15       # Espesor de la madera (mm)
margin_baffle_mm = 2.54 + wood_thickness_mm # margen adicional para la cara frontal

useAbsorbing        :bool = NotImplemented

boxType :str = "CLOSED" # CLOSED, OPEN, PORTED, BANDPASS
boxDims:int = [190, 300, 340]  # Dimensiones de la caja (mm) [ancho, alto, profundidad]
tweeterPosition_mm: int = [60, 30] # Posicion del tweeter (mm) desde la esquina superior izquierda [x, y]

filter_LowDriver_by_Type = [
                        "Woofer", 
                        "Mid Bass",
                        "Low frequency",
                        "Mid-Range",
                        "Shallow Woofer",
                        "Full-range"
                        ]


LSDB_LABEL           :str = "Loudspeaker Database"
LSDB_CONTACT         :str = "loudspeakerdatabase.com"


paper_type          :None
paper_dims          :None

ratioDims = NotImplemented