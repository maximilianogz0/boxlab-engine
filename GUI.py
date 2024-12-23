import tkinter as tk
from tkinter import ttk
import widgets
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

#====================================================================================
#====================================================================================

selected_speaker = None
dims = None
text_results = None
path = None

#====================================================================================
#====================================================================================




class Window_MGMT:
    def __init__(self):        
        pass
    
    # Ocultar la ventana actual y mostrar la siguiente
    def close_and_next(prev_window: tk.Tk, next_window: tk.Tk):
        prev_window.withdraw()  # Ocultar la ventana actual
        next_window.deiconify()  # Mostrar la siguiente ventana
        
    
    header_title :str = "BoxDesign Home (by PulsosAudio)"
    size_as_list:int = [650,500]
    size_as_str:str = f"{(size_as_list[0])}x{size_as_list[1]}"
        



# Configuración de la ventana principal
selectYourSpeaker_Window = tk.Tk()
selectYourSpeaker_Window.title(Window_MGMT.header_title)
selectYourSpeaker_Window.geometry(Window_MGMT.size_as_str)

                
#====================================================================================
# SELECCIONA TU ALTAVOZ
#====================================================================================

# Etiqueta inicial
label_1 = tk.Label(selectYourSpeaker_Window, text="Seleccione un altavoz de la lista:")
label_1.pack()

# Crear un Listbox para mostrar los altavoces
listbox = tk.Listbox(selectYourSpeaker_Window, width=50, height=15)
listbox.pack(pady=10)

# Llenar el Listbox con los altavoces (Marca, Modelo y Tipo)
for index, row in data.df.iterrows():
    listbox.insert(tk.END, f"{row['Brand']} {row['Model']} - ({row['Type']})")

# Etiqueta para mostrar el altavoz seleccionado
label_seleccion = tk.StringVar()
label_archivo = tk.Label(selectYourSpeaker_Window, textvariable=label_seleccion)
label_archivo.pack(pady=10)


# Función para asignar el altavoz
def on_button_click(prev_Window, next_Window):
    global selected_speaker
        
    selected_speaker = data.assign_speaker(listbox, label_seleccion, data.df, verbose=False)
    Window_MGMT.close_and_next(prev_Window,next_Window)
    
    if selected_speaker:
        print(f"Altavoz seleccionado: {selected_speaker.speaker_model} {selected_speaker.speaker_brand}")
    
    return selected_speaker
        
def reset_selection(listbox: tk.Listbox, label_seleccion: tk.StringVar):
    global thiele_small
    
    thiele_small = None  # Limpiar la instancia del altavoz seleccionado
    # label_seleccion.set("Selección de altavoz reiniciada.")  # Cambiar mensaje en el label

    # Limpiar la selección en el Listbox (opcional)
    listbox.selection_clear(0, tk.END)  # Desmarcar cualquier ítem seleccionado        


# Botón para asignar el altavoz
boton_asignar = tk.Button(selectYourSpeaker_Window, 
                          text=     "Asignar Altavoz", 
                          command=  lambda:on_button_click( selectYourSpeaker_Window,
                                                            chooseSettings_Window))

boton_asignar.pack(pady=10)

#dims = on_button_click()

#====================================================================================
# !!! SELECCIONA TUS AJUSTES !!! :)
#====================================================================================

def guardar_configuracion(verbose:bool):
    #global Qtc, wood_thickness_mm, useAbsorbing, ratioDims
    user.Qtc = float(qtc_var.get())
    user.wood_thickness_mm = int(thickness_var.get())
    user.useAbsorbing = bool(absorbing_var.get())
    user.ratioDims = (float(ratio1_var.get()), float(ratio2_var.get()), float(ratio3_var.get()))
    
    if verbose:
        print("Configuraciones guardadas:")
        print(f"Qtc: {user.Qtc}")
        print(f"Grosor de madera: {user.wood_thickness_mm} mm")
        print(f"Uso de absorbente acústico: {user.useAbsorbing}")
        print(f"Relación de aspecto: {user.ratioDims}")
    
# Crear ventana secuendaria
chooseSettings_Window = tk.Toplevel()
chooseSettings_Window.title(Window_MGMT.header_title)
chooseSettings_Window.geometry(Window_MGMT.size_as_str)
chooseSettings_Window.withdraw()    




# Variables ajustables
qtc_var = tk.StringVar(value="0.707")  # Opción por defecto
thickness_var = tk.StringVar(value="12")  # Grosor de madera por defecto
absorbing_var = tk.IntVar(value=0)  # Casilla booleana
ratio1_var = tk.StringVar(value="1")
ratio2_var = tk.StringVar(value="1")
ratio3_var = tk.StringVar(value="1")

