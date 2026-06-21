import streamlit as st
import pandas as pd
from PIL import Image
import io

# Importar módulos internos
from image_utils import limpiar_imagen_para_ocr
from ocr_engine import extraer_datos_con_respaldo  # <-- Nuestro nuevo motor dual
from image_generator import crear_imagen_tabla_limpia

# Configuración de página
st.set_page_config(page_title="Digitalizador Tabla MEDS", page_icon="🏥", layout="wide")

st.title("🏥 Digitalizador de Tabla Operatoria - Clínica MEDS")
st.markdown("Transforma fotografías confusas de la tabla en imágenes digitales nítidas y estructuradas.")

# --- 1. VALIDACIÓN DE SEGURIDAD LOCAL ---
# Pedimos solo la contraseña corporativa, no las API Keys
password_ingresado = st.text_input("🔑 Ingresa la contraseña de acceso MEDS:", type="password")

# Rescatamos las llaves desde la caja fuerte oculta (.streamlit/secrets.toml)
try:
    API_KEY_GOOGLE = st.secrets["GEMINI_API_KEY"]
    API_KEY_QWEN = st.secrets["QWEN_API_KEY"]
    PASSWORD_CORRECTO = st.secrets["PASSWORD_MEDS"]
except Exception:
    st.error("Falta configurar los Secrets locales en la carpeta .streamlit.")
    st.stop()

st.divider()

if not password_ingresado:
    st.info("Por favor, ingresa la contraseña de acceso para activar el sistema.")
elif password_ingresado != PASSWORD_CORRECTO:
    st.error("Contraseña incorrecta. Acceso denegado.")
else:
    # --- 2. A PARTIR DE AQUÍ EL ACCESO ES SEGURO ---
    archivo_subido = st.file_uploader("Sube la fotografía de la tabla aquí", type=["jpg", "jpeg", "png"])

    if archivo_subido is not None:
        imagen_original = Image.open(archivo_subido)
        
        with st.spinner("🤖 La IA está analizando la caligrafía médica... (Plan A: Google)"):
            imagen_preparada = limpiar_imagen_para_ocr(imagen_original)
            
            # Llamamos a la función enviándole las dos llaves maestras de respaldo
            texto_csv = extraer_datos_con_respaldo(imagen_preparada, API_KEY_GOOGLE, API_KEY_QWEN)
        
        # Si ambos motores fallan, mostramos el error
        if "Error" in texto_csv or "Fallo" in texto_csv or "❌" in texto_csv:
            st.error(texto_csv)
        else:
            try:
                # Si todo sale bien, armamos la tabla
                df_datos = pd.read_csv(io.StringIO(texto_csv), sep=";")
                
                with st.spinner("✨ Generando pizarra digital Kanban..."):
                    imagen_final_limpia = crear_imagen_tabla_limpia(df_datos)
                
                st.success("¡Digitalización completada!")
                st.divider()
                
                st.subheader("📋 Pizarra Digital Operatoria")
                st.image(imagen_final_limpia, use_column_width=True)
                
                # Botón de Descarga
                buf = io.BytesIO()
                imagen_final_limpia.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="📥 Descargar Pizarra Limpia (PNG)",
                    data=byte_im,
                    file_name="tabla_operatoria_meds.png",
                    mime="image/png",
                )
                
            except Exception as e:
                st.error(f"Error al procesar la estructura gráfica: {str(e)}\n\nTexto crudo devuelto por la IA:\n{texto_csv}")