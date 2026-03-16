from flask import Flask, render_template, jsonify, request, session
import json
from datetime import datetime
import os

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_only_local_secret')  # No exponer secretos en código

PLAYERS_FILE = os.path.join(os.path.dirname(__file__), 'players.json')
BASE_DIR = os.path.dirname(__file__)
PLANTILLAS_DIR = os.path.join(BASE_DIR, 'plantillas')
CURRENT_PLANTILLA_FILE = os.path.join(BASE_DIR, 'plantilla.json')


def ensure_plantillas_dir():
    os.makedirs(PLANTILLAS_DIR, exist_ok=True)


def persist_current_squad(squad_data):
    """Guarda la plantilla actual para que el analista siempre pueda leer contexto."""
    with open(CURRENT_PLANTILLA_FILE, 'w', encoding='utf-8') as f:
        json.dump(squad_data, f, ensure_ascii=False, indent=4)

    ensure_plantillas_dir()
    last_path = os.path.join(PLANTILLAS_DIR, 'plantilla_actual.json')
    with open(last_path, 'w', encoding='utf-8') as f:
        json.dump(squad_data, f, ensure_ascii=False, indent=4)

def load_players():
    with open(PLAYERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def index():
    return render_template('squad_builder.html')

@app.route('/api/players')
def get_players():
    """Devuelve todos los jugadores, opcionalmente filtrados por posición."""
    players = load_players()
    position = request.args.get('position', None)
    search = request.args.get('search', '').strip().lower()

    if position:
        players = [p for p in players if p.get('position') == position]

    if search:
        players = [p for p in players if search in p.get('name', '').lower()]

    def _safe_pts(p):
        try:
            v = str(p.get('ptos_total', '0')).replace('m', '').replace('-', '0').strip()
            return int(float(v)) if v else 0
        except (ValueError, TypeError):
            return 0

    # Ordenar por puntos totales descendente
    players.sort(key=_safe_pts, reverse=True)
    return jsonify(players)

@app.route('/api/save', methods=['POST'])
def save_squad():
    """Guarda la plantilla en la carpeta plantillas/."""
    data = request.get_json()
    filename = str(data.get('filename', 'mi_equipo')).strip() or 'mi_equipo'
    squad = data.get('squad', [])

    if not filename.endswith('.json'):
        filename += '.json'

    safe_name = os.path.basename(filename)
    ensure_plantillas_dir()
    output_path = os.path.join(PLANTILLAS_DIR, safe_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(squad, f, ensure_ascii=False, indent=4)

    return jsonify({'success': True, 'path': output_path, 'filename': safe_name})


@app.route('/api/templates')
def list_templates():
    """Lista plantillas guardadas en la carpeta plantillas/."""
    try:
        ensure_plantillas_dir()
        files = [
            name for name in os.listdir(PLANTILLAS_DIR)
            if name.lower().endswith('.json') and os.path.isfile(os.path.join(PLANTILLAS_DIR, name))
        ]
        files.sort()
        return jsonify({'success': True, 'templates': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/templates/load', methods=['POST'])
def load_template():
    """Carga una plantilla guardada desde plantillas/."""
    data = request.get_json()
    filename = str(data.get('filename', '')).strip()
    if not filename:
        return jsonify({'success': False, 'error': 'Nombre de plantilla vacío'}), 400

    safe_name = os.path.basename(filename)
    path = os.path.join(PLANTILLAS_DIR, safe_name)
    if not os.path.exists(path):
        return jsonify({'success': False, 'error': 'Plantilla no encontrada'}), 404

    try:
        with open(path, 'r', encoding='utf-8') as f:
            squad_data = json.load(f)
        if not isinstance(squad_data, list):
            return jsonify({'success': False, 'error': 'Formato de plantilla no válido'}), 400

        persist_current_squad(squad_data)
        return jsonify({'success': True, 'squad': squad_data, 'filename': safe_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sync_squad', methods=['POST'])
def sync_squad():
    """Sincronización silenciosa de la plantilla actual para que el Analista la conozca."""
    data = request.get_json()
    squad_data = data.get('squad', [])

    try:
        persist_current_squad(squad_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analizar', methods=['POST'])
def analizar_endpoint():
    """Recibe el equipo seleccionado y el presupuesto, lanza el analista y devuelve la recomendación."""
    data = request.get_json()
    squad_data = data.get('squad', [])
    presupuesto = float(data.get('presupuesto', 0))

    # Guardar plantilla para que analista.py la lea
    persist_current_squad(squad_data)

    try:
        from analista import analizar as analizar_agente
        resultado = analizar_agente(presupuesto)
        return jsonify({'success': True, 'resultado': str(resultado)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para el chatbot interactivo."""
    import re as _re
    data = request.get_json()
    user_msg = data.get('message', '')
    squad_data = data.get('squad', [])
    presupuesto = float(data.get('presupuesto', 0))

    # Extraer presupuesto del texto si el cliente no lo envía (ej: "mi saldo es 10m")
    if presupuesto == 0:
        _match = _re.search(r'(\d+(?:[.,]\d+)?)\s*(?:m(?:illones?)?)', user_msg.lower())
        if _match:
            presupuesto = float(_match.group(1).replace(',', '.'))

    # Inicializar historial si no existe
    if 'chat_history' not in session:
        session['chat_history'] = []

    # Si el cliente no envía plantilla, usamos la última conocida persistida.
    if not squad_data and os.path.exists(CURRENT_PLANTILLA_FILE):
        try:
            with open(CURRENT_PLANTILLA_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                squad_data = loaded
        except Exception:
            pass

    if not squad_data:
        return jsonify({
            'success': False,
            'error': 'No hay plantilla cargada todavía. Carga una plantilla o selecciona jugadores antes de chatear.'
        }), 400

    persist_current_squad(squad_data)

    try:
        from analista import chatear
        plantilla_contexto = "Sin plantilla cargada."
        if squad_data:
            nombres = [p.get('name', '?') for p in squad_data if isinstance(p, dict)]
            plantilla_contexto = f"Jugadores ({len(nombres)}): " + ", ".join(nombres)

        user_msg_with_context = (
            f"PLANTILLA ACTUAL: {plantilla_contexto}\n"
            f"PREGUNTA: {user_msg}"
        )

        respuesta, updated_history = chatear(
            user_msg_with_context,
            session.get('chat_history', []),
            presupuesto,
            original_msg=user_msg,
        )

        # Recortar el historial para que Flask no explote con el tamaño de la cookie
        MAX_MENSAJES = 4
        MAX_LONGITUD_TEXTO = 400 
        
        historial_recortado = []
        for msg in updated_history[-MAX_MENSAJES:]:
            texto = str(msg.get('content', ''))
            if len(texto) > MAX_LONGITUD_TEXTO:
                texto = texto[:MAX_LONGITUD_TEXTO] + "... [texto truncado]"
            historial_recortado.append({"role": msg['role'], "content": texto})

        session['chat_history'] = historial_recortado
        session.modified = True
        
        return jsonify({'success': True, 'response': str(respuesta)})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/market/generate', methods=['POST'])
def generate_market():
    """Genera un nuevo mercado basado en la plantilla actual (excluyendo jugadores elegidos)."""
    data = request.get_json()
    squad_data = data.get('squad', [])
    
    try:
        from procesador_simple import cargar_mercado
        mercado = cargar_mercado(excluidos=squad_data)
        
        # Guardar mercado para que el agente lo lea
        mercado_path = os.path.join(os.path.dirname(__file__), 'mercado.json')
        with open(mercado_path, 'w', encoding='utf-8') as f:
            json.dump(mercado, f, ensure_ascii=False, indent=4)
            
        return jsonify({'success': True, 'mercado': mercado})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/players/update', methods=['POST'])
def update_players_data():
    """Lanza el scraper de UEFA para actualizar players.json."""
    try:
        from scrap_champions import scrape_players
        scrape_players()
        return jsonify({'success': True, 'message': 'Base de datos UEFA actualizada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/market/current')
def get_current_market():
    """Devuelve el mercado actualmente guardado en mercado.json."""
    mercado_path = os.path.join(os.path.dirname(__file__), 'mercado.json')
    if not os.path.exists(mercado_path):
        return jsonify({'success': False, 'error': 'No hay mercado generado'}), 404
    
    try:
        with open(mercado_path, 'r', encoding='utf-8') as f:
            mercado = json.load(f)
        return jsonify({'success': True, 'mercado': mercado})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # use_reloader=False evita conflictos con subprocesos del CodeAgent
    app.run(debug=True, port=5001, use_reloader=False)
