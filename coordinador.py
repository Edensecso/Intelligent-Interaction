"""
Coordinador — Orquestador principal del sistema multi-agente UCL Fantasy.

Herramientas directas (no pasan por sub-agente, son llamadas Python puras):
  - generate_team()   → genera 11 jugadores aleatorios
  - generate_market() → genera 15 jugadores disponibles
  - save_result()     → guarda el informe completo en .txt
  - update_players()  → scraping de UEFA

Sub-agentes (requieren razonamiento LLM, por eso van como ManagedAgent):
  - analista → analiza equipo y mercado en lenguaje natural
"""

import json
import os
import random
from datetime import datetime
from dotenv import load_dotenv
from smolagents import tool, ToolCallingAgent, LiteLLMModel

load_dotenv()

# ---------------------------------------------------------------------------
# Estado compartido de la sesión
# ---------------------------------------------------------------------------

_estado = {
    "equipo": None,
    "mercado": None,
}


# ---------------------------------------------------------------------------
# Configuración del modelo del coordinador
# ---------------------------------------------------------------------------

def get_model() -> LiteLLMModel:
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_AGENT_MODEL', 'qwen2.5-coder:7b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Herramientas directas del coordinador
# (son Python puro, no pasan por ningún sub-agente para mayor fiabilidad)
# ---------------------------------------------------------------------------

@tool
def generate_team() -> str:
    """Genera un equipo aleatorio de 11 jugadores de UCL Fantasy.
    Selecciona jugadores del archivo players.json con una formación aleatoria.
    Devuelve la lista de jugadores con posición y precio."""
    from shuffle import shuffle_team
    equipo = shuffle_team()
    if not equipo:
        return "Error: no se pudo generar el equipo."
    _estado["equipo"] = equipo
    lineas = [f"  {p['position']} - {p['name']} ({p['price']})" for p in equipo]
    return "Equipo generado:\n" + "\n".join(lineas)


@tool
def generate_market() -> str:
    """Genera un mercado de 15 jugadores disponibles para fichar en UCL Fantasy.
    Excluye los jugadores ya presentes en el equipo actual.
    Devuelve la lista de jugadores disponibles con posición y precio."""
    if not _estado["equipo"]:
        return "Error: primero genera un equipo con generate_team."
    with open("players.json", encoding="utf-8") as f:
        todos = json.load(f)
    nombres_equipo = {p.get("name") for p in _estado["equipo"]}
    disponibles = [p for p in todos if p.get("name") not in nombres_equipo]
    mercado = random.sample(disponibles, min(15, len(disponibles)))
    _estado["mercado"] = mercado
    lineas = [f"  {p['position']} - {p['name']} ({p['price']})" for p in mercado]
    return "Mercado generado:\n" + "\n".join(lineas)


@tool
def analyze_team() -> str:
    """Analiza el equipo actual usando el sub-agente analista.
    Devuelve un resumen en lenguaje natural con los jugadores más destacados."""
    if not _estado["equipo"]:
        return "Error: primero genera un equipo con generate_team."
    from procesador_simple import procesar_equipo, get_model as get_analista_model
    return procesar_equipo(_estado["equipo"], get_analista_model())


@tool
def analyze_market() -> str:
    """Analiza el mercado actual usando el sub-agente analista.
    Recomienda los 3 mejores fichajes disponibles."""
    if not _estado["mercado"]:
        return "Error: primero genera el mercado con generate_market."
    from procesador_simple import procesar_mercado, get_model as get_analista_model
    return procesar_mercado(_estado["mercado"], get_analista_model())


@tool
def save_result(analisis_equipo: str, analisis_mercado: str) -> str:
    """Guarda el informe completo de UCL Fantasy en un archivo de texto.

    Args:
        analisis_equipo: Texto del análisis del equipo en lenguaje natural.
        analisis_mercado: Texto del análisis del mercado con recomendaciones.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resultado_{timestamp}.txt"
    lines = [f"=== RESULTADO FANTASY UCL — {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n"]

    lines.append("--- EQUIPO ---")
    for p in (_estado["equipo"] or []):
        lines.append(
            f"  {p.get('position','?')} - {p.get('name','?')} ({p.get('price','?')}) "
            f"| Pts: {p.get('ptos_total', 0)}"
        )
    lines.append("")

    lines.append("--- MERCADO ---")
    for p in (_estado["mercado"] or []):
        lines.append(
            f"  {p.get('position','?')} - {p.get('name','?')} ({p.get('price','?')}) "
            f"| Pts: {p.get('ptos_total', 0)}"
        )
    lines.append("")

    lines.append("--- ANÁLISIS DEL EQUIPO ---")
    lines.append(analisis_equipo)
    lines.append("")
    lines.append("--- ANÁLISIS DEL MERCADO ---")
    lines.append(analisis_mercado)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return f"✅ Resultado guardado en {filename}"


@tool
def update_players() -> str:
    """Ejecuta el scraping de jugadores de UCL Fantasy desde la web de UEFA.
    Actualiza el archivo players.json con los datos más recientes.
    Requiere Chrome instalado y puede tardar varios minutos."""
    from scrap_champions import scrape_players
    scrape_players()
    with open("players.json", encoding="utf-8") as f:
        players = json.load(f)
    return f"Scraping completado. {len(players)} jugadores guardados en players.json."


# ---------------------------------------------------------------------------
# Instrucciones del coordinador
# ---------------------------------------------------------------------------

INSTRUCTIONS = """Eres el coordinador de un asistente de UCL Fantasy (Champions League Fantasy).
Responde siempre en español.

Tienes estas herramientas directas:
- generate_team: genera un equipo de 11 jugadores aleatorios.
- generate_market: genera 15 jugadores disponibles para fichar.
- analyze_team: analiza el equipo en lenguaje natural.
- analyze_market: recomienda los 3 mejores fichajes del mercado.
- save_result: guarda el informe completo en un archivo .txt.
- update_players: actualiza los datos de jugadores de UEFA.

REGLA: usa ÚNICAMENTE la herramienta que el usuario ha pedido explícitamente y detente.
No encadenes varias herramientas a la vez salvo que el usuario lo pida."""


# ---------------------------------------------------------------------------
# Factory del coordinador
# ---------------------------------------------------------------------------

def crear_coordinador() -> ToolCallingAgent:
    """Crea el coordinador con todas las herramientas directas."""
    return ToolCallingAgent(
        tools=[
            generate_team,
            generate_market,
            analyze_team,
            analyze_market,
            save_result,
            update_players,
        ],
        model=get_model(),
        instructions=INSTRUCTIONS,
        max_steps=1,
    )


# ---------------------------------------------------------------------------
# Ejecución directa (para pruebas standalone)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    coordinador = crear_coordinador()

    print("=== Coordinador Fantasy UCL ===")
    print("Herramientas: genera equipo / genera mercado / analiza equipo / analiza mercado / guarda resultado / actualiza jugadores")
    print("(escribe 'salir' para terminar)\n")

    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue
        respuesta = coordinador.run(pregunta)
        print(f"\nCoordinador: {respuesta}\n")
