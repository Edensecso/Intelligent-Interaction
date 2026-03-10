"""
Agente Fantasy UCL — Ejecutor de Herramientas.

El CodeAgent orquesta las herramientas: genera equipo/mercado,
llama a procesador_simple.py para análisis, y guarda resultados.
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
    """Modelo para el CodeAgent (genera código)."""
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
def generate_team() -> str:
    """Genera un equipo aleatorio de 11 jugadores de UCL Fantasy.
    Devuelve un resumen con la formación y los nombres de los jugadores."""
    from shuffle import shuffle_team
    equipo = shuffle_team()
    if not equipo:
        return "Error: no se pudo generar el equipo."
    _estado["equipo"] = equipo
    nombres = [f"  {p['position']} - {p['name']} ({p['price']})" for p in equipo]
    return f"Equipo generado ({len(equipo)} jugadores):\n" + "\n".join(nombres)


@tool
def generate_market() -> str:
    """Genera un mercado de 15 jugadores disponibles para fichar.
    Requiere haber generado un equipo primero."""
    from procesador_simple import cargar_mercado
    if not _estado["equipo"]:
        return "Error: primero genera un equipo con generate_team()."
    mercado = cargar_mercado(excluidos=_estado["equipo"])
    _estado["mercado"] = mercado
    nombres = [f"  {p['position']} - {p['name']} ({p['price']})" for p in mercado]
    return f"Mercado generado ({len(mercado)} jugadores):\n" + "\n".join(nombres)


@tool
def analyze_team() -> str:
    """Analiza el equipo actual usando el procesador simple (qwen3:14b).
    Devuelve un resumen en lenguaje natural."""
    from procesador_simple import procesar_equipo, get_model
    if not _estado["equipo"]:
        return "Error: primero genera un equipo con generate_team()."
    model = get_model()
    return procesar_equipo(_estado["equipo"], model)


@tool
def analyze_market() -> str:
    """Analiza el mercado actual usando el procesador simple (qwen3:14b).
    Recomienda los 3 mejores fichajes."""
    from procesador_simple import procesar_mercado, get_model
    if not _estado["mercado"]:
        return "Error: primero genera el mercado con generate_market()."
    model = get_model()
    return procesar_mercado(_estado["mercado"], model)


@tool
def save_result(analisis_equipo: str, analisis_mercado: str) -> str:
    """Guarda el resultado completo (equipo, mercado y análisis) en un archivo de texto.

    Args:
        analisis_equipo: Texto del análisis del equipo.
        analisis_mercado: Texto del análisis del mercado.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resultado_{timestamp}.txt"

    lines = []
    lines.append(f"=== RESULTADO FANTASY UCL — {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n")

    lines.append("--- EQUIPO ---")
    if _estado["equipo"]:
        for p in _estado["equipo"]:
            lines.append(f"  {p['position']} - {p['name']} ({p['price']}) | Pts: {p.get('ptos_total', 0)} | Forma: {p.get('estado_forma', 'N/A')}")
    lines.append("")

    lines.append("--- MERCADO ---")
    if _estado["mercado"]:
        for p in _estado["mercado"]:
            lines.append(f"  {p['position']} - {p['name']} ({p['price']}) | Pts: {p.get('ptos_total', 0)} | Forma: {p.get('estado_forma', 'N/A')}")
    lines.append("")

    lines.append("--- ANÁLISIS DEL EQUIPO ---")
    lines.append(analisis_equipo)
    lines.append("")
    lines.append("--- ANÁLISIS DEL MERCADO ---")
    lines.append(analisis_mercado)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return f"Resultado guardado en {filename}"


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

INSTRUCTIONS = """Eres un asistente experto en UCL Fantasy (Champions League Fantasy).
Responde siempre en español. Usa las herramientas en el orden lógico necesario.
Al finalizar, guarda el resultado con save_result()."""

def crear_agente() -> CodeAgent:
    model = get_agent_model()
    return CodeAgent(
        tools=[generate_team, generate_market, analyze_team, analyze_market,
               update_players, save_result],
        model=model,
        instructions=INSTRUCTIONS,
        executor_kwargs={"timeout_seconds": 600},
    )


if __name__ == "__main__":
    agente = crear_agente()

    print("=== Agente Fantasy UCL ===")
    print("Escribe tu petición (o 'salir' para terminar)\n")

    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue
        respuesta = agente.run(pregunta)
        print(f"\nAgente: {respuesta}\n")
