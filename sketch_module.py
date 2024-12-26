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

# selected_speaker    = None

DXF_filename        :str = ut.DXF_filename
blueprint_folder    :str = "DXF_Blueprints"

margin_mm           :int = 65 #Placa Base Sierra Caladora

cutout_mm           :int = None # Inicialización. Se asigna en widgets/interactive.../create_saveSettings_button()/save_and_next
backPanel_mm        :int = None # Inicialización. Se asigna en widgets/interactive.../create_saveSettings_button()/save_and_next

# Crear un archivo DXF
def new_DXF(filename, 
            verbose: bool):
    # Crear el directorio si no existe
    os.makedirs(blueprint_folder, exist_ok=True)

    # Crear el documento DXF
    doc = ezdxf.new("R2000", True, 4)  # "R2000" = AutoCAD 2000
    file_path = os.path.join(blueprint_folder, filename)
    doc.saveas(file_path)

    if verbose:
        print(f"Archivo guardado en: {file_path}")
    return doc



# Función para visualizar el archivo DXF como un gráfico usando Matplotlib
def display_DXF_plot(file_path: str, 
                     output_image_path: str, 
                     verbose: bool):
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


def create_rectangle_block(doc, 
                           block_name, 
                           width, 
                           height):
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


def draw_rectangles_as_blocks(msp, 
                              doc, 
                              rectangles, 
                              margin_mm):
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
        if x_offset + width > 297:  # Supongamos un límite de 500 unidades (ajustable)
            x_offset = 0
            y_offset += max_row_height + margin_mm
            max_row_height = 0

        block_counter += 1  # Incrementar el contador para el próximo bloque


def create_dxf_with_rectangles(doc, 
                               msp, 
                               file_path, 
                               rectangles, 
                               margin_mm, 
                               verbose):
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

def add_cutout( msp, 
                rectangles, 
                cutout_mm:int, 
                layer_name="CírculoCentro"):
    """
    Dibuja un círculo en el centro del primer rectángulo basado en el diámetro especificado.
    
    :param msp: Espacio modelo de `ezdxf`.
    :param rectangles: Lista de dimensiones [(ancho, alto), ...].
    :param cutout_mm: Diámetro del círculo.
    :param layer_name: Nombre de la capa para el círculo.
    """
    if not rectangles:
        print("Error: La lista de rectángulos está vacía.")
        return

    # Tomar las dimensiones del primer rectángulo
    width, height = rectangles[0]
    
    max_diameter_width  :int = width - 4 * user_settings.wood_thickness_mm
    max_diameter_height :int = height - 4 * user_settings.wood_thickness_mm

    
    if cutout_mm >= max_diameter_width or cutout_mm >= max_diameter_height:
        print(
            f"{user_settings.wood_thickness_mm}\n"
            f"Error: El diámetro del círculo ({cutout_mm} mm) excede los límites permitidos.\n"
            f"Dimensiones del rectángulo: ancho={width} mm, alto={height} mm.\n"
            f"Límites máximos: diámetro ancho={max_diameter_width} mm, diámetro alto={max_diameter_height} mm.")  
        return


    # Calcular el centro del rectángulo
    center_x = width / 2
    center_y = height / 2

    # Calcular el radio del círculo
    radius = cutout_mm / 2

    # Dibujar el círculo en el centro del rectángulo
    msp.add_circle((center_x, center_y), radius, dxfattribs={"layer": layer_name})

    print(f"Círculo dibujado en el centro del primer rectángulo: Centro=({center_x}, {center_y}), Radio={radius}")

