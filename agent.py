"""
Agente Fantasy UCL — Ejecutor de Herramientas + Procesador Simple delegado.

El CodeAgent orquesta las herramientas (generar equipo, mercado, scraping).
Cuando necesita analizar datos, delega al agente procesador_simple.
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from smolagents import tool, CodeAgent, LiteLLMModel

load_dotenv()


# ---------------------------------------------------------------------------
# Estado compartido entre herramientas (el agente no ve los JSON)
# ---------------------------------------------------------------------------

_estado = {
    "equipo": None,   # list[dict] — 11 jugadores
    "mercado": None,  # list[dict] — 15 jugadores
}


# ---------------------------------------------------------------------------
# Configuración de modelos
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


def get_proc_model() -> LiteLLMModel:
    """Modelo para el procesador simple (lenguaje natural)."""
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen3:14b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Herramientas del procesador simple (para el agente subordinado)
# ---------------------------------------------------------------------------

@tool
def get_team_data() -> str:
    """Devuelve los datos completos del equipo actual en formato JSON
    para que el procesador los analice."""
    if not _estado["equipo"]:
        return "No hay equipo generado."
    return json.dumps(_estado["equipo"], ensure_ascii=False)


@tool
def get_market_data() -> str:
    """Devuelve los datos completos del mercado actual en formato JSON
    para que el procesador los analice."""
    if not _estado["mercado"]:
        return "No hay mercado generado."
    return json.dumps(_estado["mercado"], ensure_ascii=False)


# ---------------------------------------------------------------------------
# Herramientas del agente principal (ejecutor)
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
def save_result(analisis_equipo: str, analisis_mercado: str) -> str:
    """Guarda el resultado completo (equipo, mercado y análisis) en un archivo de texto.
    Llama a esta herramienta al final, después de tener los análisis.

    Args:
        analisis_equipo: Texto del análisis del equipo generado por el procesador simple.
        analisis_mercado: Texto del análisis del mercado generado por el procesador simple.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resultado_{timestamp}.txt"

    lines = []
    lines.append(f"=== RESULTADO FANTASY UCL — {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n")

    # Equipo
    lines.append("--- EQUIPO ---")
    if _estado["equipo"]:
        for p in _estado["equipo"]:
            lines.append(f"  {p['position']} - {p['name']} ({p['price']}) | Pts: {p.get('ptos_total', 0)} | Forma: {p.get('estado_forma', 'N/A')}")
    lines.append("")

    # Mercado
    lines.append("--- MERCADO ---")
    if _estado["mercado"]:
        for p in _estado["mercado"]:
            lines.append(f"  {p['position']} - {p['name']} ({p['price']}) | Pts: {p.get('ptos_total', 0)} | Forma: {p.get('estado_forma', 'N/A')}")
    lines.append("")

    # Análisis
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
    Actualiza el archivo players.json con los datos más recientes.
    AVISO: requiere Chrome instalado y tarda varios minutos."""
    from scrap_champions import scrape_players
    scrape_players()
    with open("players.json", encoding="utf-8") as f:
        players = json.load(f)
    return f"Scraping completado. {len(players)} jugadores guardados en players.json."


# ---------------------------------------------------------------------------
# Creación de agentes
# ---------------------------------------------------------------------------

INSTRUCTIONS = """Eres un asistente experto en UCL Fantasy (Champions League Fantasy).
Responde siempre en español. Cuando el usuario pida algo relacionado con su equipo,
usa las herramientas en el orden lógico necesario.
Para analizar el equipo o el mercado, delega al agente 'procesador_simple'.
Al finalizar, guarda todo el resultado en un archivo de texto con save_result()."""


def crear_procesador_simple() -> CodeAgent:
    """Crea el agente procesador simple: analiza equipo y mercado en lenguaje natural."""
    return CodeAgent(
        tools=[get_team_data, get_market_data],
        model=get_proc_model(),
        name="procesador_simple",
        description=(
            "Agente analista de fantasy fútbol. Llámalo cuando necesites un análisis "
            "en lenguaje natural del equipo actual o del mercado. "
            "Sabe obtener los datos internamente, solo dile qué quieres analizar."
        ),
        instructions=(
            "Eres un analista experto de UCL Fantasy. Responde siempre en español. "
            "Usa get_team_data() u get_market_data() para acceder a los datos "
            "y proporciona análisis breves y útiles."
        ),
    )


def crear_agente() -> CodeAgent:
    """Crea el agente principal (orquestador)."""
    procesador = crear_procesador_simple()
    model = get_agent_model()
    return CodeAgent(
        tools=[generate_team, generate_market, update_players, save_result],
        model=model,
        managed_agents=[procesador],
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
