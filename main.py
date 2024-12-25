import subprocess
import sys
import utility as ut
import GUI
import os

# Ejecuta el comando para instalar las librerías desde requirements.txt
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# ============================================================

os.system("clear"); print("-> Iniciando el código...\n")
main_watch = ut.myTime.start()

# selected_speaker = None
# ============================================================

GUI.run_GUI(verbose=False)

# ============================================================
# sk.run_SKETCH()
# main_box = params.boxDimensions(studySpeaker)
# main_sketch = sk.new_DXF(filename=sk.DXF_filename, verbose=False)
# main_sk.layers.add("ELEMENTOS",color=1)
# print(f"{sk.blueprint_folder}/{sk.DXF_filename}")

# =============================================================
ut.myTime.stop(main_watch)
