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
from matplotlib.backends.backend_pdf import PdfPages
import tkinter as tk
import ezdxf
import matplotlib
import math
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

#DXF_filename        :str = ut.DXF_filename
blueprint_folder    :str = "DXF_Blueprints"

margin_mm           :int = 65 #Placa Base Sierra Caladora

cutout_mm           :int = None # Inicialización. Se asigna en widgets/interactive.../create_saveSettings_button()/save_and_next
backPanel_mm        :int = None # Inicialización. Se asigna en widgets/interactive.../create_saveSettings_button()/save_and_next

class PaperSizes:
    def __init__(self):
        # Diccionario base: tipo de papel a medidas (ancho x alto en mm)
        self.paper_to_size = {
            "A0": (841, 1189),
            "A1": (594, 841),
            "A2": (420, 594),
            "A3": (297, 420),
            "A4": (210, 297),
            "A5": (148, 210),
            "A6": (105, 148),
            "A7": (74, 105),
            "A8": (52, 74),
            "A9": (37, 52),
            "A10": (26, 37),
        }

        # Crear el diccionario inverso: medidas a tipo de papel
        self.size_to_paper = {size: paper for paper, size in self.paper_to_size.items()}

    def get_size(self, paper_type):
        """Devuelve las medidas en mm dado el tipo de papel."""
        return self.paper_to_size.get(paper_type.upper(), "Tipo de papel no válido")

    def get_paper(self, size):
        """Devuelve el tipo de papel dado un tamaño en mm."""
        return self.size_to_paper.get(size, "Tamaño no corresponde a un tipo estándar")

    def find_min_paper(self, width, height):
        """
        Determina el tamaño de papel más pequeño que puede contener las dimensiones dadas.
        :param width: Ancho total en mm.
        :param height: Alto total en mm.
        :return: Tipo de papel mínimo que puede contenerlos.
        """
        for paper, (p_width, p_height) in sorted(self.paper_to_size.items(), key=lambda x: x[1]):
            if (width <= p_width and height <= p_height) or (width <= p_height and height <= p_width):
                return paper

        return "No hay un tamaño de papel estándar que lo contenga"


# Crear un archivo DXF
def new_DXF(filename, 
            save_dir,
            verbose: bool):
    # Crear el directorio si no existe
    os.makedirs(save_dir, exist_ok=True)

    # Crear el documento DXF
    doc = ezdxf.new("R2000", True, 4)  # "R2000" = AutoCAD 2000
    file_path = os.path.join(save_dir, filename)
    doc.saveas(file_path)

    if verbose:
        print(f"Archivo guardado en: {file_path}")
    return doc



