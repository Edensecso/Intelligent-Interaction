from flask import Flask, render_template, jsonify, request
import json
from datetime import datetime
import os

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

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


@app.route('/api/formations')
def get_formations():
    """Devuelve las formaciones disponibles."""
    formations = ['541', '532', '451', '442', '433', '352', '343']
    return jsonify(formations)

if __name__ == '__main__':
    # use_reloader=False evita conflictos con subprocesos del CodeAgent
    app.run(debug=True, port=5001, use_reloader=False)
