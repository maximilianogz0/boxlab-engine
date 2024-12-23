import subprocess
import sys
import importlib
import time
import os
import random
import string
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import pandas as pd
import ezdxf
import re

# AVOID RUNNING THIS CODE
if __name__ == "__main__":
    os.system("clear")
    arg = "ERROR: Este código no está pensado para ejecutarse.\n"
    sys.exit(arg)    
# ========================================================

# ABOUT LIBRARIES

libs_required = [
                 "ezdxf",
                 "matplotlib",
                 "numpy",
                 "matplotlib",
                 "tk",
                 "trash", 
                 "PyQt5",
                 "PySimpleGUI",
                 "pandas"
                 ]

def install_libs(libraries_list, verbose=True):
    
    for each_lib in libraries_list:
        install_single_lib(each_lib, verbose)


def install_single_lib(nombre_libreria, verbose=True):
    
    try:
        # Verifica si la librería ya está instalada
        importlib.import_module(nombre_libreria)
        if verbose:
            print(f"La librería '{nombre_libreria}' ya está instalada.")
        return True
    except ModuleNotFoundError:
        if verbose:
            print(f"La librería '{nombre_libreria}' no está instalada. Intentando instalar...")

    # Intenta instalar la librería si no está instalada
    try:
        comando = [sys.executable, "-m", "pip", "install", nombre_libreria]
        subprocess.check_call(comando, stdout=subprocess.DEVNULL if not verbose else None)
        if verbose:
            print(f"La librería '{nombre_libreria}' se instaló correctamente.")
        return True
    except subprocess.CalledProcessError:
        if verbose:
            print(f"Hubo un error al intentar instalar la librería '{nombre_libreria}'.")
        return False
    except Exception as e:
        if verbose:
            print(f"Error inesperado: {e}")
        return False

# SOME FUNCTIONS

fixed_randomcase = ''.join(random.choices(string.ascii_lowercase, k=5))
def setFileName() -> str:
    pre = "DXF_random_"
    return (pre + fixed_randomcase)

DXF_filename    :str = f"DXF_random_{fixed_randomcase}.dxf"
PNG_filename    :str = f"PNG_random_{fixed_randomcase}.png"

def open_folder(main_window, listbox, label_seleccion, extension):
    """
    Abrir el cuadro de diálogo para seleccionar una carpeta y cargar los archivos con la extensión especificada.
    """
    carpeta = tk.filedialog.askdirectory(parent=main_window, title="Seleccionar carpeta")
    if carpeta:
        archivos = os.listdir(carpeta)  # Obtener archivos de la carpeta seleccionada
        listbox.delete(0, 'end')       # Limpiar el Listbox
        archivos_filtrados = [
            archivo for archivo in archivos if archivo.endswith(extension)
        ]  # Filtrar por extensión
        if archivos_filtrados:
            for archivo in archivos_filtrados:
                listbox.insert('end', archivo)  # Agregar cada archivo al Listbox
            label_seleccion.set(f"Archivos con extensión {extension} cargados.")
        else:
            label_seleccion.set(f"No se encontraron archivos con extensión {extension}.")

def select_file(event, listbox, label_seleccion):
    """
    Mostrar el archivo seleccionado del Listbox en la etiqueta.
    """
    try:
        indice = listbox.curselection()  # Obtener índice del archivo seleccionado
        archivo_seleccionado = listbox.get(indice)  # Obtener el nombre del archivo
        label_seleccion.set(f"Archivo seleccionado: {archivo_seleccionado}")
    except IndexError:
        label_seleccion.set("No se ha seleccionado ningún archivo.")


def dims_2_str(dims):
    return f"{dims[0]}x{dims[1]}"

# ========================================================    
# CLASSES
    
class myTime:
    def start():
        """
        Inicia el temporizador y devuelve el momento en que se llamó.
        """
        return time.time()
    
    def stop(start):
        duracion = time.time() - start
        print(f"Duración del código: {1000*duracion:.2f} milisegundos.")
        print("El código ha finalizado. :)\n")

# PROBANDO =================================================================

# Ruta al archivo TSV
LSDB_TSV_path = "LoudspeakerDatabase.tsv"


def open_tsv_file(main_window, listbox, label_seleccion):
    """
    Abrir el archivo TSV con datos de los altavoces y cargar los datos en el Listbox.
    """
    try:
        # Leer los datos del archivo TSV
        df = pd.read_csv(LSDB_TSV_path, delimiter="\t")
        
        # Limpiar el Listbox
        listbox.delete(0, tk.END)
        
        # Agregar marcas y modelos al Listbox
        for index, row in df.iterrows():
            model_modificado = eliminar_omega(row['Model'])  # Se agregó esta línea para eliminar omega del modelo
            listbox.insert(tk.END, f"{row['Brand']} {model_modificado}")  # Se usa model_modificado aquí
        
        label_seleccion.set(f"Base de datos cargada ({len(df)} altavoces).")
        return df
    except FileNotFoundError:
        label_seleccion.set(f"Error: El archivo {LSDB_TSV_path} no se encontró.")
        return None

def select_file(event, listbox, label_seleccion, df):
    """
    Mostrar el altavoz seleccionado en el Listbox y obtener el índice del DataFrame.
    """
    try:
        # Obtener el índice del altavoz seleccionado
        selection_index = listbox.curselection()
        if selection_index:
            selected_item = listbox.get(selection_index)
            label_seleccion.set(f"Altavoz seleccionado: {selected_item}")

            # Dividir la cadena en base al espacio, pero solo en el primer espacio
            parts = selected_item.rsplit(" ", 1)  # Dividir desde la derecha en el primer espacio
            brand = parts[0]
            model = eliminar_omega(parts[1])  # Se agregó esta línea para eliminar omega del modelo seleccionado
            
            # Buscar el índice en el DataFrame
            index = df.index[(df['Brand'] == brand) & (df['Model'] == model)].tolist()[0]
            print(f"Índice en el DataFrame: {index}")
    except IndexError:
        label_seleccion.set("No se ha seleccionado ningún altavoz.")
    except ValueError:
        label_seleccion.set("Error al desempaquetar el nombre del altavoz.")
        
        
        
def eliminar_omega(texto):
    # Usar una expresión regular para eliminar números seguidos de 'Ω'
    texto_modificado = re.sub(r'\d+(\.\d+)?\s*Ω', '', texto)
    return texto_modificado

        
        
        
