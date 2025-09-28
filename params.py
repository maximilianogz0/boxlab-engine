import numpy as np
import sys
import utility as ut
import os
import user_settings as user
import math
# from sketch_module import selected_speaker as ss


# AVOID RUNNING
if __name__ == "__main__":
    os.system("clear")
    arg = "ERROR: Este código no está pensado para ejecutarse.\n"
    sys.exit(arg)
    
# ========================================================

allowed_spkr_file = (".frd", ".txt")

class ThieleSmall:
    def __init__(self, speaker_model, speaker_brand, URL, Type, Diameter_inch, Diameter_mm, SPL_dB, Fs_Hz, Qms, Qes, Qts, Xmax_mm, Power_W, Pmax_W, Z_ohm, Re_ohm, Le_mH, Sd_cm2, Mms_g, Mmd_g, Cms_uN, Vas_L, Rms):
        # Parámetros generales
        self.speaker_model = speaker_model
        self.speaker_brand = speaker_brand
        self.URL = URL
        self.Type = Type

        # Parámetros físicos y eléctricos
        self.Diameter_inch = Diameter_inch
        self.Diameter_mm = Diameter_mm
        self.SPL_dB = SPL_dB
        self.Fs_Hz = Fs_Hz
        self.Qms = Qms
        self.Qes = Qes
        self.Qts = Qts
        self.Xmax_mm = Xmax_mm
        self.Power_W = Power_W
        self.Pmax_W = Pmax_W
        self.Z_ohm = Z_ohm
        self.Re_ohm = Re_ohm
        self.Le_mH = Le_mH
        self.Sd_cm2 = Sd_cm2
        self.Mms_g = Mms_g
        self.Mmd_g = Mmd_g
        self.Cms_uN = Cms_uN
        self.Vas_L = Vas_L
        self.Rms = Rms
        self.Vb_init = Vas_L
        self.ID = None
        
        # Parámetros calculados (placeholder)
        self.alpha = None
        self.ws_radS = None
        self.Ret_ohm = None
        self.fc_Hz = None
        self.wc_radS = None
        self.Vab_m3 = None
        self.Vb_m3 = None
        
        # Tabla de valores con rangos abiertos para Vb
        
        self.valores_tabla = {
            (0, 20): [0.8, 1.0],     # Si Vb < 20, valores [0.8, 1.0]
            (20, 200): [1.5, 2.0],   # Si 20 < Vb < 200, valores [1.5, 2.0]
            (200, 2000): [2.5, 3.0]  # Si Vb > 200, valores [2.5, 3.0]
        }       

    def _calcular_parametros(self):
        self.ws_radS = 2 * np.pi * self.Fs_Hz
        self.Qes *= (1 + user.Rg_ohm / self.Re_ohm)
        self.Ret_ohm = self.Re_ohm + user.Rg_ohm
        self.alpha = (ThieleSmall.calc_Qec(self) / self.Qes) ** 2 - 1
        self.fc_Hz = self.Fs_Hz * np.sqrt(1 + self.alpha)
        self.wc_radS = 2 * np.pi * self.fc_Hz
        self.Vab_m3 = (self.Vas_L/1000) / self.alpha
        self.Vb_m3 = self.Vab_m3 + self._volumen_altavoz_L() * (1 / 1.25 if user.useAbsorbing else 1)
        self.BL_Tm = self.Re_ohm / math.sqrt(self.Qms * (self.Mms_g / self.Cms_uN)) * math.sqrt(self.Fs_Hz)
        
        self.Vas_m3 = self.Vas_L/1000
        
        if self.Qes is None :
           print(f"""                
                Qes no fue asignado a través de --_calcular_parametros()--:
                """)
         
            
        else:
            print(f"""
                Para probar --_calcular_parametros()--:
                Qes: está asignado a {self.Qes}
                """)        

    def calc_Qec(self):
        Qmc = 7.5        
        if user.useAbsorbing:
            Qmc = 3.5
        return (Qmc * user.Qtc) / (Qmc - user.Qtc)


    def _volumen_altavoz_L(self):
        return (0.41 * (self.Diameter_inch * 2.54 / 100) ** 4)
        
    def display_spkr_parameters(self):
        print(f"{self.speaker_brand} {self.speaker_model}\n")
        print("---- Parámetros del Altavoz ----")
        print(f'Diámetro: \t{self.Diameter_inch} pulgadas')
        print(f'Resistencia (Re): \t{self.Re_ohm} Ω')
        print(f'Frecuencia de resonancia (Fs): \t{self.Fs_Hz} Hz')
        print(f'Área del diafragma (Sd): \t{self.Sd_cm2 * 10000} cm²')
        print(f'Volumen acústico (Vas): \t{self.Vas_L * 1000} L')
        print(f'Compliance (Cms): \t{self.Cms_uN} M/N')
        print(f'Masa (Mms): \t{self.Mms_g * 1000} g')
        print(f'Factor de fuerza (BL): \t{self.BL_Tm}')
        print(f'Factor de calidad total (Qts): \t{self.Qts}')
        print(f'Factor de calidad mecánico (Qms): \t{self.Qms}')
        print(f'Factor de calidad eléctrico (Qes): \t{self.Qes}')
        print(f'Inductancia (Le): \t{self.Le_mH * 1e-6} H')
        print(f'Desplazamiento máximo (Xmax): \t{self.Xmax_mm} mm')
        print()
     
    def display_user_settings(self):
        print("---- Parámetros del Usuario ----")
        print(f'Resistencia del amplificador (Rg): {user.Rg_ohm} Ω')
        print(f'Qmc: {user.Qmc}')
        print(f'Qtc: {user.Qtc}')
        print(f'Densidad del aire (rho0): {user.rho0_kgm3} kg/m³')
        print(f'Velocidad del sonido (c): {user.c} m/s')
        print()
            
    def display_calc_settings(self):
        print("\n---- Parámetros Calculados ----")
        print(f'Frecuencia angular de resonancia (Ws): {self.ws_radS:.2f} rad/s')
        print(f'Resistencia total (Ret): {self.Ret_ohm:.2f} Ω')
        print(f'Alpha: {self.alpha:.2f}')
        print(f'Frecuencia de corte (fc): {self.fc_Hz:.2f} Hz')
        print(f'Frecuencia angular de corte (wc): {self.wc_radS:.2f} rad/s')
        print(f'Volumen de aire equivalente (Vab): {self.Vab_m3*1000:.2f} L')
        print(f'Volumen ocupado por el altavoz: {self._volumen_altavoz_L()*1_000_000} mL')
        print(f'Volumen de la caja (Vb): {self.Vb_m3*1000:.2f} L')
        print()

    def set_Qmc(self):
        # Establecer los valores según los rangos de Vb y useAbsorbing
        if self.Vb_init < 20/1000:
            # Si Vb < 20, retorno uno de dos posibles valores
            return 5 if user.useAbsorbing else 10
        elif 20/1000 <= self.Vb_init <= 200/1000:
            # Si Vb está entre 20 y 200, retorno otros dos posibles valores
            return 3.5 if user.useAbsorbing else 7.5
        elif self.Vb_init > 200/1000:
            # Si Vb > 200, retorno otros dos posibles valores
            return 2 if user.useAbsorbing else 5
        return None  # Si Vb no se encuentra en ningún rango, retornar None
    
    
    

