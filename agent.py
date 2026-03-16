"""
Agente Fantasy UCL — Ejecutor.

Puede usarse de dos formas:
  - Como managed_agent del Analista: recibe una tarea y la ejecuta autónomamente.
  - Standalone: python agent.py (loop interactivo básico).
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from smolagents import tool, CodeAgent, ToolCallingAgent, LiteLLMModel

load_dotenv()


# ---------------------------------------------------------------------------
# Estado compartido entre herramientas
# ---------------------------------------------------------------------------

_estado = {
    "equipo": None,
    "mercado": None,
}


# ---------------------------------------------------------------------------
# Configuración del modelo
# ---------------------------------------------------------------------------

def get_agent_model() -> LiteLLMModel:
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_AGENT_MODEL', 'qwen2.5-coder:7b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Herramientas (@tool)
# ---------------------------------------------------------------------------

@tool
def load_team(filename: str = "plantilla.json") -> str:
    """Carga el equipo desde un archivo JSON guardado por el usuario en la GUI.
    Usar este tool cuando existe el archivo plantilla.json con el equipo elegido.

    Args:
        filename: Nombre del archivo JSON con el equipo (por defecto plantilla.json).
    """
    with open(filename, encoding="utf-8") as f:
        equipo = json.load(f)
    _estado["equipo"] = equipo
    nombres = [f"  {p['position']} - {p['name']} ({p['price']})" for p in equipo]
    return f"Equipo cargado desde {filename} ({len(equipo)} jugadores):\n" + "\n".join(nombres)


@tool
def generate_team() -> str:
    """Genera un equipo aleatorio de 11 jugadores de UCL Fantasy.
    Usar este tool solo si NO existe un archivo plantilla.json con el equipo del usuario."""
    from shuffle import shuffle_team
    equipo = shuffle_team()
    if not equipo:
        return "Error: no se pudo generar el equipo."
    _estado["equipo"] = equipo
    nombres = [f"  {p['position']} - {p['name']} ({p['price']})" for p in equipo]
    return f"Equipo generado ({len(equipo)} jugadores):\n" + "\n".join(nombres)


@tool
def load_market(filename: str = "mercado.json") -> str:
    """Carga el mercado de jugadores desde un archivo JSON generado por el usuario.
    Usar este tool una vez el usuario ha pulsado el botón de generar mercado.

    Args:
        filename: Nombre del archivo JSON (por defecto mercado.json).
    """
    if not os.path.exists(filename):
        return "Error: el mercado aún no ha sido generado desde la UI."
    with open(filename, encoding="utf-8") as f:
        mercado = json.load(f)
    _estado["mercado"] = mercado
    nombres = [f"  {p['position']} - {p['name']} ({p['price']})" for p in mercado]
    return f"Mercado cargado desde {filename} ({len(mercado)} jugadores):\n" + "\n".join(nombres)


@tool
def analyze_team() -> str:
    """Analiza el equipo actual con el procesador simple (qwen3:14b).
    Devuelve un resumen en lenguaje natural."""
    from procesador_simple import procesar_equipo, get_model
    if not _estado["equipo"]:
        return "Error: primero carga o genera un equipo."
    return procesar_equipo(_estado["equipo"], get_model())


@tool
def analyze_market() -> str:
    """Analiza el mercado actual con el procesador simple (qwen3:14b).
    Recomienda los 3 mejores fichajes."""
    from procesador_simple import procesar_mercado, get_model
    if not _estado["mercado"]:
        return "Error: primero genera el mercado con generate_market."
    return procesar_mercado(_estado["mercado"], get_model())


@tool
def save_result(analisis_equipo: str, analisis_mercado: str) -> str:
    """Guarda el resultado completo (equipo, mercado y análisis) en un archivo de texto
    y devuelve el contenido completo del archivo guardado.

    Args:
        analisis_equipo: Texto del análisis del equipo.
        analisis_mercado: Texto del análisis del mercado.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resultado_{timestamp}.txt"

    lines = []
    lines.append(f"=== RESULTADO FANTASY UCL — {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n")

    def _fmt_player(p: dict) -> str:
        fields = [
            f"{p.get('position','?')} - {p.get('name','?')}",
            f"Precio: {p.get('price','?')}",
            f"Pts: {p.get('ptos_total','0')}",
            f"Forma: {p.get('estado_forma','N/A')}",
            f"Goles: {p.get('goles','0')}",
            f"Asist: {p.get('asistencias','0')}",
            f"Mins: {p.get('mins_jugados','0')}",
            f"Equipo: {p.get('team_match','?')}",
        ]
        # Añadir cualquier otro campo que exista en el JSON
        known = {'position','name','price','ptos_total','estado_forma','goles','asistencias','mins_jugados','team_match'}
        extras = {k: v for k, v in p.items() if k not in known}
        if extras:
            fields.append(" | ".join(f"{k}: {v}" for k, v in extras.items()))
        return "  " + " | ".join(fields)

    lines.append("--- EQUIPO ---")
    if _estado["equipo"]:
        for p in _estado["equipo"]:
            lines.append(_fmt_player(p))
    lines.append("")

    lines.append("--- MERCADO ---")
    if _estado["mercado"]:
        for p in _estado["mercado"]:
            lines.append(_fmt_player(p))
    lines.append("")

    lines.append("--- ANÁLISIS DEL EQUIPO ---")
    lines.append(analisis_equipo)
    lines.append("")
    lines.append("--- ANÁLISIS DEL MERCADO ---")
    lines.append(analisis_mercado)

    content = "\n".join(lines)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    resumen_json = {
        "equipo": _estado["equipo"] or [],
        "mercado": _estado["mercado"] or [],
        "analisis_equipo": analisis_equipo,
        "analisis_mercado": analisis_mercado,
        "archivo_guardado": filename
    }
    return json.dumps(resumen_json, ensure_ascii=False)