# Función para visualizar el archivo DXF como un gráfico usando Matplotlib
def display_DXF_plot(file_path: str, 
                     output_image_path: str, 
                     verbose: bool,
                     paper_type:str,
                     paper_sizes: PaperSizes,
                     output_pdf_path: str = None):
    """
    Visualiza un archivo DXF como una imagen usando Matplotlib.

    :param file_path: Ruta del archivo DXF.
    :param output_image_path: Ruta de salida para la imagen.
    :param verbose: Si es True, imprime información adicional.
    """
    
    # Obtener las dimensiones del papel en mm y convertirlas a pulgadas
    paper_width_mm, paper_height_mm = paper_sizes.get_size(paper_type)
    paper_width_in = paper_width_mm / 25.4
    paper_height_in = paper_height_mm / 25.4

    
    # Cargar el archivo DXF
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    
    # Crear una figura para la visualización
    fig, ax = plt.subplots(figsize=(paper_width_in,
                                    paper_height_in))  # Tamaño A4 en pulgadas
    ax.set_aspect('equal')  # Mantener proporciones
    
    # Configurar los límites
    ax.axis('off')  # Ocultar los ejes
    
    # Inicializar límites de las coordenadas
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')


        # Verificar si las variables min_x y max_x se actualizaron
    if min_x == float('inf') or max_x == float('-inf'):
        min_x, max_x = 0, 100  # Valores predeterminados si no hay entidades
    if min_y == float('inf') or max_y == float('-inf'):
        min_y, max_y = 0, 100  # Valores predeterminados si no hay entidades



    # Configurar los ticks en intervalos de 5 mm
    x_ticks = range(int(min_x) - margin_mm, int(max_x) + margin_mm, 5)
    y_ticks = range(int(min_y) - margin_mm, int(max_y) + margin_mm, 5)
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)

    # Activar cuadrícula con separación de 5 mm
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')  # Cuadrícula

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
                # Validar si las variables de límites se actualizaron
        if min_x == float('inf') or max_x == float('-inf'):
            min_x, max_x = 0, 100  # Valores predeterminados para límites X
        if min_y == float('inf') or max_y == float('-inf'):
            min_y, max_y = 0, 100  # Valores predeterminados para límites Y


    # Establecer los límites del gráfico
    ax.set_xlim(min_x - margin_mm, max_x + margin_mm)  # Ampliamos los límites un poco para mayor claridad
    ax.set_ylim(min_y - margin_mm, max_y + margin_mm)
    
    # Agregar grid con separación de 5 mm
    ax.set_xticks(range(int(min_x) - margin_mm, int(max_x) + margin_mm, 5))
    ax.set_yticks(range(int(min_y) - margin_mm, int(max_y) + margin_mm, 5))
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)

    # Guardar la visualización como imagen
    fig.savefig(output_image_path, bbox_inches='tight', pad_inches=0.1)
    
    if output_pdf_path:
        with PdfPages(output_pdf_path) as pdf:
            pdf.savefig(fig, bbox_inches='tight', pad_inches=0.1)
        if verbose:
            print(f"PDF exportado con éxito: {output_pdf_path}")

    if verbose:
        print(f"DXF plot saved to {output_image_path}")

    plt.close(fig)

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
    Crea un archivo DXF con una serie de rectángulos con márgenes entre ellos,
    asegurando un diseño compacto en formato 2x3 o 3x2.

    :param file_path: Ruta donde se guardará el archivo DXF.
    :param rectangles: Lista de dimensiones [(ancho, alto), ...].
    :param margin_mm: Margen en milímetros entre los rectángulos.
    """
    # Número de columnas y filas para 2x3 o 3x2
    num_rectangles = len(rectangles)
    if num_rectangles <= 6:
        num_columns = 3
    else:
        num_columns = 3  # Ajusta según el caso si necesitas más filas
    num_rows = -(-num_rectangles // num_columns)  # Redondeo hacia arriba

    x_offset, y_offset = 0, 0  # Desplazamiento inicial
    max_row_height = 0         # Altura máxima de la fila actual
    row_counter = 0            # Contador para las filas

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

        # Verificar si el siguiente rectángulo no cabe en la fila actual
        if (i + 1) % num_columns == 0:
            x_offset = 0
            y_offset += max_row_height + margin_mm
            max_row_height = 0
            row_counter += 1

    # Guardar el archivo DXF
    save_dir = os.path.dirname(file_path)
    os.makedirs(save_dir, exist_ok=True)
    doc.saveas(file_path)
    
    if verbose: print(f"DXF file with rectangles saved to {file_path}")

    
def calculate_total_drawing_size(rectangles, margin=0):
    """
    Calcula el tamaño total del dibujo basado en los rectángulos dibujados.

    :param rectangles: Lista de rectángulos [(ancho, alto), ...].
    :param margin: Margen adicional alrededor del dibujo en mm.
    :return: (ancho_total, alto_total) en mm.
    """
    # Inicializar límites
    total_width = 0
    total_height = 0

    # Asumiendo disposición en arreglo 2x3 o similar
    row_width = 0
    row_height = 0

    for i, (width, height) in enumerate(rectangles):
        row_width += width + margin
        row_height = max(row_height, height)

        # Cada 3 rectángulos, pasa a la siguiente fila
        if (i + 1) % 3 == 0 or i == len(rectangles) - 1:
            total_width = max(total_width, row_width - margin)  # Remover último margen
            total_height += row_height + margin
            row_width = 0
            row_height = 0

    # Remover el margen adicional de la última fila
    total_height -= margin

    return total_width, total_height


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



def save_drawing_info(folder_path, file_name, drawing_data):
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)
    
    with open(file_path, "w") as file:
        # PRESENTACION
        file.write("==============================\n")
        file.write(f"BoxDesign Home\n")
        file.write(f"-- por Maximiliano Gómez y Pulsos Audio.\n")
        file.write("==============================\n\n")        
        
        
        file.write("==============================\n")        
        file.write("Datos del altavoz:\n")
        file.write("==============================\n\n")        

        #for key, value in drawing_data["speaker_data"].items():
        #    file.write(f"{key}: {value}\n")        
        
        file.write(f"Modelo: {drawing_data['speaker_data']['brand']} {drawing_data['speaker_data']['model']}\n")
        file.write(f"URL: {drawing_data['speaker_data']['url']}\n")
        file.write(f"Tipo: {drawing_data['speaker_data']['type']}\n")
        file.write(f"Diámetro (pulgadas): {drawing_data['speaker_data']['diameter_inch']}\n")
        
        #DIBUJO        
        file.write("\n==============================\n")
        file.write("Información del dibujo:\n")
        file.write("==============================\n\n")
        
        file.write(f"Tamaño total: {drawing_data['total_width']} mm x {drawing_data['total_height']} mm\n")
        file.write(f"Papel recomendado: {drawing_data['paper_type']}\n")
        file.write(f"Orientación: {drawing_data['orientation']}\n\n")        
        
        # CARPINTERIA
        file.write("==============================\n")

        file.write("Detalles adicionales:\n")
        file.write("==============================\n\n")

        file.write(f"Número de rectángulos: {drawing_data.get('rectangles_count', 'N/A')}\n")
        file.write(f"Margen utilizado: {drawing_data.get('margin', 'N/A')} mm\n")
        file.write(f"Espesor del material: {drawing_data.get('wood_thickness_mm', 'No especificado')} mm\n")
        #file.write(f"Dimensiones interiores: {drawing_data.get('areInteriorDims', 'No especificado')}\n")
        file.write(f"Uso de absorbente: {drawing_data.get('useAbsorbing', 'No especificado')}\n")
        #file.write(f"Var. cutout: {drawing_data.get('cutout_var', 'No especificado')}\n")
        #file.write(f"Var. BackPanel: {drawing_data.get('backPanel_var', 'No especificado')}\n")
        #file.write(f"Preferencia de Qtc: {drawing_data['qtc_choice']}\n")

        file.write("\n==============================\n")
        file.write("Dimensiones de las tablas:\n")
        file.write("==============================\n\n")
        
        dimensions = drawing_data["dimensions"]
        file.write(f"Frontal y Posterior: {dimensions['frontal_posterior'][0]} mm x {dimensions['frontal_posterior'][1]} mm\n")
        file.write(f"Laterales: {dimensions['lateral'][0]} mm x {dimensions['lateral'][1]} mm\n")
        file.write(f"Superior e Inferior: {dimensions['superior_inferior'][0]} mm x {dimensions['superior_inferior'][1]} mm\n")
    
    print(f"Información del dibujo guardada en: {file_path}")


def run_SKETCH(selected_speaker, save_dir):
    paper_sizes = PaperSizes()
    
    box = params.boxDimensions(selected_speaker)
    dims = box.calcular_dimensiones_plancha(selected_speaker)
    DXF_filepath = os.path.join(save_dir, ut.DXF_filename)
    TXT_filepath = os.path.join(save_dir, ut.TXT_filename)
    PNG_filepath = os.path.join(save_dir, ut.PNG_filename)
    PDF_filepath = os.path.join(save_dir, ut.PDF_filename)

    DXF_filename = ut.DXF_filename
    TXT_filename = ut.TXT_filename
    PNG_filename = ut.PNG_filename
    PDF_filename = ut.PDF_filename


    main_sketch = new_DXF(filename=DXF_filename, 
                          save_dir=save_dir,
                          verbose=False)

    
    
    if cutout_mm is None or backPanel_mm is None:
        raise ValueError("Las variables 'cutout_mm' y 'backPanel_mm' deben estar inicializadas antes de ejecutar run_SKETCH.")


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
                               DXF_filepath, 
                               rectangles_array,
                               margin_mm,
                               verbose=False)
    
    total_width, total_height = calculate_total_drawing_size(rectangles_array,margin_mm)

    print(f"Tamaño total del dibujo: {total_width} mm x {total_height} mm")

    # Determinar tamaño de papel mínimo
    paper_type = paper_sizes.find_min_paper(total_width, total_height)
    print(f"Tamaño de papel necesario: {paper_type}")

    output_image_path = f"{save_dir}/{PNG_filename}"
    output_pdf_path = f"{save_dir}/{PDF_filename}"
    add_cutout(msp, 
               rectangles_array, 
               cutout_mm=cutout_mm)
    
    print(cutout_mm)
    
    add_backPanel(  msp=msp,
                    rectangles=rectangles_array,
                    shape_type="circle",  # Puede ser 'rectangle', 'square', o 'circle'
                    shape_dimensions=[50],  # Cambiar según el tipo de figura
                    layer_name="BackPanel",
                    status_label=None  # Widget opcional para mensajes en GUI
                )
    
    



    # Strings nuevos:
    developer = "Desarrollador: PulsosAudio"
    brand = "Marca: BoxDesign Studio"
    acknowledgment = "Gracias por usar nuestro software"
    title = "Diseño Acústico Personalizado"

    # Qtc del usuario
    qtc_mapping = {
        1/math.sqrt(3): "Alta Definición (D2 Bessel)",
        1/math.sqrt(2): "Sonido Equilibrado (B2 Butterworth)",
        1.25: "Sonido Profundo (C2 Chebyshev)",
    }
    qtc_choice = qtc_mapping.get(user_settings.Qtc, "No especificado")

    # Datos del altavoz
    speaker_data = {
        "model": selected_speaker.speaker_model,
        "brand": selected_speaker.speaker_brand,
        "url": selected_speaker.URL,
        "type": selected_speaker.Type,
        "diameter_inch": selected_speaker.Diameter_inch,
    }

    # Consolidar toda la información existente
    drawing_data = {
        "title": title,
        "developer": developer,
        "brand": brand,
        "acknowledgment": acknowledgment,
        "total_width": total_width,
        "total_height": total_height,
        "paper_type": paper_type,
        "orientation": "horizontal" if total_width > total_height else "vertical",
        "rectangles_count": len([rectangles_array]),  # Si se conoce el conteo, cámbialo
        "margin": margin_mm,
        "wood_thickness_mm": user_settings.wood_thickness_mm,
        "areInteriorDims": user_settings.areInteriorDims,
        "useAbsorbing": user_settings.useAbsorbing,
        "cutout_var" : getattr(selected_speaker, "cutout_var", "No especificado"),
        "backPanel_var" : getattr(selected_speaker, "backPanel_var", "No especificado"),

        "qtc_choice": qtc_choice,
        "speaker_data": speaker_data,
        "dimensions": {
            "frontal_posterior": dims[0],
            "lateral": dims[1],
            "superior_inferior": dims[2]
        }
    }

    
    save_drawing_info(save_dir, TXT_filename, drawing_data)

    
    main_sketch.save()


    # Visualizar el archivo DXF como imagen
    output_image_path = f"{save_dir}/{PNG_filename}"
    
    display_DXF_plot(f"{save_dir}/{DXF_filename}", 
                     output_image_path,
                     verbose=False,
                     paper_type=paper_type,
                     paper_sizes=paper_sizes,
                     output_pdf_path=output_pdf_path)
    

# Calcular tamaño total del dibujo
def calculate_total_drawing_size(rectangles, margin=0):
    """
    Calcula el tamaño total del dibujo basado en los rectángulos dibujados.

    :param rectangles: Lista de rectángulos [(ancho, alto), ...].
    :param margin: Margen adicional alrededor del dibujo en mm.
    :return: (ancho_total, alto_total) en mm.
    """
    total_width = 0
    total_height = 0

    # Asumiendo disposición en arreglo 2x3
    row_width = 0
    row_height = 0

    for i, (width, height) in enumerate(rectangles):
        row_width += width + margin
        row_height = max(row_height, height)

        # Cada 3 rectángulos, pasa a la siguiente fila
        if (i + 1) % 3 == 0 or i == len(rectangles) - 1:
            total_width = max(total_width, row_width - margin)  # Remover último margen
            total_height += row_height + margin
            row_width = 0
            row_height = 0

    # Remover el margen adicional de la última fila
    total_height -= margin

    return total_width, total_height