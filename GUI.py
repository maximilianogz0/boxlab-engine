import tkinter as tk
from tkinter import ttk
import widgets as wdg
from widgets import default_values
import os
import utility as ut
from params import ThieleSmall , boxDimensions
import data
import re
import logging
import user_settings as user
import sketch_module as sk
from tkinter import filedialog as fd

os.system("clear"); print("-> Iniciando el código...\n")
main_watch = ut.myTime.start()

def run_GUI(verbose :bool):
    # Ejecutar la ventana principal
    selectYourSpeaker_Window.mainloop()
        
window_manager = wdg.window()
default = wdg.default_values()
                  
#=================================================================
# ------------- WINDOW INITIALIZATION ----------------------------
#=================================================================

# Inicializa la ventana principal
selectYourSpeaker_Window    :tk.Tk = window_manager.create_window(type="main", 
                                                                  should_hide=False)
# Inicializa la ventana secundaria
chooseSettings_Window       :tk.Tk = window_manager.create_window(type="secondary", 
                                                                  should_hide=True)
# Inicializa la ventana de resultados
showResults_Window          :tk.Tk = window_manager.create_window(type="secondary",
                                                                  should_hide=True)

# ================================================================
# ---------------- WIDGETS SCHEME --------------------------------
# ================================================================
def call_fullWidgets(whichWindow:tk.Tk):
    global selected_speaker
    print(f"Entrando a call_fullWidgets para {whichWindow.title()}")
    
    if whichWindow == selectYourSpeaker_Window:        
        wdg.interactive_widgets.create_title(selectYourSpeaker_Window, "Seleccione su altavoz")        
        listbox                 = wdg.interactive_widgets.create_speaker_listbox(selectYourSpeaker_Window, data.df)    
        wdg.interactive_widgets.create_assignSpeaker_button(selectYourSpeaker_Window, listbox, data.df, chooseSettings_Window, call_fullWidgets)
        
        #selected_speaker = wdg.selected_speaker
        #selected_speaker = wdg.interactive_widgets.on_button_click(listbox, data.df, chooseSettings_Window, call_fullWidgets)
        
        #global selected_speaker
        #selected_speaker = None
    
    elif whichWindow == chooseSettings_Window:
        wdg.interactive_widgets.create_title(chooseSettings_Window,"Configuración")
        
        """"
        tk.Label(chooseSettings_Window, 
                 text="Configuración",
                 font=(wdg.window.title_font, 
                       wdg.window.title_font_size,
                       "bold"),
                 fg=   wdg.window.highlight_color,
                 bg=   wdg.window.bg_color
                 ).pack(pady=wdg.window.std_padding_y)
        """
        tk.Label(chooseSettings_Window, 
                 text=f"{wdg.selected_speaker.speaker_brand} {wdg.selected_speaker.speaker_model}",
                 font=(wdg.window.title_font, 
                       int(wdg.window.title_font_size*0.75),
                       "bold"),
                 fg=   wdg.window.secondary_color,
                 bg=   wdg.window.bg_color,
                 
                 
                 ).pack(pady=wdg.window.std_padding_y)
        
        
        
        wdg.interactive_widgets.create_qtc_section(chooseSettings_Window)
        wdg.interactive_widgets.create_ratio_section(chooseSettings_Window, ratio1_var, ratio2_var, ratio3_var)
        wdg.interactive_widgets.create_thickness_section(chooseSettings_Window, thickness_var)
        wdg.interactive_widgets.create_cutout_section(chooseSettings_Window, cutout_var)
        wdg.interactive_widgets.create_backpanel_section(chooseSettings_Window, backPanel_var)
        wdg.interactive_widgets.create_absorbing_checkbox(chooseSettings_Window, absorbing_var)
        wdg.interactive_widgets.create_saveSettings_button(chooseSettings_Window, showResults_Window, qtc_var, thickness_var, absorbing_var, ratio1_var, ratio2_var, ratio3_var, cutout_var,backPanel_var)

    elif whichWindow == showResults_Window:
        wdg.interactive_widgets.create_title(showResults_Window, f"{wdg.selected_speaker.speaker_brand} {wdg.selected_speaker.speaker_model}")        
                    
        label = tk.Label(chooseSettings_Window, 
                        text="Utilizar:",
                        font=( wdg.window.main_font,
                                wdg.window.main_font_size),
                        fg=wdg.window.secondary_color,
                        bg=wdg.window.bg_color)        
        label.pack(pady= wdg.window.std_padding_y)
                
        text_results = wdg.displays_and_labels.show_results_as_text()
        wdg.displays_and_labels.create_label(showResults_Window,text_results)
        
        path_label = tk.Label(showResults_Window)
        wdg.interactive_widgets.create_browseDir_button(showResults_Window, 
                                                        "Buscar y Guardar",
                                                        path_label)
        path_label.pack(pady=wdg.window.std_padding_y)
        #wdg.displays_and_labels.create_label(showResults_Window, "¡Gracias por usar nuestro programa!")

        
    elif whichWindow is None:
        print("No se ha seleccionado ninguna ventana.")

# ================================================================
# ----------------- WINDOWS FLOW ---------------------------------
# ================================================================

call_fullWidgets(selectYourSpeaker_Window)

# Variables ajustables
qtc_var =           tk.StringVar(value=wdg.default_values.qtc_var)  # Opción por defecto
thickness_var =     tk.StringVar(value=wdg.default_values.thickness_var)  # Grosor de madera por defecto
absorbing_var =     tk.IntVar   (value=wdg.default_values.absorbing_var)  # Casilla booleana
ratio1_var =        tk.StringVar(value=wdg.default_values.ratio1_var)  # Opción por defecto
ratio2_var =        tk.StringVar(value=wdg.default_values.ratio2_var)  # Opción por defecto
ratio3_var =        tk.StringVar(value=wdg.default_values.ratio3_var)  # Opción por defecto
cutout_var =        tk.StringVar(value=wdg.default_values.cutout_var)
backPanel_var =     tk.StringVar(value=wdg.default_values.backPanel_var)

# ====================================================================================
# ====================================================================================












