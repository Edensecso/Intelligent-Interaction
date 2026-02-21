import json
import random

def shuffle_team(players_file="players.json"):
    """
    Lee jugadores de un archivo JSON, elige una alineación aleatoria y selecciona
    aleatoriamente un equipo válido de 11 jugadores, mostrando la media de 
    sus estadísticas clave.
    """
    with open(players_file, 'r', encoding='utf-8') as f:
        players = json.load(f)
        
    # Separar jugadores por posición según indica el JSON
    por_list = [p for p in players if p.get('position') == 'POR']
    def_list = [p for p in players if p.get('position') == 'DEF']
    cen_list = [p for p in players if p.get('position') == 'CEN']
    del_list = [p for p in players if p.get('position') == 'DEL']
    
    # Formaciones posibles
    formations = ['541', '532', '451', '442', '433', '352', '343']
    
    # Elegir "1 aleatoria"
    chosen_formation = random.choice(formations)
    
    # Parsear formación para obtener número de jugadores por línea
    num_def = int(chosen_formation[0])
    num_cen = int(chosen_formation[1])
    num_del = int(chosen_formation[2])
    num_por = 1 # Siempre hay 1 portero en un equipo de 11
    
    print(f"Formación elegida aleatoriamente: {chosen_formation}")
    
    # "Se va de 'position' en position escogiendo aleatoriamente un jugador que encaje ahí"
    try:
        selected_por = random.sample(por_list, num_por)
        selected_def = random.sample(def_list, num_def)
        selected_cen = random.sample(cen_list, num_cen)
        selected_del = random.sample(del_list, num_del)
    except ValueError as e:
        print("Error: No hay suficientes jugadores en alguna posición para formar el equipo.")
        return
        
    team = selected_por + selected_def + selected_cen + selected_del
    
    print_players_table(team, "EQUIPO SELECCIONADO")
    return team

def print_players_table(team, title):
    stats_keys = [
        'ptos_total', 'ptos_jornada', 'ptos_por_euro', 'ptos_per_md', 'ptos_potm',
        'goles', 'asistencias', 'balones_recuperados', 'porteria_a_0', 
        'tarjetas_rojas', 'tarjetas_amarillas', 'mins_jugados'
    ]
    
    headers_map = {
        'ptos_total': 'P.Tot', 'ptos_jornada': 'P.Jor', 'ptos_por_euro': 'P/Eur', 
        'ptos_per_md': 'P/MD', 'ptos_potm': 'POTM', 'goles': 'Gls', 
        'asistencias': 'Asi', 'balones_recuperados': 'Recup', 'porteria_a_0': 'P.a.0', 
        'tarjetas_rojas': 'T.Roj', 'tarjetas_amarillas': 'T.Ama', 'mins_jugados': 'Mins'
    }
    
    print(f"\n--- {title} ---")
    header_cols = [f"{'POS':<3}", f"{'Nombre':<18}", f"{'Partido':<16}", f"{'Precio':>6}"]
    header_cols += [f"{headers_map[k]:>5}" for k in stats_keys]
    header = " | ".join(header_cols)
    print(header)
    print("-" * len(header))
    
    team_stats_sum = {key: 0.0 for key in stats_keys}
    prices = []
    
    for p in team:
        nombre = p.get('name', 'Desconocido')
        # Acortar nombre si es muy largo para no descoladrar
        if len(nombre) > 18:
            nombre = nombre[:15] + "..."
            
        posicion = p.get('position', '')
        precio = p.get('price', '0m')
        
        team_match = p.get('team_match', '')
        prox_partido = p.get('prox_partido', '')
        
        # Extraer equipo
        equipo = ""
        rival_limpio = prox_partido.split(' ')[0] if ' ' in prox_partido else prox_partido.strip()
        
        if '-' in team_match:
            equipos_en_partido = [e.strip() for e in team_match.split('-')]
            if rival_limpio in equipos_en_partido:
                equipos_en_partido.remove(rival_limpio)
                equipo = equipos_en_partido[0] if equipos_en_partido else rival_limpio
            else:
                equipo = equipos_en_partido[0]
        else:
            equipo = team_match.strip()
            
        if prox_partido and prox_partido != "-":
            cajita_partido = f"[{equipo} 🆚 {prox_partido}]"
        else:
            cajita_partido = f"[{equipo} 🆚 Sin part.]"
            
        # Acortar cajita si es muy larga
        if len(cajita_partido) > 16:
            cajita_partido = cajita_partido[:14] + "]"  # type: ignore
            
        row_cols = [f"{posicion:<3}", f"{nombre:<18}", f"{cajita_partido:<16}", f"{precio:>6}"]
        
        for key in stats_keys:
            val = str(p.get(key, "0"))
            if val == "-": val = "0"
            try:
                team_stats_sum[key] += float(val)  # type: ignore
            except ValueError:
                pass
            
            row_cols.append(f"{val:>5}")
            
        print(" | ".join(row_cols))
        
        price_str = precio.replace('m', '').strip()
        try:
            prices.append(float(price_str))  # type: ignore
        except ValueError:
            pass
            
    print("-" * len(header))
    
    total_price = sum(prices)
    num_players = len(team) if len(team) > 0 else 1
    
    avg_cols = [f"{'AVG':<3}", f"{'':<18}", f"{'':<16}", f"{total_price/num_players:>5.1f}m"]
    for key in stats_keys:
        avg = team_stats_sum[key] / num_players
        avg_cols.append(f"{avg:>5.1f}")
        
    print(" | ".join(avg_cols))

def shuffle_mercado(players_file="players.json", excluded_team=None):
    """
    Lee jugadores de un archivo JSON, y selecciona 15 jugadores aleatorios 
    para el mercado, excluyendo los que ya están en el equipo.
    """
    if excluded_team is None:
        excluded_team = []
        
    with open(players_file, 'r', encoding='utf-8') as f:
        players = json.load(f)
        
    nombres_excluidos = {p.get('name') for p in excluded_team}
    jugadores_disponibles = [p for p in players if p.get('name') not in nombres_excluidos]
    
    try:
        mercado = random.sample(jugadores_disponibles, 15)
    except ValueError:
        print("Error: No hay suficientes jugadores para formar el mercado.")
        return
        
    print_players_table(mercado, "MERCADO (15 Jugadores)")


if __name__ == "__main__":
    equipo_usuario = shuffle_team()
    if equipo_usuario:
        shuffle_mercado(excluded_team=equipo_usuario)
