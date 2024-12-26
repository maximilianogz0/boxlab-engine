import tkinter as tk
from tkinter import ttk
from data import df, assign_speaker
#import data 
import user_settings as user
import params
from tkinter import filedialog as fd
import sketch_module as sk
import math


global qtc_var, thickness_var, absorbing_var, ratio1_var, ratio2_var, ratio3_var
qtc_var = None  # Inicializar la variable
thickness_var = None
absorbing_var = None
ratio1_var = None
ratio2_var = None
ratio3_var = None
#selected_speaker = None

class interactive_widgets:

    @staticmethod
    def create_thickness_section(which_Window, thickness_var):
        thickness_label = tk.Label(which_Window, 
                                   text="Grosor de madera (mm):",
                                   bg=window.bg_color,
                                   font=(window.main_font, 
                                         window.main_font_size),
                                   justify="center"
                                   )
        thickness_label.pack(pady=window.std_padding_y)
        
        thickness_spinbox = ttk.Spinbox(which_Window, 
                                        from_=10,   to=40,  increment=1, 
                                        textvariable=thickness_var,
                                        background=window.bg_color,
                                        width=10,
                                        font=(window.main_font, 
                                              window.main_font_size),
                                        justify="center"                                        
                                        )
        thickness_spinbox.pack(pady=window.std_padding_y)

    @staticmethod
    def create_cutout_section(which_Window, 
                              cutout_var):
        """
        Crea una sección para ingresar el diámetro del cutout.
        
        Args:
            which_Window: La ventana donde se colocará la sección.
            cutout_var: Una variable de control (tk.IntVar) para almacenar el valor ingresado.
        """
        
        # Etiqueta para el diámetro del cutout
        cutout_label = tk.Label(
            which_Window,
            text="Diámetro del cutout (mm):",
            bg=window.bg_color,
            font=(window.main_font, window.main_font_size),
            justify="center"
        )
        cutout_label.pack(pady=window.std_padding_y,
                          padx=window.std_padding_x)
        
        # Spinbox para ingresar el diámetro del cutout
        # cutout_var = tk.IntVar(value=100)
        cutout_spinbox = ttk.Spinbox(
            which_Window,
            from_=1,  # Valor mínimo
            to=500,    # Valor máximo
            increment=1,  # Incremento por paso
            textvariable= cutout_var,
            background=window.bg_color,
            width=10,
            font=(window.main_font, window.main_font_size),
            justify="center"
        )
        cutout_spinbox.pack(pady=window.std_padding_y,
                            padx=window.std_padding_x)
        

    @staticmethod
    def create_backpanel_section(which_Window, backPanel_var):
        """
        Crea una sección para ingresar el espesor del Backpanel.
        
        Args:
            which_Window: La ventana donde se colocará la sección.
            backPanel_var: Una variable de control (tk.IntVar) para almacenar el valor ingresado.
        """
        
        # Etiqueta para el espesor del Backpanel
        backpanel_label = tk.Label(
            which_Window,
            text="Diámetro para el Backpanel (mm):",
            bg=window.bg_color,
            font=(window.main_font, 
                window.main_font_size),
            justify="center"
        )
        backpanel_label.pack(pady=window.std_padding_y,
                            padx=window.std_padding_x)
        
        # Spinbox para ingresar el espesor del Backpanel
        backpanel_spinbox = ttk.Spinbox(
            which_Window,
            from_=1,       # Valor mínimo
            to=100,         # Valor máximo
            increment=1,   # Incremento por paso
            textvariable=backPanel_var,
            background=window.bg_color,
            width=10,
            font=(window.main_font, window.main_font_size),
            justify="center"
        )
        backpanel_spinbox.pack(pady=window.std_padding_y,
                            padx=window.std_padding_x)






    @staticmethod
    def create_absorbing_checkbox(which_Window, absorbing_var):
        absorbing_checkbox = tk.Checkbutton(which_Window, 
                                            text="Usar absorbente acústico", 
                                            variable=absorbing_var,
                                            bg=window.bg_color,
                                            font=(window.main_font, 
                                                  window.main_font_size)
                                            )
        absorbing_checkbox.select()
        absorbing_checkbox.pack(pady=window.std_padding_y)

    @staticmethod
    def create_ratio_section(which_Window, ratio1_var, ratio2_var, ratio3_var):
        ratio_label = tk.Label(which_Window, 
                               text="Relación de aspecto",
                               font=(   window.main_font, 
                                        window.main_font_size),
                               bg=      window.bg_color)                 
        ratio_label.pack(pady=window.std_padding_y)
        
        
        ratio_frame = tk.Frame(which_Window,
                               bg=window.bg_color)
        ratio_frame.pack(pady=window.std_padding_y)

        ratio1_entry = tk.Entry(ratio_frame, 
                                textvariable=ratio1_var, 
                                width=5, justify="center",
                                bg=window.bg_color,
                                font=(window.main_font, 
                                      window.main_font_size)
                                )
        ratio1_entry.pack(side="left")
        
        tk.Label(ratio_frame, text=" : ").pack(side="left")
        ratio2_entry = tk.Entry(ratio_frame, 
                                textvariable=ratio2_var, 
                                width=5, justify="center",
                                bg=window.bg_color,
                                font=(window.main_font, 
                                      window.main_font_size)
                                )
        ratio2_entry.pack(side="left")
        
        tk.Label(ratio_frame, text=" : ").pack(side="left")
        ratio3_entry = tk.Entry(ratio_frame, 
                                textvariable=ratio3_var, 
                                width=5, justify="center",
                                bg=window.bg_color,
                                font=(window.main_font, 
                                      window.main_font_size)
                                )
        ratio3_entry.pack(side="left")

    @staticmethod
    def create_saveSettings_button(which_Window, next_Window, 
                                   qtc_var, 
                                   thickness_var, 
                                   absorbing_var, 
                                   ratio1_var, 
                                   ratio2_var, 
                                   ratio3_var,
                                   cutout_var,
                                   backPanel_var):

        prev_Window = which_Window
        
        def save_and_next():
            # global qtc_var, thickness_var, absorbing_var, ratio1_var, ratio2_var, ratio3_var
            user.Qtc                = float(qtc_var.get())
            user.wood_thickness_mm  = int(thickness_var.get())
            user.useAbsorbing       = bool(absorbing_var.get())
            user.ratioDims          = (float(ratio1_var.get()), float(ratio2_var.get()), float(ratio3_var.get()))    
            sk.cutout_mm            = int(cutout_var.get())  # Guardar el diámetro del cutout
            sk.backPanel_mm         = int(backPanel_var.get())  # Guardar el diámetro del cutout

            
            window.close_and_next(prev_Window, next_Window) # en este metodo ya se llaman los widgets de la siguiente ventana
        
        saveSettings_button = tk.Button(which_Window, 
                                        text="Siguiente", 
                                        command=save_and_next,
                                        font=(window.main_font, 
                                              window.main_font_size)
                                        )
        saveSettings_button.pack(pady=window.std_padding_y)
                
    @staticmethod    
    def create_qtc_section(which_Window):
        
        qtc_var = tk.StringVar()
        qtc_value = tk.DoubleVar()
        
        qtc_label = tk.Label(which_Window, 
                             text="Preferencia:",
                             bg=window.bg_color,
                             font=(window.main_font,
                                   window.main_font_size)
                             )
        qtc_label.pack(pady=window.std_padding_y)
        
        qtc_mapping = {            
            "Alta Definición (D2 Bessel)"           : 1/math.sqrt(3),   #D2 Bessel
            "Sonido Equilibrado (B2 Butterworth)"   : 1/math.sqrt(2),   #B2 Butterworth
            "Sonido Profundo (C2 Chebyshev)"        : 1.25              #C2 Chebyshev
        }
        

        
        qtc_dropdown = ttk.Combobox(which_Window, 
                                    textvariable=qtc_var, 
                                    values=list(qtc_mapping.keys()),  # Usar las claves del diccionario
                                    state="readonly",
                                    width=30,
                                    background=window.bg_color,
                                    font=(window.main_font, 
                                          window.main_font_size),
                                    justify="center"
                                    
                                    )
        
        dropdown_default_text = "Sonido Equilibrado (B2 Butterworth)"
        qtc_dropdown.set(dropdown_default_text)  # Mostrar el texto inicial
        qtc_var.set(dropdown_default_text)       # Texto inicial visible
        qtc_value.set(qtc_mapping[dropdown_default_text])  # Valor flotante inicial
        
            # Función para actualizar el valor flotante basado en la opción seleccionada
        def update_qtc(event):
            selected_text = qtc_dropdown.get()  # Obtener el texto seleccionado
            qtc_var.set(selected_text)         # Actualizar el texto visible
            qtc_value.set(qtc_mapping[selected_text])  # Actualizar el valor flotante asociado

    # Asociar el evento de selección al combobox
        qtc_dropdown.bind("<<ComboboxSelected>>", update_qtc)
        
        qtc_dropdown.pack(pady=window.std_padding_y)
        
        def set_displayed_text(value):
            for key, val in qtc_mapping.items():
                if val == value:
                    qtc_dropdown.set(key)  # Esto asegura que el texto correcto se muestra
                    break
        
        set_displayed_text(qtc_var.get())  # Mostrar el texto correspondiente al valor flotante al iniciar


    @staticmethod        
    def create_title(which_Window, title:str):
        title_label = tk.Label(which_Window,
                               text=    title, 
                               font=    (window.title_font, 
                                        window.title_font_size,
                                        "bold"), 
                                bg=     window.bg_color,
                                fg=     window.highlight_color
                                )
                

        title_label.pack(pady= 4* window.std_padding_y)
        
    @staticmethod
    def create_button(which_Window, text, command):
        button = tk.Button(which_Window, 
                           text=text, 
                           font=(window.main_font,window.main_font_size),
                           command=command)
        button.pack(pady=window.std_padding_y)
            
    @staticmethod            
    def create_listbox(which_Window):
        listbox = tk.Listbox(which_Window, 
                             width=50,
                             font=(window.main_font,
                                   window.main_font_size),
                             bg=window.bg_color
                )
        listbox.pack(pady=window.std_padding_y)
        return listbox
    
    @staticmethod            
    def create_speaker_listbox(which_Window,listbox, **listbox_properties):
    # Crear una listbox con propiedades personalizables
        listbox = tk.Listbox(which_Window, **listbox_properties)

        # Llenar la listbox con datos del DataFrame
        for index, row in df.iterrows():
            listbox.insert(tk.END, f"{row['Brand']} {row['Model']} - ({row['Type']})")
        
        # Empacar la listbox
        listbox.pack(pady=window.std_padding_y, 
                     fill=tk.BOTH, 
                     expand=True,
                     padx=window.std_padding_x)  # Empaque estándar, ajustable según necesidades
        return listbox            
            
    # Botón para asignar el altavoz
    @staticmethod
    def create_assignSpeaker_button(which_Window, 
                             listbox, 
                             df, 
                             next_Window,
                             call_fullWidgets):
        
        prev_Window = which_Window # Ninguna utilidad. Es solo para salir del paso al eliminar argumentos
         
        def on_button_click(prev_Window, next_Window):
            global selected_speaker 
            print("Ejecutando on_button_click...")
           
            selected_speaker = assign_speaker(listbox, 
                                              None, 
                                              df,
                                              prev_Window,
                                              next_Window, 
                                              verbose=False) ##REVISAR ESTO. "True" arroja error
            
            print(f"selected_speaker asignado: {selected_speaker}, tipo: {type(selected_speaker)}")            
            
            if isinstance(selected_speaker, params.ThieleSmall):
                print(f"Modelo seleccionado en --on_button_click()--: {selected_speaker.speaker_model}")
            else:
                print("Error: 'selected_speaker' no es una instancia de ThieleSmall en --on_button_click()--.")
                #selected_speaker = None
            
            if selected_speaker:
                print(f"Modelo seleccionado en --on_button_click()--: {selected_speaker.speaker_model}")
                window.close_and_next(prev_Window, next_Window)
                #return selected_speaker
                
            else:
                print("Error: 'selected_speaker' no está configurado dentro de --on_button_click()--.")
                #return None
            
        button = tk.Button(which_Window, 
                           text="Asignar altavoz", 
                           command=lambda:on_button_click(prev_Window,next_Window))
        button.pack(pady=window.std_padding_y*5)    
        return button

    @staticmethod
    def create_browseDir_button(which_Window, 
                                text:str,
                                label:tk.Label):        
        label.config(bg=window.bg_color)

        def on_button_click():
            print("setSave_dirPath llamado")
            
            def setSave_dirPath():
                path = fd.askdirectory()
                if path:
                    print(f"Los archivos resultantes serán guardados en la ruta: {path}")
                    label.config(   text=f"Los archivos serán guardados en: {path}",
                                    font=(  window.main_font,
                                            window.main_font_size),
                                    bg=     window.bg_color,
                                    fg=     window.secondary_color,
                                    pady=   window.std_padding_y *4)
            
            ## CORRE ESTO AL PRESIONAR BOTON
            setSave_dirPath()
            sk.run_SKETCH(selected_speaker)
                       
    
        
        browseDir_button = tk.Button(which_Window, 
                                     text=text, 
                                     command=on_button_click,
                                     font=(window.main_font, 
                                           window.main_font_size)
                                     )
        browseDir_button.pack(pady=window.std_padding_y)
        return browseDir_button
            