# Sección Qtc
qtc_label = tk.Label(chooseSettings_Window, text="Qtc (ajuste B4):")
qtc_label.pack(pady=5)
qtc_options = ["0.707", "0.9", "1.1", "1.4"]
qtc_dropdown = ttk.Combobox(chooseSettings_Window, textvariable=qtc_var, values=qtc_options, state="readonly")
qtc_dropdown.pack()

# Sección Grosor de madera
thickness_label = tk.Label(chooseSettings_Window, text="Grosor de madera (mm):")
thickness_label.pack(pady=5)
thickness_spinbox = ttk.Spinbox(chooseSettings_Window, from_=10, to=40, increment=1, textvariable=thickness_var, width=10)
thickness_spinbox.pack()

# Casilla booleana para uso de absorbente acústico
absorbing_checkbox = tk.Checkbutton(chooseSettings_Window, text="Usar absorbente acústico", variable=absorbing_var)
absorbing_checkbox.select()
absorbing_checkbox.pack(pady=10)

# Relación de aspecto
ratio_label = tk.Label(chooseSettings_Window, text="Relación de aspecto\n")
ratio_label.pack(pady=5)
ratio_frame = tk.Frame(chooseSettings_Window)
ratio_frame.pack()

ratio1_entry = tk.Entry(ratio_frame, textvariable=ratio1_var, width=5, justify="center")
ratio1_entry.pack(side="left")
tk.Label(ratio_frame, text=" : ").pack(side="left")
ratio2_entry = tk.Entry(ratio_frame, textvariable=ratio2_var, width=5, justify="center")
ratio2_entry.pack(side="left")
tk.Label(ratio_frame, text=" : ").pack(side="left")
ratio3_entry = tk.Entry(ratio_frame, textvariable=ratio3_var, width=5, justify="center")
ratio3_entry.pack(side="left")

# Botón para guardar configuraciones
guardar_button = tk.Button(chooseSettings_Window, 
                           text="Siguiente", 
                           command=lambda:(guardar_configuracion(verbose=False), show_results_Window_fx()))
guardar_button.pack(pady=20)

#dims = boxDimensions.calcular_dimensiones_plancha(selected_speaker)

def display_TextResults():
        global text_results
        text_results = (f"""
        
        {data.thiele_small.speaker_brand} {data.thiele_small.speaker_model} 
        
        Espesor del material:
                {user.wood_thickness_mm}mm
        
        Dimensiones de tablas:
        
        Frontal-Trasera:
        |2|
        {dims[0][0]:.0f}mm x {dims[0][1]:.0f}mm
        
        Laterales:
        |2|
        {dims[1][0]:.0f}mm x {dims[1][1]:.0f}mm
        
        Superior-Inferior:
        |2|
        {dims[2][0]:.0f}mm x {dims[2][1]:.0f}mm
        
                        
        """)    
        return text_results
    


def show_results_Window_fx():
    show_results_Window_wdo = tk.Toplevel()
    show_results_Window_wdo.title(Window_MGMT.header_title)
    show_results_Window_wdo.geometry(Window_MGMT.size_as_str)
    Window_MGMT.close_and_next(chooseSettings_Window,show_results_Window_wdo)


    ThieleSmall._calcular_parametros(data.thiele_small)
    ThieleSmall.display_calc_settings(data.thiele_small)
    
    #dims = boxDimensions.calcular_dimensiones_plancha(data.thiele_small)
    

    # Muestra las configuraciones guardadas
    configuracion_label = tk.Label(
        show_results_Window_wdo,
        text=text_results,
        justify="center"
    )
    configuracion_label.pack(pady=20)

    # Botón para cerrar la nueva ventana
    printSketch_button = tk.Button(show_results_Window_wdo, text="Guardar planos de corte", command=sk.run_SKETCH())
    printSketch_button.pack(pady=10)
    
    """""
    printText_button = tk.Button(show_results_Window_wdo, text="Guardar datos como texto", command=())
    printText_button.pack(pady=10)
    """""
    

    #QUEDÉ ACAAAA
    setDir_button = tk.Button(show_results_Window_wdo, text="Buscar carpeta para guardar", command=(setSave_dirPath(verbose=True)))
    setDir_button.pack(pady=10)

    return show_results_Window_fx



def setSave_dirPath(verbose):
    global path
    path = fd.askdirectory()
    if verbose:
        print(f"Los archivos resultantes serán guardados en la ruta: {path}")
    return path

# dirPath = setSave_dirPath()

    

""""
def save_textResults():
    
    textResults_filepath = fd.askdirectory()
    
    f = open(textResults_filepath, "w")   # 'r' for reading and 'w' for writing
    f.write(text_results)    # Write inside file 
    f.close()                                # Close file 
    

    return None
    
"""












## ========================================================================
## ========================================================================
def run_GUI(verbose:bool=False):
    # Ejecutar la ventana principal
    selectYourSpeaker_Window.mainloop()