import subprocess
import sys
import utility as ut
import GUI
import os
import params_NEW as params

# Ejecuta el comando para instalar las librerías desde requirements.txt
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# ============================================================

os.system("clear"); print("-> Iniciando el código...\n")
main_watch = ut.myTime.start()

# ============================================================

# GUI.run_GUI(verbose=False)


box = params.boxDimensions(Speaker=None).display_parameters()


# =============================================================
ut.myTime.stop(main_watch)

# DESAFIOS:
# Incluir perforaciones para tornillos
# Incluir variedad de formas para back panel
# Incluir subir parlantes propios