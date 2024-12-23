import ezdxf as dxf
import sys
import utility as ut
import os
import params
import random
import string
from ezdxf.gfxattribs import GfxAttribs
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import ezdxf
import matplotlib
import data

matplotlib.use('Qt5Agg')  # Usar PyQt5 como backend
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
#from PyQt5.QtWidgets import QApplication, QMainWindow
import user_settings


# AVOID RUNNING
if __name__ == "__main__":
    os.system("clear")
    arg = "ERROR: Este código no está pensado para ejecutarse.\n"
    sys.exit(arg)    
# ========================================================


DXF_filename        :str = ut.DXF_filename
blueprint_folder    :str = "DXF_Blueprints"

margin_mm           :int = 65 #Placa Base Sierra Caladora

cutout_mm           :int = data.speaker.Diameter_mm

# Crear un archivo DXF
def new_DXF(filename, verbose: bool):
    # Crear el directorio si no existe
    os.makedirs(blueprint_folder, exist_ok=True)

    # Crear el documento DXF
    doc = ezdxf.new("R2000", True, 4)  # "R2000" = AutoCAD 2000
    file_path = os.path.join(blueprint_folder, filename)
    doc.saveas(file_path)

    if verbose:
        print(f"Archivo guardado en: {file_path}")
    return doc

main_sketch = new_DXF(filename=DXF_filename, verbose=False)