Qtc_range = [0.5, 1.1] # [Amortiguamiento crítico , C2 Chebyshev]

def volumen_interior_L(ancho_ext_mm, alto_ext_mm, prof_ext_mm, espesor_mm):
    ancho_int = ancho_ext_mm - 2 * espesor_mm
    alto_int = alto_ext_mm - 2 * espesor_mm
    prof_int = prof_ext_mm - 2 * espesor_mm

    if any(x <= 0 for x in [ancho_int, alto_int, prof_int]):
        raise ValueError("Una o más dimensiones interiores son negativas o cero.")

    volumen_mm3 = ancho_int * alto_int * prof_int
    volumen_L = volumen_mm3 / 1_000_000  # mm³ a litros
    return volumen_L


        
class boxDimensions:
    
    def __init__(self, Speaker):                
        self.speaker = Speaker       
        
        self.ancho_ext_mm     = user.boxDims[0]
        self.prof_ext_mm      = user.boxDims[2]
        self.alto_ext_mm      = user.boxDims[1]
        self.espesor_mm       = user.wood_thickness_mm       
        
        self.Vb_m3 = self.calcular_Vb_m3()
    
    def calcular_Vb_m3(self):
        ancho_int = self.ancho_ext_mm - 2 * self.espesor_mm
        alto_int  = self.alto_ext_mm - 2 * self.espesor_mm
        prof_int  = self.prof_ext_mm - 2 * self.espesor_mm

        if any(x <= 0 for x in [ancho_int, alto_int, prof_int]):
            raise ValueError("Una o más dimensiones interiores son negativas o cero.")

        volumen_mm3 = ancho_int * alto_int * prof_int
        return volumen_mm3 / 1_000_000_000  # mm³ a m³
    
    def display_parameters(self):
        ancho_int = self.ancho_ext_mm - 2 * self.espesor_mm
        alto_int  = self.alto_ext_mm - 2 * self.espesor_mm
        prof_int  = self.prof_ext_mm - 2 * self.espesor_mm

        print("DIMENSIONES DE LA CAJA:")
        print()
        print(f"  Espesor madera:      {self.espesor_mm} mm")        
        print()
        print(f"  Ancho exterior:      {self.ancho_ext_mm} mm")
        print(f"  Alto exterior:       {self.alto_ext_mm} mm")
        print(f"  Profundidad exterior:{self.prof_ext_mm} mm")
        print()
        print(f"  Ancho interior:      {ancho_int} mm")
        print(f"  Alto interior:       {alto_int} mm")
        print(f"  Profundidad interior:{prof_int} mm")
        print()
        print(f"  Volumen interior:        {self.Vb_m3 * 1000:.3f} L")
        print()
        

    def calcular_dimensiones_plancha(self,selected_speaker:ThieleSmall):        
        if selected_speaker.Vb_m3 is None:
            print("Error: Vb_m3 no está configurado.")
        
        # Calcular factor de escalado según volumen y relación de aspecto
        factor =            (self.Vb_m3 / (user.ratioDims[0] * user.ratioDims[1] * user.ratioDims[2])) ** (1/3)
        ancho_base =        user.ratioDims[0] * factor
        alto_base =         user.ratioDims[1] * factor
        profundidad_base =  user.ratioDims[2] * factor
        t =                 user.wood_thickness_mm / 1000

        if user.areInteriorDims:
            # Si el ratio se refiere a dimensiones interiores
            self.frontal_posterior_m =  (ancho_base + 2*t,  alto_base + 2*t)
            self.lateral_m =            (profundidad_base,  alto_base + 2*t)
            self.superior_inferior_m =  (ancho_base,        profundidad_base)

        else:
            # Si el ratio se refiere a dimensiones exteriores CORREGIIIIIIIIIIIRRRRRRRRR NO ESTA LA FORMULA
            self.frontal_posterior_m =  (ancho_base - 2*t,          alto_base - 2*t)
            self.lateral_m =            (profundidad_base - 2*t,    alto_base - 2*t)
            self.superior_inferior_m =  (ancho_base - 2*t,          profundidad_base - 2*t)


            
        # Redondear las dimensiones a 1 mm (0.001 m)
        self.frontal_posterior_m    = (round(1000 * self.frontal_posterior_m[0])/1000,  round(1000 * self.frontal_posterior_m[1])/1000)
        self.superior_inferior_m    = (round(1000 * self.superior_inferior_m[0])/1000,  round(1000 * self.superior_inferior_m[1])/1000)
        self.lateral_m              = (round(1000 * self.lateral_m[0])/1000,            round(1000 * self.lateral_m[1])/1000)
                
        return [(1000*self.frontal_posterior_m[0],     1000*self.frontal_posterior_m[1]),
                (1000*self.lateral_m[0],               1000*self.lateral_m[1]),
                (1000*self.superior_inferior_m[0],     1000*self.superior_inferior_m[1])
                ]

    def mostrar_dimensiones_plancha(self):
        print("\n--- Dimensiones de cada plancha: ---")
        print(f"Frontal y Posterior:    {1000*self.frontal_posterior_m[0]:.0f} mm x {1000*self.frontal_posterior_m[1]:.0f} mm")
        print(f"Laterales:              {1000*self.lateral_m[0]:.0f} mm x {1000*self.lateral_m[1]:.0f} mm")
        print(f"Superior e Inferior:    {1000*self.superior_inferior_m[0]:.0f} mm x {1000*self.superior_inferior_m[1]:.0f} mm")

        print()