@tool
def update_players() -> str:
    """Ejecuta el scraping de jugadores de UCL Fantasy desde la web de UEFA.
    Actualiza el archivo players.json. Requiere Chrome y tarda varios minutos."""
    from scrap_champions import scrape_players
    scrape_players()
    with open("players.json", encoding="utf-8") as f:
        players = json.load(f)
    return f"Scraping completado. {len(players)} jugadores guardados en players.json."


@tool
def buscar_noticias_jugador(query: str) -> str:
    """Busca noticias de última hora en internet (vía DuckDuckGo) sobre un jugador o equipo.
    Útil para saber si un jugador está lesionado, sancionado o si hay rumores de fichajes.

    Args:
        query: El término de búsqueda (ej: 'lesion Mbappe hoy', 'alineacion Real Madrid proximo partido').
    """
    try:
        from smolagents import DuckDuckGoSearchTool
        search_tool = DuckDuckGoSearchTool()
        return search_tool(query)
    except Exception as e:
        return f"Error al buscar en internet: {str(e)}"


# ---------------------------------------------------------------------------
# Agente
# ---------------------------------------------------------------------------

def _get_val(p, key, default=0):
    """Helper interno para limpiar y obtener valores numéricos de los JSON."""
    try:
        v = p.get(key, default)
        if isinstance(v, str):
            v = v.replace('m','').replace('%','').replace('€','').strip()
        return float(v) if v else float(default)
    except: return float(default)

