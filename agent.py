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
from smolagents import tool, CodeAgent, LiteLLMModel

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
        model_id=f"ollama/{os.getenv('OLLAMA_AGENT_MODEL', 'qwen2.5-coder:14b')}",
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
def generate_market() -> str:
    """Genera un mercado de 15 jugadores disponibles para fichar,
    excluyendo los jugadores ya presentes en el equipo."""
    from procesador_simple import cargar_mercado
    if not _estado["equipo"]:
        return "Error: primero carga o genera un equipo."
    mercado = cargar_mercado(excluidos=_estado["equipo"])
    _estado["mercado"] = mercado
    nombres = [f"  {p['position']} - {p['name']} ({p['price']})" for p in mercado]
    return f"Mercado generado ({len(mercado)} jugadores):\n" + "\n".join(nombres)


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

    # Resumen compacto para el analista (evita saturar el contexto del LLM)
    def _compact(jugadores, titulo):
        rows = [titulo]
        for p in jugadores:
            rows.append(
                f"  {p.get('position','?')} {p.get('name','?')} | "
                f"{p.get('price','?')} | "
                f"Pts:{p.get('ptos_total',0)} | "
                f"Forma:{p.get('estado_forma','?')} | "
                f"Pts/€:{p.get('ptos_por_euro',0)} | "
                f"Goles:{p.get('goles',0)} | "
                f"Asist:{p.get('asistencias',0)} | "
                f"Mins:{p.get('mins_jugados',0)} | "
                f"Prox:{p.get('prox_partido','?')}"
            )
        return "\n".join(rows)

    resumen = (
        f"[Archivo guardado: {filename}]\n\n"
        + _compact(_estado["equipo"] or [], "EQUIPO:") + "\n\n"
        + _compact(_estado["mercado"] or [], "MERCADO:") + "\n\n"
        + f"ANÁLISIS EQUIPO:\n{analisis_equipo}\n\n"
        + f"ANÁLISIS MERCADO:\n{analisis_mercado}"
    )
    return resumen


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

INSTRUCTIONS = """Eres el agente ejecutor de UCL Fantasy. Responde siempre en español.

Tu objetivo es preparar todos los datos del equipo y mercado para que el analista pueda tomar decisiones.
Tienes estas herramientas disponibles: load_team, generate_team, generate_market, analyze_team, analyze_market, save_result, update_players.

Usa load_team() si existe plantilla.json, o generate_team() si no hay equipo guardado.
Cuando termines, devuelve el contenido completo que retorna save_result, que incluye los datos JSON de todos los jugadores."""


def crear_agente() -> CodeAgent:
    agente = CodeAgent(
        tools=[load_team, generate_team, generate_market, analyze_team,
               analyze_market, save_result],
        model=get_agent_model(),
        instructions=INSTRUCTIONS,
        additional_authorized_imports=["os", "json", "glob"],
        max_steps=8,
        executor_kwargs={"timeout_seconds": 3600},
    )
    # Atributos requeridos para usarse como managed_agent
    agente.name = "ejecutor"
    agente.description = (
        "Agente ejecutor de UCL Fantasy. Carga el equipo del usuario desde plantilla.json "
        "(o genera uno aleatorio si no existe), obtiene el mercado de jugadores disponibles, "
        "analiza ambos con el procesador simple y guarda el resultado en un archivo .txt. "
        "Devuelve el contenido completo del archivo con equipo, mercado y análisis."
    )
    return agente


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
