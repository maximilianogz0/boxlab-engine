import tkinter as tk
from tkinter import ttk
from data import df, assign_speaker
#import data 
import user_settings as user
import params

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
        thickness_label = tk.Label(which_Window, text="Grosor de madera (mm):")
        thickness_label.pack(pady=5)
        thickness_spinbox = ttk.Spinbox(which_Window, from_=10, to=40, increment=1, textvariable=thickness_var, width=10)
        thickness_spinbox.pack()

    @staticmethod
    def create_absorbing_checkbox(which_Window, absorbing_var):
        absorbing_checkbox = tk.Checkbutton(which_Window, text="Usar absorbente acústico", variable=absorbing_var)
        absorbing_checkbox.select()
        absorbing_checkbox.pack(pady=10)

    @staticmethod
    def create_ratio_section(which_Window, ratio1_var, ratio2_var, ratio3_var):
        ratio_label = tk.Label(which_Window, text="Relación de aspecto\n")
        ratio_label.pack(pady=5)
        ratio_frame = tk.Frame(which_Window)
        ratio_frame.pack()

        ratio1_entry = tk.Entry(ratio_frame, textvariable=ratio1_var, width=5, justify="center")
        ratio1_entry.pack(side="left")
        tk.Label(ratio_frame, text=" : ").pack(side="left")
        ratio2_entry = tk.Entry(ratio_frame, textvariable=ratio2_var, width=5, justify="center")
        ratio2_entry.pack(side="left")
        tk.Label(ratio_frame, text=" : ").pack(side="left")
        ratio3_entry = tk.Entry(ratio_frame, textvariable=ratio3_var, width=5, justify="center")
        ratio3_entry.pack(side="left")

    @staticmethod
    def create_saveSettings_button(which_Window, next_Window, 
                                   qtc_var, 
                                   thickness_var, 
                                   absorbing_var, 
                                   ratio1_var, 
                                   ratio2_var, 
                                   ratio3_var):

        prev_Window = which_Window
        
        def save_and_next():
            # global qtc_var, thickness_var, absorbing_var, ratio1_var, ratio2_var, ratio3_var
            user.Qtc = float(qtc_var.get())
            user.wood_thickness_mm = int(thickness_var.get())
            user.useAbsorbing = bool(absorbing_var.get())
            user.ratioDims = (float(ratio1_var.get()), float(ratio2_var.get()), float(ratio3_var.get()))    
            
            window.close_and_next(prev_Window, next_Window) # en este metodo ya se llaman los widgets de la siguiente ventana
        
        saveSettings_button = tk.Button(which_Window, 
                                        text="Siguiente", 
                                        command=save_and_next)
        saveSettings_button.pack(pady=20)
        """
        user.Qtc = float(qtc_var.get())
        user.wood_thickness_mm = int(thickness_var.get())
        user.useAbsorbing = bool(absorbing_var.get())
        user.ratioDims = (float(ratio1_var.get()), float(default_values.ratio2_var.get()), float(default_values.ratio3_var.get()))
        saveSettings_button.pack(pady=20)
        """
        
        
    @staticmethod    
    def create_qtc_section(which_Window, qtc_var):
        qtc_label = tk.Label(which_Window, text="Qtc (ajuste B4):")
        qtc_label.pack(pady=5)
        qtc_options = ["0.707", "0.9", "1.1", "1.4"]
        qtc_dropdown = ttk.Combobox(which_Window, textvariable=qtc_var, values=qtc_options, state="readonly")
        qtc_dropdown.pack()

    @staticmethod        
    def create_title(which_Window, title):
        title_label = tk.Label(which_Window, text=title)
        title_label.pack(pady=10)
        
    @staticmethod
    def create_button(which_Window, text, command):
        button = tk.Button(which_Window, text=text, command=command)
        button.pack(pady=10)
            
    @staticmethod            
    def create_listbox(which_Window):
        listbox = tk.Listbox(which_Window, width=50)
        listbox.pack(pady=10)
        return listbox
    
    @staticmethod            
    def create_speaker_listbox(which_Window,listbox):
        listbox = interactive_widgets.create_listbox(which_Window)
        for index, row in df.iterrows():
            listbox.insert(tk.END, f"{row['Brand']} {row['Model']} - ({row['Type']})")
        return listbox
            
            
    # Botón para asignar el altavoz
    @staticmethod
    def create_assignSpeaker_button(which_Window, 
                             listbox, 
                             df, 
                             next_Window,
                             call_fullWidgets):
        
        prev_Window = which_Window
        label_selection = tk.StringVar()

        # Crear un Label para mostrar la selección
        label_archivo = tk.Label(which_Window, textvariable=label_selection)
        label_archivo.pack(pady=10)
                        
        def on_button_click(prev_Window, next_Window):
            global selected_speaker 
            print("Ejecutando on_button_click...")
           
            selected_speaker = assign_speaker(listbox, 
                                              label_selection, 
                                              df,
                                              prev_Window,
                                              next_Window, 
                                              verbose=False)
            
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
        button.pack(pady=10)    
        return button
            
        
class displays_and_labels:

    def create_label(which_Window, text):
        label = tk.Label(which_Window, text=text)
        label.pack(pady=10)
    pass

    def create_selected_speaker_label(which_Window):
            label_seleccion = tk.StringVar()
            label_archivo = tk.Label(which_Window, 
                                    textvariable=label_seleccion)
            label_archivo.pack(pady=10)
    pass

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
        
        {selected_speaker.speaker_brand} {selected_speaker.speaker_model} 
        
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
                        
    
class window:
    
    def __init__(self):        
        #global header_title, size_as_list, size_as_str
        
        self.header_title :str = "BoxDesign Home (BETA by PulsosAudio)"
        self.size_as_list :int = [650,500]
        self.size_as_str :str = f"{(self.size_as_list[0])}x{self.size_as_list[1]}"                
    
    def create_window(self,type:str,should_hide:bool):        
        if type == "main":
            window = tk.Tk()
        else:
            window = tk.Toplevel()        
                        
        window.title(self.header_title)
        window.geometry(self.size_as_str)
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
    # Variables ajustables
    def __init__(self):
        self.qtc_var =      "0.707"
        self.thickness_var = "12"
        self.absorbing_var = 0
        self.ratio1_var =    "1"
        self.ratio2_var =    "1"
        self.ratio3_var =    "1"
        
