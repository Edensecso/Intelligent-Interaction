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
    """Guarda la plantilla como archivo .txt."""
    data = request.get_json()
    filename = data.get('filename', 'mi_equipo')
    squad = data.get('squad', [])

    if not filename.endswith('.txt'):
        filename += '.txt'

    now = datetime.now().strftime('%d/%m/%Y %H:%M')

    lines = [f"=== RESULTADO FANTASY UCL — {now} ===", "", "--- EQUIPO ---"]

    for player in squad:
        pos = player.get('position', '???')
        name = player.get('name', 'Desconocido')
        price = player.get('price', '0m')
        pts = player.get('ptos_total', '0')
        forma = player.get('estado_forma', '0.0 stars')
        lines.append(f"  {pos} - {name} ({price}) | Pts: {pts} | Forma: {forma}")

    output_path = os.path.join(os.path.dirname(__file__), filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    return jsonify({'success': True, 'path': output_path})

@app.route('/api/formations')
def get_formations():
    """Devuelve las formaciones disponibles."""
    formations = ['541', '532', '451', '442', '433', '352', '343']
    return jsonify(formations)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
