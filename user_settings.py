# Parametros ambientales
rho0_kgm3   = 1.2 # Densidad Aire
c           = 343 # Velocidad Aire

# Parametros ajustables
Qmc = NotImplemented    # Con material absorbente?
Qtc = NotImplemented    # Ajuste
Rg_ohm = 0.12   # Resistencia CC del amplificador

# Parámetros carpinteria
wood_thickness_mm   :int = NotImplemented
areInteriorDims     :bool = NotImplemented
useAbsorbing        :bool = NotImplemented

paper_type          :None
paper_dims          :None



# Relación de aspecto deseada (ancho : alto : profundidad)
# GOLDEN RATIO (0.6, 1, 1.6)
ratioDims = NotImplemented


"""""""""
# Parametros ambientales
rho0_kgm3   = 1.2 # Densidad Aire
c           = 343 # Velocidad Aire

# Parametros ajustables
Qmc = 3.5  # Con material absorbente
Qtc = 0.707 # Ajuste B4
Rg_ohm = 0.12   # Resistencia CC del amplificador

# Parámetros carpinteria
wood_thickness_mm   :int = 15
areInteriorDims     :bool = False
useAbsorbing        :bool = False

paper_size          :str = "A3"

# Relación de aspecto deseada (ancho : alto : profundidad)
# GOLDEN RATIO (0.6, 1, 1.6)
ratioDims = (0.6, 1, 1.6) 

"""""""""