# Función para visualizar el archivo DXF como un gráfico usando Matplotlib
def display_DXF_plot(file_path: str, output_image_path: str, verbose: bool):
    """
    Visualiza un archivo DXF como una imagen usando Matplotlib.

    :param file_path: Ruta del archivo DXF.
    :param output_image_path: Ruta de salida para la imagen.
    :param verbose: Si es True, imprime información adicional.
    """
    # Cargar el archivo DXF
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    # Crear una figura para la visualización
    fig, ax = plt.subplots()
    ax.set_aspect('equal')  # Escala uniforme
    ax.axis('off')          # Sin ejes

    # Variables para el ajuste de límites
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')

    def process_entity(entity, offset=(0, 0)):
        """
        Procesa una entidad DXF y la dibuja en el gráfico.

        :param entity: Entidad DXF a procesar.
        :param offset: Desplazamiento (x, y) aplicado a las coordenadas.
        """
        nonlocal min_x, min_y, max_x, max_y

        if entity.dxftype() == 'LINE':  # Dibujar líneas
            start = entity.dxf.start
            end = entity.dxf.end
            ax.plot(
                [start.x + offset[0], end.x + offset[0]],
                [start.y + offset[1], end.y + offset[1]],
                color="black"
            )
            min_x = min(min_x, start.x + offset[0], end.x + offset[0])
            max_x = max(max_x, start.x + offset[0], end.x + offset[0])
            min_y = min(min_y, start.y + offset[1], end.y + offset[1])
            max_y = max(max_y, start.y + offset[1], end.y + offset[1])

        elif entity.dxftype() == 'CIRCLE':  # Dibujar círculos
            center = entity.dxf.center
            radius = entity.dxf.radius
            circle = plt.Circle(
                (center.x + offset[0], center.y + offset[1]),
                radius,
                color="black",
                fill=False
            )
            ax.add_artist(circle)
            min_x = min(min_x, center.x + offset[0] - radius)
            max_x = max(max_x, center.x + offset[0] + radius)
            min_y = min(min_y, center.y + offset[1] - radius)
            max_y = max(max_y, center.y + offset[1] + radius)

        elif entity.dxftype() in {'LWPOLYLINE', 'POLYLINE'}:  # Dibujar polilíneas
            points = list(entity.vertices())  # Convierte el generador a una lista
            if entity.closed:  # Si la polilínea está cerrada
                points.append(points[0])
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]
                ax.plot(
                    [p1[0] + offset[0], p2[0] + offset[0]],
                    [p1[1] + offset[1], p2[1] + offset[1]],
                    color="black"
                )
                min_x = min(min_x, p1[0] + offset[0], p2[0] + offset[0])
                max_x = max(max_x, p1[0] + offset[0], p2[0] + offset[0])
                min_y = min(min_y, p1[1] + offset[1], p2[1] + offset[1])
                max_y = max(max_y, p1[1] + offset[1], p2[1] + offset[1])

        elif entity.dxftype() == 'INSERT':  # Procesar bloques
            block_name = entity.dxf.name
            block = doc.blocks.get(block_name)
            insert_point = entity.dxf.insert  # Punto de inserción
            block_offset = (insert_point.x, insert_point.y)
            for block_entity in block:
                process_entity(block_entity, offset=block_offset)

    # Procesar todas las entidades en el espacio modelo
    for entity in msp:
        process_entity(entity)

    # Establecer los límites del gráfico
    ax.set_xlim(min_x - margin_mm, max_x + margin_mm)  # Ampliamos los límites un poco para mayor claridad
    ax.set_ylim(min_y - margin_mm, max_y + margin_mm)

    # Guardar la visualización como imagen
    fig.savefig(output_image_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    if verbose:
        print(f"DXF plot saved to {output_image_path}")



"""    
def draw_rectangles(msp, rectangles, margin_mm=margin_mm, atribs=None):
"""
"""
    Dibuja una serie de rectángulos en el espacio modelo con un margen especificado.

    :param msp: Espacio modelo de `ezdxf`
    :param rectangles: Lista de dimensiones [(ancho, alto), ...]
    :param margin: Margen entre rectángulos
    :param atribs: Atributos gráficos para los rectángulos
    """
"""
    x_offset, y_offset = 0, 0  # Desplazamiento inicial
    max_row_height = 0         # Altura máxima de la fila actual

    for width, height in rectangles:
        # Primer rectángulo
        p1 = (x_offset, y_offset)
        p2 = (x_offset + width, y_offset)
        p3 = (x_offset + width, y_offset + height)
        p4 = (x_offset, y_offset + height)

        # Dibujar el primer rectángulo como una polilínea cerrada
        msp.add_lwpolyline([p1, p2, p3, p4, p1], close=True, dxfattribs=atribs)

        # Desplazar para el segundo rectángulo
        x_offset += width + margin_mm  # Desplazar a la derecha

        # Segundo rectángulo (con las mismas dimensiones)
        p1 = (x_offset, y_offset)
        p2 = (x_offset + width, y_offset)
        p3 = (x_offset + width, y_offset + height)
        p4 = (x_offset, y_offset + height)

        # Dibujar el segundo rectángulo como una polilínea cerrada
        msp.add_lwpolyline([p1, p2, p3, p4, p1], close=True, dxfattribs=atribs)

        # Actualizar el desplazamiento horizontal
        x_offset += width + margin_mm
        max_row_height = max(max_row_height, height)

        # Si el siguiente par de rectángulos no cabe en la fila actual, saltar a la siguiente fila
        if x_offset + width > 500:  # Supongamos un límite de 500 unidades (ajustable)
            x_offset = 0
            y_offset += max_row_height + margin_mm
            max_row_height = 0

"""

def create_rectangle_block(doc, block_name, width, height):
    """
    Crea un bloque con un rectángulo de dimensiones dadas.

    :param doc: Documento DXF de `ezdxf`.
    :param block_name: Nombre del bloque.
    :param width: Ancho del rectángulo.
    :param height: Alto del rectángulo.
    :return: Bloque creado.
    """
    # Crear o sobrescribir un bloque
    block = doc.blocks.new(name=block_name)

    # Coordenadas del rectángulo
    p1 = (0, 0)
    p2 = (width, 0)
    p3 = (width, height)
    p4 = (0, height)

    # Agregar una polilínea cerrada al bloque
    block.add_lwpolyline([p1, p2, p3, p4, p1], close=True)

    return block


def draw_rectangles_as_blocks(msp, doc, rectangles, margin_mm):
    """
    Crea y dibuja rectángulos como bloques en el espacio modelo.

    :param msp: Espacio modelo de `ezdxf`.
    :param doc: Documento DXF de `ezdxf`.
    :param rectangles: Lista de dimensiones [(ancho, alto), ...].
    :param margin_mm: Margen entre rectángulos.
    """
    x_offset, y_offset = 0, 0  # Desplazamiento inicial
    max_row_height = 0         # Altura máxima de la fila actual
    block_counter = 1          # Contador para nombres de bloques únicos

    for width, height in rectangles:
        # Crear un bloque único para el rectángulo
        block_name = f"RectBlock_{block_counter}"
        create_rectangle_block(doc, block_name, width, height)

        # Insertar el bloque en el espacio modelo
        msp.add_blockref(block_name, (x_offset, y_offset))

        # Actualizar el desplazamiento horizontal
        x_offset += width + margin_mm
        max_row_height = max(max_row_height, height)

        # Si el siguiente rectángulo no cabe en la fila actual, saltar a la siguiente fila
        if x_offset + width > 500:  # Supongamos un límite de 500 unidades (ajustable)
            x_offset = 0
            y_offset += max_row_height + margin_mm
            max_row_height = 0

        block_counter += 1  # Incrementar el contador para el próximo bloque


def create_dxf_with_rectangles(doc, msp, file_path, rectangles, margin_mm, verbose):
    """
    Crea un archivo DXF con una serie de rectángulos con márgenes entre ellos.

    :param file_path: Ruta donde se guardará el archivo DXF.
    :param rectangles: Lista de dimensiones [(ancho, alto), ...].
    :param margin_mm: Margen en milímetros entre los rectángulos.
    """
    """"
    # Crear un nuevo documento DXF
    doc = ezdxf.new()
    msp = doc.modelspace()
    """
    
    x_offset, y_offset = 0, 0  # Desplazamiento inicial
    max_row_height = 0         # Altura máxima de la fila actual

    for i, (width, height) in enumerate(rectangles):
        # Coordenadas del rectángulo actual
        p1 = (x_offset, y_offset)
        p2 = (x_offset + width, y_offset)
        p3 = (x_offset + width, y_offset + height)
        p4 = (x_offset, y_offset + height)

        # Dibujar el rectángulo como una polilínea cerrada
        msp.add_lwpolyline([p1, p2, p3, p4, p1], close=True, dxfattribs={"layer": "CORTE Caras"})
        
        # Actualizar el desplazamiento horizontal
        x_offset += width + margin_mm
        max_row_height = max(max_row_height, height)

        # Si el siguiente rectángulo no cabe en la fila actual, saltar a la siguiente fila
        if x_offset + width > 500:  # Supongamos un límite de 500 unidades (ajustable)
            x_offset = 0
            y_offset += max_row_height + margin_mm
            max_row_height = 0

    # Guardar el archivo DXF
    doc.saveas(file_path)
    
    if verbose: print(f"DXF file with rectangles saved to {file_path}")

def run_SKETCH():
    # print(main_box.calcular_dimensiones_plancha())
    #main_sketch.layers.add("ELEMENTOS",color=3)


    msp = main_sketch.modelspace()
    atribs = GfxAttribs(layer="MyLayer")


    # point = msp.add_point((10,10),dxfattribs=atribs)
    circle = msp.add_circle((5,15),radius=1, dxfattribs=atribs)

    # CORREGIR EL LLAMADO DEL ALTAVOZ PRIMERO
    rectangles_array = params.boxDimensions.calcular_dimensiones_plancha(data.thiele_small)
    rectangles_array = rectangles_array[:] = [item for item in rectangles_array for _ in range(2)]



    create_dxf_with_rectangles(main_sketch,msp,f"{blueprint_folder}/{DXF_filename}", rectangles_array,margin_mm,verbose=False)

    main_sketch.save()


    # Visualizar el archivo DXF como imagen
    output_image_path = f"{blueprint_folder}/{ut.PNG_filename}"
    display_DXF_plot(f"{blueprint_folder}/{DXF_filename}", output_image_path,verbose=False)
    
""""
def add_cutout(prueba1,prueba2):
        


    center_x = (p1[0] + p3[0]) / 2
    center_y = (p1[1] + p3[1]) / 2
    # Dibujar un círculo en el centro del primer rectángulo
    radius = cutout_mm  # Ajusta el radio del círculo según sea necesario
    msp.add_circle((center_x, center_y), radius, dxfattribs={"layer": "CírculoCentro"})
"""
