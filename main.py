import GUI
import utility as ut
import os
#import data
#import numpy as np
#import matplotlib.pyplot as plot
#import params
#import sketch_module as sk
#import random
#import string
from ezdxf.gfxattribs import GfxAttribs
# import PySimpleGUI as sg

# ============================================================

os.system("clear"); print("-> Iniciando el código...\n")
main_watch = ut.myTime.start()

# Install libs
ut.install_libs(ut.libs_required, verbose=False)

# ============================================================

GUI.run_GUI()
# Llamar a la función RUN_GUI() para obtener los widgets

# Usar los widgets obtenidos para asignar el altavoz
# data.assign_speaker(None, listbox, label_seleccion, data.df)

# GUI.main_window.mainloop()

"""""""""
studySpeaker = data.thiele_small
studySpeaker.display_spkr_parameters()
"""""""""
# sk.run_SKETCH()

# main_box = params.boxDimensions(studySpeaker)




# main_sketch = sk.new_DXF(filename=sk.DXF_filename, verbose=False)
#main_sk.layers.add("ELEMENTOS",color=1)



# print(f"{sk.blueprint_folder}/{sk.DXF_filename}")

# =============================================================
ut.myTime.stop(main_watch)
