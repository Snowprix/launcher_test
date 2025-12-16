import os
import glob
import json
import time
import google.generativeai as genai

# --- CONFIGURACIÓN ---
CARPETA_TUITS = 'tuits'
CARPETA_NEWS = 'news'

def configurar_modelo_seguro():
    """Prueba modelos en orden hasta encontrar uno que funcione gratis."""
    # Lista de prioridades: Del más nuevo al más viejo/seguro
    candidatos = [
        'gemini-1.5-flash-8b',    # El más ligero y probable de ser gratis hoy
        'gemini-2.5-flash-lite',  # Versión ligera del nuevo
        'gemini-1.5-flash',       # El estándar anterior
        'gemini-pro'              # La vieja confiable (nunca falla)
    ]

    for nombre_modelo in candidatos:
        print(f"🔄 Probando conexión con modelo: {nombre_modelo}...")
        try:
            model = genai.GenerativeModel(nombre_modelo)
            # Hacemos una prueba tonta para ver si responde y si hay cuota
            model.generate_content("Hola")
            print(f"✅ ¡CONECTADO! Usaremos: {nombre_modelo}")
            return model
        except Exception as e:
            print(f"   ❌ Falló {nombre_modelo}. Razón: {e}")
            time.sleep(1) # Esperar un poco antes de probar el siguiente
    
    raise Exception("💀 TODOS los modelos fallaron. Revisa tu API KEY.")

def main():
    # 1. APLICAR LA LLAVE
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR CRÍTICO: No se encontró la GEMINI_API_KEY.")
        exit(1)

    genai.configure(api_key=api_key)

    # --- AUTO-SELECCIÓN DE MODELO ---
    try:
        model = configurar_modelo_seguro()
    except Exception as e:
        print(e)
        exit(1)
    # --------------------------------

    # 2. VERIFICAR CARPETAS
    if not os.path.exists(CARPETA_NEWS):
        os.makedirs(CARPETA_NEWS)

    # 3. BUSCAR TUITS
    patron_busqueda = os.path.join(CARPETA_TUITS, "*.json")
    archivos_json = glob.glob(patron_busqueda)
    print(f"📂 Se encontraron {len(archivos_json)} tuits.")

    if len(archivos_json) == 0:
        return

    # 4. PROCESAR
    nuevas_noticias = 0
    
    for archivo in archivos_json:
        try:
            nombre_archivo = os.path.basename(archivo)
            nombre_base = os.path.splitext(nombre_archivo)[0]
            ruta_salida = os.path.join(CARPETA_NEWS, f"noticia_{nombre_base}.txt")

            if os.path.exists(ruta_salida):
                continue

            print(f"🤖 Generando noticia para: {nombre_archivo}...")

            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                contenido = data.get('text', str(data))

            prompt = f"""
            Actúa como un redactor de noticias. Tuit origen: "{contenido}"
            Tarea: Redacta una noticia corta (Título + 2 párrafos). Tono neutral.
            """

            # INTENTO DE GENERACIÓN CON EL MODELO ELEGIDO
            try:
                response = model.generate_content(prompt)
                texto_generado = response.text
                
                with open(ruta_salida, "w", encoding="utf-8") as f:
                    f.write(texto_generado)
                
                print(f"✅ Noticia guardada: {ruta_salida}")
                nuevas_noticias += 1
                time.sleep(5) # Pausa larga para evitar error 429
                
            except Exception as e_gen:
                print(f"⚠️ Error generando contenido: {e_gen}")

        except Exception as e:
            print(f"⚠️ Error procesando archivo: {e}")

    print(f"🏁 Finalizado. Noticias nuevas: {nuevas_noticias}")

if __name__ == "__main__":
    main()
