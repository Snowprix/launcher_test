import os
import glob
import json
import time
import google.generativeai as genai

# --- CONFIGURACIÓN ---
# Como el script lo ejecuta GitHub desde la raíz del proyecto,
# las rutas se escriben directas:
CARPETA_TUITS = 'tuits'
CARPETA_NEWS = 'news'

def main():
    # 1. APLICAR LA LLAVE (SEGURIDAD)
    # El script busca la llave en las variables de entorno que configuramos en el YAML.
    # No necesitas escribirla aquí, GitHub se la pasa invisiblemente.
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ ERROR CRÍTICO: No se encontró la GEMINI_API_KEY en el entorno.")
        print("   Asegúrate de haberla agregado en Settings -> Secrets en GitHub.")
        exit(1)

    # Configuramos Gemini
    genai.configure(api_key=api_key)
    # Usamos el modelo Flash que es rápido y eficiente
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 2. VERIFICAR CARPETAS
    if not os.path.exists(CARPETA_NEWS):
        os.makedirs(CARPETA_NEWS)
        print(f"📁 Carpeta '{CARPETA_NEWS}' creada automáticamente.")

    # 3. BUSCAR TUITS
    patron_busqueda = os.path.join(CARPETA_TUITS, "*.json")
    archivos_json = glob.glob(patron_busqueda)
    
    print(f"📂 Se encontraron {len(archivos_json)} tuits en la carpeta '{CARPETA_TUITS}'.")

    if len(archivos_json) == 0:
        print("ℹ️ No hay nada que procesar. Finalizando.")
        return

    # 4. PROCESAR CADA TUIT
    nuevas_noticias = 0
    
    for archivo in archivos_json:
        try:
            # Preparamos el nombre del archivo de salida
            nombre_archivo = os.path.basename(archivo) # ej: tuit_123.json
            nombre_base = os.path.splitext(nombre_archivo)[0]
            ruta_salida = os.path.join(CARPETA_NEWS, f"noticia_{nombre_base}.txt")

            # Si ya existe la noticia, no gastamos saldo de API
            if os.path.exists(ruta_salida):
                # print(f"⏩ Saltando {nombre_archivo}, ya fue procesado.")
                continue

            print(f"🤖 Generando noticia para: {nombre_archivo}...")

            # Leemos el tuit
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Intentamos obtener el texto, si falla usamos todo el json
                contenido = data.get('text', str(data))

            # Prompt para Gemini (El "Periodista")
            prompt = f"""
            Actúa como un redactor de noticias digitales.
            Tengo este tuit crudo extraído de X (Twitter):
            
            "{contenido}"
            
            Tu tarea:
            1. Analiza el contenido.
            2. Redacta una noticia corta (Título + 2 párrafos máximo).
            3. Usa un tono informativo y neutral.
            4. Si el tuit es irrelevante o spam, escribe solo "IRRELEVANTE".
            """

            # Llamada a la API
            response = model.generate_content(prompt)
            texto_generado = response.text

            # Guardamos el resultado
            with open(ruta_salida, "w", encoding="utf-8") as f:
                f.write(texto_generado)
            
            print(f"✅ Noticia guardada: {ruta_salida}")
            nuevas_noticias += 1
            
            # Pausa de cortesía para la API (Rate Limit)
            time.sleep(2)

        except Exception as e:
            print(f"⚠️ Error procesando {archivo}: {e}")

    print(f"🏁 Proceso finalizado. Se generaron {nuevas_noticias} noticias nuevas.")

if __name__ == "__main__":
    main()
