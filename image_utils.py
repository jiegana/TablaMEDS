import cv2
import numpy as np
from PIL import Image

def limpiar_imagen_para_ocr(imagen_pil):
    """
    Versión minimalista: Ajuste de contraste básico sin filtros agresivos.
    Prepara la imagen suavemente para dejar que el OCR moderno haga el trabajo duro.
    """
    # 1. Convertir de PIL a formato OpenCV
    img_array = np.array(imagen_pil)
    
    if len(img_array.shape) == 3 and img_array.shape[2] == 4:
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
    else:
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    # 2. Convertir a Escala de Grises
    imagen_gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # 3. Ajuste de Contraste y Brillo Simple
    # alpha=1.2 aumenta levemente el contraste (las diferencias entre claros y oscuros)
    # beta=10 sube un poquito el brillo general
    imagen_mejorada = cv2.convertScaleAbs(imagen_gris, alpha=1.2, beta=10)

    # 4. Convertir de vuelta a formato PIL
    imagen_lista = Image.fromarray(imagen_mejorada)

    return imagen_lista