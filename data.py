import utility as ut
import numpy as np
import matplotlib.pyplot as plot
import os
import params as p

#import sketch_module as sk
from ezdxf.gfxattribs import GfxAttribs
import tkinter as tk
import csv
import pandas as pd
import re
import logging

os.system("clear"); print("-> Iniciando el código...\n")
main_watch = ut.myTime.start()

LSDB_TSV_path = "LoudspeakerDatabase_v2.tsv"

df = pd.read_csv(LSDB_TSV_path, delimiter="\t")

"""
marca = "Eighteen Sound"
modelo = "10MB600"

indices = df.index[(df["Brand"] == marca) & (df["Model"] == modelo)].tolist()

if indices:
    # Obtener la fila como un diccionario
    row = df.loc[indices[0]]

"""

speakers = []

# Iterar sobre las filas del DataFrame
for index, row in df.iterrows():
    # Crear una instancia de ThieleSmall con todos los datos necesarios
    speaker = p.ThieleSmall(
        speaker_model=row['Model'],
        speaker_brand=row['Brand'],
        URL=row['URL'],
        Type=row['Type'],
        Diameter_inch=row['Nominal diameter [″]'],
        Diameter_mm=row['Nominal diameter [mm]'],
        SPL_dB=row['SPL 1W [dB]'],
        Fs_Hz=row['fs [Hz]'],
        Qms=row['Qms'],
        Qes=row['Qes'],
        Qts=row['Qts'],
        Xmax_mm=row['xmax [mm]'],
        Power_W=row['Power [W]'],
        Pmax_W=row['Pmax [W]'],
        Z_ohm=row['Z [Ω]'],
        Re_ohm=row['Re [Ω]'],
        Le_mH=row['Le [mH]'],
        Sd_cm2=row['Sd [cm²]'],
        Mms_g=row['Mms [g]'],
        Mmd_g=row['Mmd [g]'],
        Cms_uN=row['Cms [µm/N]'],
        Vas_L=row['Vas [L]'],
        Rms=row['Rms [N·s/m]']
    )

    # Asignar un ID único basado en el índice de la fila
    speaker.ID = index


    # Función para imprimir información de cada altavoz, si se desea
    def print_some_speaker_data(should_print):
        if should_print:
            print(f"ID: {speaker.ID},\t Marca: {speaker.speaker_brand},\t Modelo: {speaker.speaker_model}")

    # Llamar a la función de impresión con False para no imprimir por defecto
    print_some_speaker_data(False)

    # Agregar el altavoz a la lista
    speakers.append(speaker)

# Confirmar la cantidad de altavoces agregados
print(f"Se han agregado {len(speakers)} altavoces a la lista.")


# Crear una instancia de la clase ThieleSmall para almacenar los datos del altavoz

# Función para asignar un altavoz seleccionado a la clase ThieleSmall ajustada para no depender de eventos
def assign_speaker(listbox:tk.Listbox, 
                   label_seleccion:tk.StringVar, 
                   df:pd.DataFrame,
                   verbose:bool):
    
    global thiele_small
    thiele_small = None

    try:
        # Obtener el altavoz seleccionado del Listbox
        selection_index = listbox.curselection()
        if selection_index:
            selected_item = listbox.get(selection_index)
            # label_seleccion.set(f"Altavoz seleccionado: {selection_index}")

            # Dividir correctamente el texto
            brand_model, _type = selected_item.split(" - ")
            brand, model = brand_model.split(" ", 1)

            # Buscar el altavoz en el DataFrame
            speaker_data = df.iloc[index]

            # Crear una instancia de ThieleSmall con todos los datos
            thiele_small = p.ThieleSmall(
                speaker_model=model,
                speaker_brand=brand,
                URL=speaker_data['URL'],
                Type=speaker_data['Type'],
                Diameter_inch=speaker_data['Nominal diameter [″]'],
                Diameter_mm=speaker_data['Nominal diameter [mm]'],
                SPL_dB=speaker_data['SPL 1W [dB]'],
                Fs_Hz=speaker_data['fs [Hz]'],
                Qms=speaker_data['Qms'],
                Qes=speaker_data['Qes'],
                Qts=speaker_data['Qts'],
                Xmax_mm=speaker_data['xmax [mm]'],
                Power_W=speaker_data['Power [W]'],
                Pmax_W=speaker_data['Pmax [W]'],
                Z_ohm=speaker_data['Z [Ω]'],
                Re_ohm=speaker_data['Re [Ω]'],
                Le_mH=speaker_data['Le [mH]'],
                Sd_cm2=speaker_data['Sd [cm²]'],
                Mms_g=speaker_data['Mms [g]'],
                Mmd_g=speaker_data['Mmd [g]'],
                Cms_uN=speaker_data['Cms [µm/N]'],
                Vas_L=speaker_data['Vas [L]'],
                Rms=speaker_data['Rms [N·s/m]']
            )
            if verbose:
            # Mostrar la información del altavoz
                thiele_small.display_spkr_parameters()
                thiele_small.display_user_settings()
                thiele_small.display_calc_settings()
            return thiele_small
        else:
            label_seleccion.set("No se ha seleccionado ningún altavoz.")
    except IndexError:
        label_seleccion.set("No se ha encontrado el altavoz en la base de datos.")
    except KeyError as e:
        label_seleccion.set(f"Columna no encontrada: {e}")
    except ValueError:
        label_seleccion.set("Error al obtener los datos del altavoz.")
        
    return thiele_small