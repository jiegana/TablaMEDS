import google.generativeai as genai
import requests  # <-- Cambiado para usar conexión directa sin el bug de Mac
import io
import base64

def extraer_datos_con_respaldo(imagen_pil, api_key_google, api_key_qwen):
    """
    Motor Dual de OCR/ICR Espacial:
    Intenta extraer los datos usando Google Gemini (Rápido/Gratuito).
    Si Google falla (Timeout, Quota Exceeded), cambia automáticamente 
    a Llama-3.2 Vision vía OpenRouter de forma 100% GRATUITA.
    """
    
    # --- PROMPT MAESTRO (Compartido para ambas IAs) ---
    prompt = """
    Eres un asistente médico experto. Analiza la fotografía de una tabla operatoria de la Clínica MEDS.
    Tu trabajo es leerla y estructurarla estrictamente en formato CSV usando el punto y coma (;) como separador.
    
    Las columnas obligatorias a generar son: Pabellon;Anestesista;Horario;Paciente;Cirugia;Medico.
    
    REGLAS CRÍTICAS DE LECTURA ESPACIAL E ICR (Reconocimiento Inteligente de Caracteres):
    1. TEXTO IMPRESO VS MANUSCRITO: La tabla combina bloques de texto impreso por el sistema y anotaciones escritas a mano con plumón.
    2. IDENTIFICACIÓN DEL ANESTESISTA: El Anestesista SIEMPRE está escrito a mano. Suele ser un único apellido (ej. Olivo, Sanchez, Olivares, Vallette, Herve, Acuña). NUNCA contiene los prefijos del sistema impreso como 'PCTE.', 'DR.', o 'CX.'.
    3. FLUJO DE ASIGNACIÓN (DE ARRIBA HACIA ABAJO): Lee cada columna del pabellón de arriba hacia abajo. Cuando encuentres un apellido manuscrito, ese es el 'Anestesista Activo'. Asígnale ese anestesista a TODOS los bloques de pacientes impresos que estén por debajo de él en esa columna.
    4. CAMBIO DE ANESTESISTA: Si sigues bajando por la misma columna y encuentras un NUEVO apellido manuscrito, el anestesista cambia. A partir de ese punto hacia abajo, los siguientes pacientes deben llevar el nuevo anestesista.
    5. Si no logras entender una palabra por la caligrafía, escribe 'Ilegible'.
    
    FORMATO DE SALIDA:
    - NO incluyas saludos, explicaciones, ni el formato markdown ```csv. 
    - Devuelve ÚNICAMENTE las líneas de texto separadas por punto y coma, incluyendo la primera fila de títulos.
    """

    # --- EMPAQUETADO DE IMAGEN (JPEG en memoria para alta velocidad) ---
    buffer = io.BytesIO()
    imagen_pil.convert('RGB').save(buffer, format="JPEG", quality=95)
    bytes_imagen = buffer.getvalue()

    # ==========================================
    # INTENTO 1: GOOGLE GEMINI
    # ==========================================
    try:
        genai.configure(api_key=api_key_google)
        
        # Autodetección de modelos disponibles
        modelo_disponible = "gemini-3.5-flash"
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and '3.5-flash' in m.name:
                modelo_disponible = m.name
                break

        model = genai.GenerativeModel(modelo_disponible)
        imagen_google = {"mime_type": "image/jpeg", "data": bytes_imagen}
        
        respuesta_google = model.generate_content(
            [prompt, imagen_google],
            request_options={"timeout": 60}
        )
        return respuesta_google.text.strip()

    except Exception as e_google:
        # Si Google falla, guardamos el error en la terminal y activamos el Plan B gratuito
        error_google = str(e_google)
        print(f"⚠️ Google falló o superó su cuota ({error_google}). Activando plan de respaldo GRATUITO...")

    # ==========================================
    # INTENTO 2: MODELO VISIÓN GRATUITO (Conexión Directa a OpenRouter)
    # ==========================================
    try:
        if not api_key_qwen:
             return f"Error con Google IA: {error_google} \n(No se pudo activar el respaldo porque falta la QWEN_API_KEY en tus secrets)."

        # Convertir bytes a formato Base64 necesario para OpenRouter
        imagen_base64 = base64.b64encode(bytes_imagen).decode('utf-8')

        # Headers de conexión directa (Evita el bug de Mac)
        headers = {
            "Authorization": f"Bearer {api_key_qwen}",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Digitalizador MEDS",
            "Content-Type": "application/json"
        }

        # Configuración del payload con el modelo 100% GRATIS y límite seguro de tokens
        payload = {
            "model": "google/gemini-2.0-flash-lite-preview-02-05:free", # <-- Nueva ruta 100% gratuita y estable
            "max_tokens": 2000,                                     # <-- Evita el error 402 de saldo
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{imagen_base64}"}
                        }
                    ]
                }
            ]
        }

        # Disparamos la solicitud HTTP directa
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )
        
        # Si la respuesta es exitosa (Código 200) extraemos el CSV
        if response.status_code == 200:
            datos_json = response.json()
            return datos_json['choices'][0]['message']['content'].strip()
        else:
            raise Exception(f"OpenRouter rechazó la petición. Código {response.status_code}: {response.text}")

    except Exception as e_qwen:
        # Si ambos sistemas fallan por completo, devolvemos el reporte
        return f"❌ Fallo crítico en ambos servidores.\n- Error Google: {error_google}\n- Error Respaldo/OpenRouter: {str(e_qwen)}"