class displays_and_labels:

    def create_label(which_Window, text):
        label = tk.Label(which_Window, 
                         text=text,
                         font=( window.main_font,
                                window.main_font_size),
                         bg=window.bg_color)
        
        label.pack(pady=window.std_padding_y,
                   padx=window.std_padding_x,
                   #fill="both",                                      
                   expand=True)
    

    def create_selected_speaker_label(which_Window):
            label_seleccion = tk.StringVar()
            label_seleccion.set(f"{selected_speaker.speaker_brand} {selected_speaker.speaker_model}") ### esto es nuevo. probar. puede que no funcione.
            
            label_archivo = tk.Label(which_Window, 
                                    textvariable=label_seleccion,
                                    font=(window.title_font, 
                                          window.title_font_size,
                                          "bold"),
                                    bg=window.bg_color,
                                    fg=window.highlight_color)
            label_archivo.pack(pady=window.std_padding_y)
            

    def show_results_as_text(): 
        global selected_speaker
        print(f"selected_speaker antes de validación en --show_results_as_text--: {selected_speaker}, tipo: {type(selected_speaker)}")

        # START DEBUG -------------------------------------
        if selected_speaker is None:
            print("Error: 'selected_speaker' no está configurado para --show_results_as_text()--.")            
        elif selected_speaker is not None:
            print(f"Modelo: {selected_speaker.speaker_model}")
            print(f"Marca: {selected_speaker.speaker_brand}")
        
        elif selected_speaker is not params.ThieleSmall:
            print(f"Error: 'selected_speaker' no es del tipo 'ThieleSmall' en --show_results_as_text()--.")

        try:
            params.ThieleSmall._calcular_parametros(selected_speaker)
            box = params.boxDimensions(selected_speaker)
            box.calcular_Vb_m3(selected_speaker)
            dims = box.calcular_dimensiones_plancha(selected_speaker)
            
        except AttributeError as e:
            print(f"Error al calcular dimensiones: {e}")
                    
        # END DEBUG -------------------------------------
        
        
        print(f"selected_speaker antes de llamar a text_results: {selected_speaker}")        
        text_results = (f"""
Espesor del material:
{user.wood_thickness_mm}mm
        
Dimensiones de tablas:
        
|2| Frontal-Trasera:
{dims[0][0]:.0f}mm x {dims[0][1]:.0f}mm
        
|2| Laterales:
{dims[1][0]:.0f}mm x {dims[1][1]:.0f}mm

|2| Superior-Inferior:
{dims[2][0]:.0f}mm x {dims[2][1]:.0f}mm""")
        return text_results
                            
