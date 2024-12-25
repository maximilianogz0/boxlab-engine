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

#====================================================================================
#====================================================================================
        
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
        #wdg.displays_and_labels.create_label(chooseSettings_Window, "Seleccione sus ajustes")
        tk.Label(chooseSettings_Window, 
                 text="Seleccione sus ajustes",
                 font=(wdg.window.title_font, 
                       wdg.window.title_font_size,
                       "bold"),
                 fg=   wdg.window.highlight_color,
                 bg=   wdg.window.bg_color
                 ).pack(pady=wdg.window.std_padding_y)
        
        wdg.interactive_widgets.create_qtc_section(chooseSettings_Window, qtc_var)
        wdg.interactive_widgets.create_ratio_section(chooseSettings_Window, ratio1_var, ratio2_var, ratio3_var)
        wdg.interactive_widgets.create_thickness_section(chooseSettings_Window, thickness_var)
        wdg.interactive_widgets.create_absorbing_checkbox(chooseSettings_Window, absorbing_var)
        wdg.interactive_widgets.create_saveSettings_button(chooseSettings_Window, showResults_Window, qtc_var, thickness_var, absorbing_var, ratio1_var, ratio2_var, ratio3_var)

    elif whichWindow == showResults_Window:
        wdg.displays_and_labels.create_selected_speaker_label(showResults_Window)        
                    
        label = tk.Label(chooseSettings_Window, 
                        text="Utilizar:",
                        font=( wdg.window.main_font,
                                wdg.window.main_font_size),
                        fg=wdg.window.secondary_color,
                        bg=wdg.window.bg_color)        
        label.pack(pady=wdg.window.std_padding_y)
                
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
qtc_var =           tk.StringVar(value=default.qtc_var)  # Opción por defecto
thickness_var =     tk.StringVar(value=default.thickness_var)  # Grosor de madera por defecto
absorbing_var =     tk.IntVar   (value=default.absorbing_var)  # Casilla booleana
ratio1_var =        tk.StringVar(value=default.ratio1_var)
ratio2_var =        tk.StringVar(value=default.ratio2_var)
ratio3_var =        tk.StringVar(value=default.ratio3_var)    


# Etiqueta para mostrar el altavoz seleccionado


"""
# Función para asignar el altavoz
def on_button_click(listbox,
                    label_selection,
                    prev_Window, 
                    next_Window):
    global selected_speaker
        
    selected_speaker = data.assign_speaker(listbox, assign_speaker_button, data.df, verbose=False)
    
    if selected_speaker:
        print(f"Altavoz seleccionado: {selected_speaker.speaker_model} {selected_speaker.speaker_brand}")
        wdg.window.close_and_next(prev_Window,next_Window)

    
    return selected_speaker


        
def reset_selection(listbox: tk.Listbox, label_seleccion: tk.StringVar):
    global thiele_small
    
    thiele_small = None  # Limpiar la instancia del altavoz seleccionado
    # label_seleccion.set("Selección de altavoz reiniciada.")  # Cambiar mensaje en el label

    # Limpiar la selección en el Listbox (opcional)
    listbox.selection_clear(0, tk.END)  # Desmarcar cualquier ítem seleccionado        


"""
#====================================================================================
# !!! SELECCIONA TUS AJUSTES !!! :)
#====================================================================================




"""
# Botón para guardar configuraciones
guardar_button = tk.Button(chooseSettings_Window, 
                           text="Siguiente", 
                           command=lambda:(guardar_configuracion(verbose=False), show_results_Window_fx()))
guardar_button.pack(pady=20)

dims = boxDimensions.calcular_dimensiones_plancha(selected_speaker)
"""


    


"""
def show_results_Window_fx():
    showResults_Window.title(window_manager.header_title)
    showResults_Window.geometry(window_manager.size_as_str)
    wdg.window.close_and_next(chooseSettings_Window,showResults_Window)


    ThieleSmall._calcular_parametros(data.thiele_small)
    ThieleSmall.display_calc_settings(data.thiele_small)
    
    #dims = boxDimensions.calcular_dimensiones_plancha(data.thiele_small)
    

    # Muestra las configuraciones guardadas
    configuracion_label = tk.Label(
        showResults_Window,
        text=text_results,
        justify="center"
    )
    configuracion_label.pack(pady=20)

    # Botón para cerrar la nueva ventana
    printSketch_button = tk.Button(showResults_Window, text="Guardar planos de corte", command=sk.run_SKETCH())
    printSketch_button.pack(pady=10)
    
"""""
    #printText_button = tk.Button(show_results_Window_wdo, text="Guardar datos como texto", command=())
    #printText_button.pack(pady=10)
"""""
    

    #QUEDÉ ACAAAA
    setDir_button = tk.Button(showResults_Window, text="Buscar carpeta para guardar", command=(setSave_dirPath(verbose=True)))
    setDir_button.pack(pady=10)

    return show_results_Window_fx

"""

def setSave_dirPath():
    global path
    print("Función --setSave_dirPath-- llamada.")

    path = fd.askdirectory()
    print(f"Los archivos resultantes serán guardados en la ruta: {path}")
    return path

# dirPath = setSave_dirPath()

#wdg.window.close_and_next(selectYourSpeaker_Window, chooseSettings_Window)



# Crear ventana secuendaria

# Llamar a las funciones de widgets.py para crear los elementos de la GUI


# ====================================================================================
# ====================================================================================


# wdg.displays_and_labels.show_results_as_text(showResults_Window,selected_speaker)

""""
def save_textResults():
    
    textResults_filepath = fd.askdirectory()
    
    f = open(textResults_filepath, "w")   # 'r' for reading and 'w' for writing
    f.write(text_results)    # Write inside file 
    f.close()                                # Close file 
    

    return None
    
"""












