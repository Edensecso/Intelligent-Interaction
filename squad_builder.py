from flask import Flask, render_template, jsonify, request, session
import json
from datetime import datetime
import os

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
app.secret_key = 'ucl_fantasy_secret_key' # Para persistir historial de chat

PLAYERS_FILE = os.path.join(os.path.dirname(__file__), 'players.json')

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

    # Ordenar por puntos totales descendente
    players.sort(key=lambda p: int(p.get('ptos_total', '0')), reverse=True)
    return jsonify(players)

@app.route('/api/save', methods=['POST'])
def save_squad():
    """Guarda la plantilla como archivo .json con el mismo formato que players.json."""
    data = request.get_json()
    filename = data.get('filename', 'mi_equipo')
    squad = data.get('squad', [])

    if not filename.endswith('.json'):
        filename += '.json'

    output_path = os.path.join(os.path.dirname(__file__), filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(squad, f, ensure_ascii=False, indent=4)

    return jsonify({'success': True, 'path': output_path})

@app.route('/api/sync_squad', methods=['POST'])
def sync_squad():
    """Sincronización silenciosa de la plantilla actual para que el Analista la conozca."""
    data = request.get_json()
    squad_data = data.get('squad', [])
    
    plantilla_path = os.path.join(os.path.dirname(__file__), 'plantilla.json')
    try:
        with open(plantilla_path, 'w', encoding='utf-8') as f:
            json.dump(squad_data, f, ensure_ascii=False, indent=4)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analizar', methods=['POST'])
def analizar():
    """Recibe el equipo seleccionado y el presupuesto, lanza el analista y devuelve la recomendación."""
    data = request.get_json()
    squad_data = data.get('squad', [])
    presupuesto = float(data.get('presupuesto', 0))

    # Guardar plantilla para que analista.py la lea en ejecutar_pipeline()
    plantilla_path = os.path.join(os.path.dirname(__file__), 'plantilla.json')
    with open(plantilla_path, 'w', encoding='utf-8') as f:
        json.dump(squad_data, f, ensure_ascii=False, indent=4)

    try:
        from analista import analizar
        resultado = analizar(presupuesto)
        return jsonify({'success': True, 'resultado': str(resultado)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para el chatbot interactivo."""
    data = request.get_json()
    user_msg = data.get('message', '')
    squad_data = data.get('squad', [])
    presupuesto = float(data.get('presupuesto', 0))

    # Inicializar historial si no existe
    if 'chat_history' not in session:
        session['chat_history'] = []

    # Guardar plantilla actual (por si el agente necesita leerla)
    plantilla_path = os.path.join(os.path.dirname(__file__), 'plantilla.json')
    with open(plantilla_path, 'w', encoding='utf-8') as f:
        json.dump(squad_data, f, ensure_ascii=False, indent=4)

    try:
        from analista import chatear
        # Enviamos historial vacío para que no tenga "memoria" de errores pasados
        respuesta, _ = chatear(user_msg, [], presupuesto)
        
        # Ya no guardamos el historial en la sesión
        session['chat_history'] = []
        
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
