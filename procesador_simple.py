"""
Agente Analista — sub-agente especializado en análisis de UCL Fantasy.

Expone herramientas de análisis de equipo y mercado que pueden ser usadas
directamente o delegadas por el coordinador (coordinador.py) como managed_agent.

Proveedores soportados (por orden de prioridad en .env):
  - Groq          → GROQ_API_KEY
  - Google AI     → GOOGLE_API_KEY
  - Ollama local  → OLLAMA_MODEL + OLLAMA_BASE_URL (por defecto qwen:7b / localhost:11434)
"""

import json
import random
import os
from dotenv import load_dotenv
from smolagents import tool, ToolCallingAgent, LiteLLMModel

load_dotenv()


# ---------------------------------------------------------------------------
# Configuración del modelo del analista
# ---------------------------------------------------------------------------

def get_model() -> LiteLLMModel:
    """Devuelve un LiteLLMModel según las variables de entorno disponibles."""
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen:7b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Utilidad: cargar mercado (la usa el generador, no es un @tool del analista)
# ---------------------------------------------------------------------------

def cargar_mercado(players_file: str = "players.json", excluidos: list[dict] | None = None) -> list[dict]:
    """Carga jugadores disponibles en el mercado excluyendo los ya seleccionados."""
    with open(players_file, encoding="utf-8") as f:
        players = json.load(f)
    nombres_excluidos = {p.get("name") for p in (excluidos or [])}
    disponibles = [p for p in players if p.get("name") not in nombres_excluidos]
    return random.sample(disponibles, min(15, len(disponibles)))


# ---------------------------------------------------------------------------
# Estado interno del analista
# ---------------------------------------------------------------------------

_datos_analista: dict = {
    "equipo": None,
    "mercado": None,
}


# ---------------------------------------------------------------------------
# Herramientas del agente analista (@tool)
# ---------------------------------------------------------------------------

@tool
def set_team_data(equipo_json: str) -> str:
    """Recibe los datos del equipo en formato JSON para poder analizarlos.

    Args:
        equipo_json: Lista de jugadores del equipo en formato JSON string.
    """
    _datos_analista["equipo"] = json.loads(equipo_json)
    return f"Datos del equipo recibidos: {len(_datos_analista['equipo'])} jugadores."


@tool
def set_market_data(mercado_json: str) -> str:
    """Recibe los datos del mercado en formato JSON para poder analizarlos.

    Args:
        mercado_json: Lista de jugadores del mercado en formato JSON string.
    """
    _datos_analista["mercado"] = json.loads(mercado_json)
    return f"Datos del mercado recibidos: {len(_datos_analista['mercado'])} jugadores."


@tool
def analizar_equipo() -> str:
    """Analiza el equipo cargado y devuelve un resumen en lenguaje natural.
    Describe jugadores destacados, formación y precio medio aproximado."""
    if not _datos_analista["equipo"]:
        return "Error: no hay datos de equipo. Llama primero a set_team_data()."
    model = get_model()
    instruccion = (
        "Eres analista de fantasy fútbol Champions League. Responde siempre en español. "
        "Describe este equipo de 11 jugadores de forma breve y natural (máx. 5 frases). "
        "Menciona 2-3 jugadores destacados por puntos o forma, y el precio medio aproximado."
    )
    messages = [{
        "role": "user",
        "content": [{"type": "text", "text": f"{instruccion}\n{json.dumps(_datos_analista['equipo'], ensure_ascii=False)}"}],
    }]
    return model(messages).content


@tool
def analizar_mercado() -> str:
    """Analiza el mercado cargado y recomienda los 3 mejores fichajes disponibles."""
    if not _datos_analista["mercado"]:
        return "Error: no hay datos de mercado. Llama primero a set_market_data()."
    model = get_model()
    instruccion = (
        "Eres analista de fantasy fútbol Champions League. Responde siempre en español. "
        "De estos jugadores disponibles en el mercado, "
        "recomienda los 3 mejores fichajes de forma breve (máx. 4 frases). "
        "Justifica cada uno en una línea."
    )
    messages = [{
        "role": "user",
        "content": [{"type": "text", "text": f"{instruccion}\n{json.dumps(_datos_analista['mercado'], ensure_ascii=False)}"}],
    }]
    return model(messages).content


# ---------------------------------------------------------------------------
# Funciones de compatibilidad para llamadas directas (sin pasar por el agente)
# ---------------------------------------------------------------------------

def procesar_equipo(equipo: list[dict], model: LiteLLMModel) -> str:
    """Analiza un equipo pasado directamente (sin pasar por el agente)."""
    instruccion = (
        "Eres analista de fantasy fútbol Champions League. Responde siempre en español. "
        "Describe este equipo de 11 jugadores de forma breve y natural (máx. 5 frases). "
        "Menciona 2-3 jugadores destacados por puntos o forma, y el precio medio aproximado."
    )
    messages = [{
        "role": "user",
        "content": [{"type": "text", "text": f"{instruccion}\n{json.dumps(equipo, ensure_ascii=False)}"}],
    }]
    return model(messages).content


def procesar_mercado(mercado: list[dict], model: LiteLLMModel) -> str:
    """Analiza un mercado pasado directamente (sin pasar por el agente)."""
    instruccion = (
        "Eres analista de fantasy fútbol Champions League. Responde siempre en español. "
        "De estos jugadores disponibles en el mercado, "
        "recomienda los 3 mejores fichajes de forma breve (máx. 4 frases). "
        "Justifica cada uno en una línea."
    )
    messages = [{
        "role": "user",
        "content": [{"type": "text", "text": f"{instruccion}\n{json.dumps(mercado, ensure_ascii=False)}"}],
    }]
    return model(messages).content


# ---------------------------------------------------------------------------
# Factory: crea el agente analista como ToolCallingAgent
# ---------------------------------------------------------------------------

def crear_agente_analista() -> ToolCallingAgent:
    """Crea y devuelve el sub-agente analista con sus herramientas de análisis."""
    model = get_model()
    return ToolCallingAgent(
        tools=[set_team_data, set_market_data, analizar_equipo, analizar_mercado],
        model=model,
        max_steps=2,
    )


# ---------------------------------------------------------------------------
# Ejecución directa (para pruebas standalone)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from shuffle import shuffle_team, print_players_table

    model = get_model()

    print("Generando equipo aleatorio...\n")
    equipo = shuffle_team()

    if equipo:
        print("\n=== ANÁLISIS DEL EQUIPO (Agente Analista) ===")
        print(procesar_equipo(equipo, model))

        mercado = cargar_mercado(excluidos=equipo)
        print_players_table(mercado, "MERCADO (15 Jugadores)")

        print("\n=== ANÁLISIS DEL MERCADO (Agente Analista) ===")
        print(procesar_mercado(mercado, model))
