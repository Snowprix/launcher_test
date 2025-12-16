import os
import re
import random 
from flask import Flask, render_template, url_for, send_from_directory 

# Inicializa la aplicación Flask
app = Flask(__name__)

# --- Rutas a las carpetas (Actualizadas) ---
NOTICIAS_DIR = os.path.join(app.root_path, 'news')
IMAGES_DIR = os.path.join(app.root_path, 'tuits', 'images') 

# --- RUTA CLAVE PARA SERVIR IMÁGENES ---
@app.route('/media/<filename>')
def servir_imagen_desde_templates(filename):
    """
    Sirve los archivos de la ruta 'tuits/images/' al navegador.
    """
    return send_from_directory(IMAGES_DIR, filename)


# --- FUNCIÓN: SIMULACIÓN DE API DE ANUNCIOS (TEXTO SOLAMENTE) ---
def generar_anuncio(slot_id):
    """
    Simula una llamada a una API de anuncios. Se ha eliminado la imagen del anuncio 3.
    """
    
    anuncios_disponibles = [
        # Anuncio 1: Servicios
        f"""
        <div class="ad-unit ad-servicio" id="{slot_id}">
            <h3>💸 Patrocinado: Servicios en la Nube</h3>
            <p>Optimice sus costos y escale su negocio con nuestra plataforma de hosting ultrarrápida. ¡30% de descuento!</p>
            <a href="#" class="ad-link">Visitar Ahora →</a>
        </div>
        """,
        # Anuncio 2: Producto
        f"""
        <div class="ad-unit ad-producto" id="{slot_id}">
            <h4>Anuncio</h4>
            <h2>¡Nuevo Libro! "El Futuro del Código"</h2>
            <p>Descubre las tendencias que revolucionarán la programación en 2026. Disponible en tapa dura.</p>
            <a href="#" class="ad-link">Comprar el eBook</a>
        </div>
        """,
        # --- ANUNCIO 3: Vuelto a formato solo texto (Sin la etiqueta <img>) ---
        f"""
        <div class="ad-unit ad-juego" id="{slot_id}">
            <h4>Ocio Digital - Patrocinado</h4>
            <h2>¡Únete a Roulette Rooms y Juega!</h2>
            <p>Descubre el mundo de los desafíos y las salas de chat. ¡Entra ya y diviértete!</p>
            <a href="https://roulette-rooms.lovable.app/" target="_blank" class="ad-link">¡Jugar Ahora!</a>
        </div>
        """
    ]
    
    return random.choice(anuncios_disponibles)

# Hacemos la función 'generar_anuncio' accesible globalmente en todas las plantillas Jinja
@app.context_processor
def inject_globals():
    return dict(generar_anuncio=generar_anuncio)


# --- FUNCIONES DE PROCESAMIENTO (Se mantienen) ---

def formatear_parrafos(contenido):
    contenido = contenido.strip()
    contenido_con_p = re.sub(r'\n\s*\n', '</p><p>', contenido)
    return f'<p>{contenido_con_p}</p>'

def procesar_etiquetas_imagen(contenido):
    patron = r'\*(.*?)\*'
    
    def reemplazar_etiqueta(match):
        parametros = [p.strip() for p in match.group(1).split(',')]
        
        # Asignación Flexible (Nombre, Dimensiones, Alineación)
        if not parametros or not parametros[0]: return f""
        nombre_archivo_base = parametros[0]
        dimensiones = parametros[1] if len(parametros) > 1 and parametros[1] else 'auto x auto' 
        try:
            ancho, alto = dimensiones.split('x')
        except ValueError:
            ancho, alto = 'auto', 'auto' 
        alineacion = parametros[3].lower() if len(parametros) > 3 and parametros[3] else 'none'
        clase_css = f'align-{alineacion}'
        
        # Búsqueda del Archivo Real
        nombre_archivo_con_extension = None
        try:
            for f in os.listdir(IMAGES_DIR):
                if f.startswith(nombre_archivo_base + '.') and f != '.' and f != '..':
                    nombre_archivo_con_extension = f 
                    break
        except FileNotFoundError: return f'<div style="color: red;">ERROR: La carpeta de imágenes no existe en: {IMAGES_DIR}</div>'

        if not nombre_archivo_con_extension:
            return f'<div style="color: red; padding: 10px; border: 1px dashed red;">ERROR: La imagen "{nombre_archivo_base}" no se encontró en {IMAGES_DIR}</div>'

        # Generación del HTML con la ruta /media/
        img_url = url_for('servir_imagen_desde_templates', filename=nombre_archivo_con_extension)
        
        img_html = (
            f'<img src="{img_url}" alt="{nombre_archivo_base}" width="{ancho}" height="{alto}" class="{clase_css}">'
        )
        
        return img_html

    contenido_procesado = re.sub(patron, reemplazar_etiqueta, contenido)
    return contenido_procesado


# --- Rutas de la Aplicación ---

@app.route('/')
def pagina_principal():
    try:
        archivos_noticias = [f for f in os.listdir(NOTICIAS_DIR) if f.endswith('.txt')]
        titulares = [f.replace('.txt', '') for f in archivos_noticias]
        return render_template('index.html', titulares=titulares)
    except Exception as e:
        return f"Error al cargar noticias. Asegúrate de que la carpeta 'news' exista. Error: {e}", 500

@app.route('/noticia/<titulo_archivo>')
def mostrar_noticia(titulo_archivo):
    nombre_archivo = titulo_archivo + '.txt'
    ruta_completa = os.path.join(NOTICIAS_DIR, nombre_archivo)
    if not os.path.exists(ruta_completa):
        return "Noticia no encontrada", 404
    try:
        with open(ruta_completa, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        contenido_formateado = formatear_parrafos(contenido)
        contenido_procesado = procesar_etiquetas_imagen(contenido_formateado)
        titulo_display = titulo_archivo
        
        return render_template('noticia.html', titulo=titulo_display, contenido=contenido_procesado)
    except Exception as e:
        return f"Error al leer la noticia: {e}", 500

if __name__ == '__main__':
    # Obtiene el puerto de la variable de entorno (usado por Render, Heroku, etc.)
    # o usa 5000 si no se encuentra (para desarrollo local)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)