class window:
    
    # COLORES    
    bg_color :str           = "#252525" # Gris claro
    highlight_color :str    = "#39BFBF" # Turquesa claro
    secondary_color :str    = "#2E5959" # Azul petroleo
    
    # BANNER
    header_title :str      = "BoxDesign Home (BETA by PulsosAudio)"

    # TAMAÑO
    size_ratio :int        = [4,3]
    size_factor :int       = 250
    size_as_str :str       = f"{int((size_ratio[0])*size_factor)}x{int((size_ratio[1])*size_factor)}"   
    
    # TIPOGRAFIA
    title_font :str         = ("Stencil Std")
    main_font :str          = ("Segoe UI")
        
    font_size_factor        :int = 1.2 
    main_font_size          :int = int(12 *font_size_factor)
    title_font_size         :int = int(26 *font_size_factor)
    secondary_font_size     :int = int(16 *font_size_factor)
    
    # MARGENES 
    std_padding_x           :int = 50
    std_padding_y           :int = 10
    
    # footer = tk.Frame(which_Window)
    # GENERAR ESE FOOTER !!!!!!!!!  
    
    def __init__(self):        
        # global header_title, size_as_list, size_as_str, main_font, title_font_size
        pass
                   
    def create_window(self,type:str,should_hide:bool):        
        if type == "main":
            window = tk.Tk()
        else:
            window = tk.Toplevel()        
                        
        window.title(self.header_title)
        window.geometry(self.size_as_str)
        window.configure(bg=self.bg_color)
        #window.wm_attributes('-transparent', 0.9)
        if should_hide:
            window.withdraw()        
        return window
    
    def close_and_next(prev_window: tk.Tk | tk.Toplevel, 
                       next_window: tk.Toplevel):
        global selected_speaker
        
        if not selected_speaker:
            print("Error: 'selected_speaker' no está configurado en --close_and_next(...)--.")            
        
        prev_window.withdraw()  # Ocultar la ventana actual
        from GUI import call_fullWidgets
        call_fullWidgets(next_window)
        next_window.deiconify()  # Mostrar la siguiente ventana
    
class default_values:

        qtc_var =       "0.707"
        thickness_var = "12"
        absorbing_var = 0
        ratio1_var =    "1"
        ratio2_var =    "1"
        ratio3_var =    "1"
        cutout_var =    "150"
        backPanel_var = "50"