def add_backPanel(msp, 
                  rectangles, 
                  shape_type, 
                  shape_dimensions, 
                  layer_name="BackPanel",
                  status_label=None):
    """
    Agrega una figura (rectángulo, cuadrado o círculo) al centro del segundo rectángulo.

    :param msp: Espacio modelo de `ezdxf`.
    :param rectangles: Lista de dimensiones [(ancho, alto), ...].
    :param shape_type: Tipo de figura a dibujar ('rectangle', 'square', 'circle').
    :param shape_dimensions: Dimensiones de la figura (para 'rectangle' [width, height], 
                              para 'square' [side], para 'circle' [diameter]).
    :param layer_name: Nombre de la capa para la figura.
    :param status_label: (Opcional) Widget de tkinter para mostrar mensajes en la ventana.
    """
    if len(rectangles) < 2:
        message = "Error: No hay suficientes rectángulos en la lista para procesar el segundo."
        print(message)
        if status_label:
            status_label.config(text=message)
        return

    # Obtener las dimensiones del segundo rectángulo
    width, height = rectangles[1]

    # Calcular el centro del segundo rectángulo considerando el desplazamiento acumulado
    x_offset = sum(rect[0] + margin_mm for rect in rectangles[:1])  # Acumular desplazamientos
    y_offset = 0  # No hay desplazamiento vertical acumulado en este caso

    center_x = x_offset + width / 2
    center_y = y_offset + height / 2

    # Verificar y dibujar la figura correspondiente
    if shape_type == "rectangle" and len(shape_dimensions) == 2:
        rect_width, rect_height = shape_dimensions
        p1 = (center_x - rect_width / 2, center_y - rect_height / 2)
        p2 = (center_x + rect_width / 2, center_y - rect_height / 2)
        p3 = (center_x + rect_width / 2, center_y + rect_height / 2)
        p4 = (center_x - rect_width / 2, center_y + rect_height / 2)
        msp.add_lwpolyline([p1, p2, p3, p4, p1], close=True, dxfattribs={"layer": layer_name})
        message = f"Rectángulo agregado al centro del segundo rectángulo: {p1}, {p2}, {p3}, {p4}"
        print(message)
        if status_label:
            status_label.config(text=message)

    elif shape_type == "square" and len(shape_dimensions) == 1:
        side = shape_dimensions[0]
        p1 = (center_x - side / 2, center_y - side / 2)
        p2 = (center_x + side / 2, center_y - side / 2)
        p3 = (center_x + side / 2, center_y + side / 2)
        p4 = (center_x - side / 2, center_y + side / 2)
        msp.add_lwpolyline([p1, p2, p3, p4, p1], close=True, dxfattribs={"layer": layer_name})
        message = f"Cuadrado agregado al centro del segundo rectángulo: {p1}, {p2}, {p3}, {p4}"
        print(message)
        if status_label:
            status_label.config(text=message)

    elif shape_type == "circle" and len(shape_dimensions) == 1:
        radius = shape_dimensions[0] / 2
        msp.add_circle((center_x, center_y), radius, dxfattribs={"layer": layer_name})
        message = f"Círculo agregado al centro del segundo rectángulo: Centro=({center_x}, {center_y}), Radio={radius}"
        print(message)
        if status_label:
            status_label.config(text=message)

    else:
        # Si el tipo de figura no es válido
        message = "Forma omitida: tipo no definido o inválido."
        print(message)
        if status_label:
            status_label.config(text=message)

def run_SKETCH(selected_speaker):
    #global selected_speaker
    box = params.boxDimensions(selected_speaker)
    main_sketch = new_DXF(filename=DXF_filename, 
                          verbose=False)

    if not isinstance(selected_speaker, params.ThieleSmall):
        print("Error: 'selected_speaker' no es una instancia de ThieleSmall.")
                
    # print(main_box.calcular_dimensiones_plancha())
    #main_sketch.layers.add("ELEMENTOS",color=3)


    msp = main_sketch.modelspace()
    atribs = GfxAttribs(layer="MyLayer")


    rectangles_array = box.calcular_dimensiones_plancha(selected_speaker)
    rectangles_array = rectangles_array[:] = [item for item in rectangles_array for _ in range(2)]



    create_dxf_with_rectangles(main_sketch,
                               msp,
                               f"{blueprint_folder}/{DXF_filename}", 
                               rectangles_array,
                               margin_mm,
                               verbose=False)

    add_cutout(msp, 
               rectangles_array, 
               cutout_mm)
    
    print(cutout_mm)
    
    add_backPanel(  msp=msp,
                    rectangles=rectangles_array,
                    shape_type="circle",  # Puede ser 'rectangle', 'square', o 'circle'
                    shape_dimensions=[50],  # Cambiar según el tipo de figura
                    layer_name="BackPanel",
                    status_label=None  # Widget opcional para mensajes en GUI
                )
    
    main_sketch.save()


    # Visualizar el archivo DXF como imagen
    output_image_path = f"{blueprint_folder}/{ut.PNG_filename}"
    display_DXF_plot(f"{blueprint_folder}/{DXF_filename}", 
                     output_image_path,verbose=False)
    
""""
def add_cutout(prueba1,prueba2):
        


    center_x = (p1[0] + p3[0]) / 2
    center_y = (p1[1] + p3[1]) / 2
    # Dibujar un círculo en el centro del primer rectángulo
    radius = cutout_mm  # Ajusta el radio del círculo según sea necesario
    msp.add_circle((center_x, center_y), radius, dxfattribs={"layer": "CírculoCentro"})
"""
