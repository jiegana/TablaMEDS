from PIL import Image, ImageDraw, ImageFont
import pandas as pd

def wrap_text(text, font, max_width, draw):
    """
    Función inteligente que corta el texto en varias líneas 
    si supera el ancho de la columna, evitando que se ampute.
    """
    words = str(text).split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def crear_imagen_tabla_limpia(df):
    """
    Genera una Pizarra Digital donde cada Pabellón es una columna vertical.
    Los textos largos bajan a la siguiente línea para que nada se corte.
    """
    # --- 1. CONFIGURACIÓN DE FUENTES ---
    try:
        # Rutas comunes en macOS
        font_path = "/System/Library/Fonts/Helvetica.ttc" 
        font_title = ImageFont.truetype(font_path, 22)
        font_anest = ImageFont.truetype(font_path, 18)
        font_body = ImageFont.truetype(font_path, 16)
        font_time = ImageFont.truetype(font_path, 18)
    except:
        font_title = ImageFont.load_default()
        font_anest = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_time = ImageFont.load_default()

    # --- 2. CONFIGURACIÓN DEL DISEÑO ---
    # Obtener los pabellones únicos manteniendo el orden original
    pabellones = df['Pabellon'].dropna().unique().tolist()
    
    col_width = 380  # Ancho generoso para cada columna
    padding = 15     # Margen interno de los textos
    margin_top = 20
    
    # --- 3. CALCULAR EL ALTO DINÁMICO DE LA IMAGEN ---
    # Simulamos el dibujo para saber qué columna es la más alta
    dummy_img = Image.new('RGB', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    col_heights = []
    
    for pab in pabellones:
        df_pab = df[df['Pabellon'] == pab]
        h = margin_top + 50 # Espacio del título del pabellón
        current_anest = None
        
        for _, row in df_pab.iterrows():
            # Cambio de Anestesista
            if str(row['Anestesista']) != str(current_anest):
                h += 40 
                current_anest = row['Anestesista']
            
            # Espacio del Horario
            h += 30 
            # Calcular líneas que ocupará el Paciente, Cirugía y Médico
            h += len(wrap_text(f"Pcte: {row['Paciente']}", font_body, col_width - padding*2, dummy_draw)) * 22
            h += len(wrap_text(f"Cx: {row['Cirugia']}", font_body, col_width - padding*2, dummy_draw)) * 22
            h += len(wrap_text(f"Dr: {row['Medico']}", font_body, col_width - padding*2, dummy_draw)) * 22
            
            h += 30 # Margen debajo de cada cirugía
            
        col_heights.append(h)
        
    # El alto de la imagen será el de la columna más larga
    max_height = max(col_heights) if col_heights else 600
    max_height += 50 
    total_width = col_width * len(pabellones)
    
    # --- 4. DIBUJAR LA PIZARRA DIGITAL ---
    img = Image.new('RGB', (total_width, max_height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    for i, pab in enumerate(pabellones):
        x_start = i * col_width
        
        # Línea divisoria de la columna
        draw.rectangle([x_start, 0, x_start + col_width, max_height], outline=(200, 200, 200), width=1)
        
        # Cabecera gris del Pabellón
        draw.rectangle([x_start, 0, x_start + col_width, 50], fill=(235, 235, 235), outline=(200, 200, 200))
        
        # Texto del Pabellón (Centrado)
        pab_text = str(pab).upper()
        title_bbox = draw.textbbox((0, 0), pab_text, font=font_title)
        title_w = title_bbox[2] - title_bbox[0]
        draw.text((x_start + (col_width - title_w)/2, 12), pab_text, font=font_title, fill=(0, 0, 0))
        
        df_pab = df[df['Pabellon'] == pab]
        y_curr = 60
        current_anest = None
        
        # Dibujar cada cirugía en la columna
        for _, row in df_pab.iterrows():
            
            # --- DIBUJAR ANESTESISTA ---
            if str(row['Anestesista']) != str(current_anest):
                anest_text = str(row['Anestesista']).upper()
                if anest_text.lower() != 'nan' and anest_text != '-':
                    # Cajita azul clara para el anestesista
                    draw.rectangle([x_start + 10, y_curr, x_start + col_width - 10, y_curr + 30], fill=(220, 235, 255))
                    a_bbox = draw.textbbox((0, 0), anest_text, font=font_anest)
                    a_w = a_bbox[2] - a_bbox[0]
                    draw.text((x_start + (col_width - a_w)/2, y_curr + 4), anest_text, font=font_anest, fill=(0, 50, 150))
                    y_curr += 40
                current_anest = row['Anestesista']
            
            # --- DIBUJAR DATOS DE LA CIRUGÍA ---
            # Horario (en rojo oscuro para destacar)
            horario_str = str(row['Horario'])
            if horario_str.lower() == 'nan': horario_str = ""
            draw.text((x_start + padding, y_curr), horario_str, font=font_time, fill=(150, 0, 0))
            y_curr += 28
            
            # Paciente
            pac_lines = wrap_text(f"Pcte: {row['Paciente']}", font_body, col_width - padding*2, draw)
            for line in pac_lines:
                draw.text((x_start + padding, y_curr), line, font=font_body, fill=(0, 0, 0))
                y_curr += 22
                
            # Cirugía
            cx_lines = wrap_text(f"Cx: {row['Cirugia']}", font_body, col_width - padding*2, draw)
            for line in cx_lines:
                draw.text((x_start + padding, y_curr), line, font=font_body, fill=(80, 80, 80))
                y_curr += 22
                
            # Médico Tratante (en verde oscuro)
            med_lines = wrap_text(f"Dr: {row['Medico']}", font_body, col_width - padding*2, draw)
            for line in med_lines:
                draw.text((x_start + padding, y_curr), line, font=font_body, fill=(0, 80, 0))
                y_curr += 22
            
            y_curr += 10
            
            # Línea sutil separadora entre pacientes
            draw.line([(x_start + padding, y_curr), (x_start + col_width - padding, y_curr)], fill=(220, 220, 220), width=1)
            y_curr += 15
            
    return img