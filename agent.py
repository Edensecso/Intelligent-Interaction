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


# ---------------------------------------------------------------------------
# Agente
# ---------------------------------------------------------------------------

@tool
def obtener_analisis_squad() -> str:
    """Realiza un pre-análisis estadístico completo de la plantilla y el mercado.
    NO requiere argumentos. Úsala siempre para obtener recomendaciones directas.
    Devuelve un resumen textual con el equipo completo (todos los jugadores con TODAS sus estadísticas)
    y candidatos del mercado para comparación opcional.
    """
    base_dir = os.path.dirname(__file__)
    equipo_file = os.path.join(base_dir, "plantilla.json")
    mercado_file = os.path.join(base_dir, "mercado.json")
    
    try:
        reporte = []
        
        # 1. Cargar Equipo
        if not os.path.exists(equipo_file):
            return "Error: No hay equipo cargado. Añade jugadores al campo."
            
        with open(equipo_file, encoding="utf-8") as f:
            equipo = json.load(f)
            
        reporte.append(f"=== ESTADO DEL EQUIPO ({len(equipo)} jugadores) ===")
        
        def get_val(p, key, default=0):
            try: 
                val = str(p.get(key, default)).replace('m','').replace('%','').strip()
                return float(val) if val else float(default)
            except: return float(default)

        # Mostrar TODO el equipo con TODAS las stats de players.json
        for p in equipo:
            stats = f"Pts:{p.get('ptos_total','0')} | ROI:{p.get('ptos_por_euro','?')} | Frm:{p.get('estado_forma','?')} | G:{p.get('goles','0')} | A:{p.get('asistencias','0')} | R:{p.get('balones_recuperados','0')} | M:{p.get('mins_jugados','0')}"
            if p.get('position') in ['POR', 'DEF']:
                stats += f" | CS:{p.get('porteria_a_0','0')}"
            
            reporte.append(f"[{p['position']}] {p['name']} ({p['price']}) -> {stats}")

        # 2. Cargar Mercado (Solo resumen para no sobrecargar context, salvo que pida mejorar)
        if os.path.exists(mercado_file):
            with open(mercado_file, encoding="utf-8") as f:
                mercado = json.load(f)
            
            reporte.append("\n=== OPORTUNIDADES DEL MERCADO (Solo si se pide mejorar) ===")
            mejores = sorted(mercado, key=lambda x: (get_val(x, "estado_forma", 0), get_val(x, "ptos_por_euro", 0)), reverse=True)[:5]
            for p in mejores:
                reporte.append(f"[SUGERENCIA] {p['name']} ({p['price']}) - Pts: {p['ptos_total']} | ROI: {p.get('ptos_por_euro','?')}")
        else:
            reporte.append("\n[AVISO] No hay mercado generado.")

        return "\n".join(reporte)
        
    except Exception as e:
        return f"Error en el pre-análisis: {str(e)}"


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
