# Parametros ambientales
rho0_kgm3   = 1.2 # Densidad Aire
c           = 343 # Velocidad Aire

# Parametros ajustables
Qmc = NotImplemented    # Con material absorbente?
Qtc = NotImplemented    # Ajuste
Rg_ohm = 0.12   # Resistencia CC del amplificador

# Parámetros carpinteria
wood_thickness_mm   :int = 15       # Espesor de la madera (mm)
useAbsorbing        :bool = NotImplemented

boxType :str = "CLOSED" # CLOSED, OPEN, PORTED, BANDPASS
boxDims :int = [200, 200, 200] # Dimensiones de la caja (mm) [ancho, alto, profundidad]


paper_type          :None
paper_dims          :None

ratioDims = NotImplemented