@tool
def evaluar_plantilla_actual() -> str:
    """Evalúa SOLO los 11 jugadores de la plantilla actual. 
    Devuelve desglose individual, goleadores, asistentes, recuperadores y balance por líneas.
    """
    base_dir = os.path.dirname(__file__)
    equipo_file = os.path.join(base_dir, "plantilla.json")
    if not os.path.exists(equipo_file):
        return "Error: No hay equipo cargado. Añade jugadores primero."
    
    try:
        with open(equipo_file, encoding="utf-8") as f:
            equipo = json.load(f)
        
        informe = ["=== ANÁLISIS TÉCNICO DE LA PLANTILLA ==="]
        informe.append("\n📋 DESGLOSE INDIVIDUAL:")
        for p in equipo:
            pts = _get_val(p, 'ptos_total')
            prc = _get_val(p, 'price')
            roi = p.get('ptos_por_euro', '?')
            g, a, r = p.get('goles',0), p.get('asistencias',0), p.get('balones_recuperados',0)
            informe.append(f"  - {p['name']} ({p['position']}): {prc}M | {int(pts)} Pts | ROI {roi} | G:{g} A:{a} R:{r}")

        informe.append("\n🔝 LÍDERES ESTADÍSTICOS:")
        top_g = sorted(equipo, key=lambda x: _get_val(x, 'goles'), reverse=True)[:1]
        top_a = sorted(equipo, key=lambda x: _get_val(x, 'asistencias'), reverse=True)[:1]
        top_r = sorted(equipo, key=lambda x: _get_val(x, 'balones_recuperados'), reverse=True)[:1]
        if top_g: informe.append(f"  - Máximo Goleador: {top_g[0]['name']} ({top_g[0].get('goles',0)} G)")
        if top_a: informe.append(f"  - Máximo Asistente: {top_a[0]['name']} ({top_a[0].get('asistencias',0)} A)")
        if top_r: informe.append(f"  - Mejor Recuperador: {top_r[0]['name']} ({top_r[0].get('balones_recuperados',0)} R)")

        informe.append("\n📊 BALANCE POR LÍNEAS (Media Pts):")
        for pos in ['POR', 'DEF', 'CEN', 'DEL']:
            p_pos = [p for p in equipo if p['position'] == pos]
            avg = sum(_get_val(p, 'ptos_total') for p in p_pos)/len(p_pos) if p_pos else 0
            informe.append(f"  - {pos}: {avg:.1f} pts de media")

        return "\n".join(informe)
    except Exception as e:
        return f"Error en evaluación de plantilla: {str(e)}"

@tool
def evaluar_mercado_fichajes() -> str:
    """Analiza SOLO el mercado disponible. Devuelve las mejores oportunidades por ROI.
    """
    base_dir = os.path.dirname(__file__)
    mercado_file = os.path.join(base_dir, "mercado.json")
    if not os.path.exists(mercado_file):
        return "Error: El mercado no ha sido generado."
    
    try:
        with open(mercado_file, encoding="utf-8") as f:
            mercado = json.load(f)
        
        informe = ["=== OPORTUNIDADES DEL MERCADO (Mejor ROI) ==="]
        mejores = sorted(mercado, key=lambda x: _get_val(x, 'ptos_por_euro'), reverse=True)[:5]
        for p in mejores:
            informe.append(f"  - [CHOLLO] {p['name']} ({p['position']}): {p['price']}M | ROI: {p.get('ptos_por_euro','?')}")
        
        return "\n".join(informe)
    except Exception as e:
        return f"Error en evaluación de mercado: {str(e)}"

@tool
def obtener_recomendaciones_cambio() -> str:
    """Sugiere cambios estratégicos (Quién vender y quién fichar).
    Compara el ROI bajo de tu equipo con el ROI alto del mercado.
    """
    base_dir = os.path.dirname(__file__)
    equipo_file = os.path.join(base_dir, "plantilla.json")
    mercado_file = os.path.join(base_dir, "mercado.json")
    
    if not os.path.exists(equipo_file) or not os.path.exists(mercado_file):
        return "Error: Se requieren plantilla y mercado para recomendar cambios."

    try:
        with open(equipo_file, encoding="utf-8") as f: equipo = json.load(f)
        with open(mercado_file, encoding="utf-8") as f: mercado = json.load(f)

        peores_equipo = sorted(equipo, key=lambda x: _get_val(x, 'ptos_por_euro'))[:2]
        mejores_mercado = sorted(mercado, key=lambda x: _get_val(x, 'ptos_por_euro'), reverse=True)[:2]

        informe = ["=== ⚠️ RECOMENDACIONES DE CAMBIO ==="]
        for v, f in zip(peores_equipo, mejores_mercado):
            informe.append(f"  - VENDER: {v['name']} ({v['price']}M, ROI {v.get('ptos_por_euro','?')})")
            informe.append(f"  - FICHAR: {f['name']} ({f['price']}M, ROI {f.get('ptos_por_euro','?')})")
            informe.append(f"  - MOTIVO: Optimización de rentabilidad.")
            informe.append("")
        
        return "\n".join(informe)
    except Exception as e:
        return f"Error en recomendaciones: {str(e)}"


# ---------------------------------------------------------------------------
# Ejecución directa (standalone)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agente = crear_agente()

    print("=== Agente Ejecutor Fantasy UCL ===")
    print("Comandos: analiza mi equipo, actualiza jugadores, (o 'salir')\n")

    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue
        respuesta = agente.run(pregunta)
        print(f"\nEjecutor: {respuesta}\n")
