"""
Procesador Simple — interfaz de lenguaje natural para los resultados de shuffle.py.

El LLM recibe los datos completos de cada jugador y devuelve una presentación
natural y amigable para el usuario.

Proveedores soportados (por orden de prioridad en .env):
  - Groq          → GROQ_API_KEY
  - Google AI     → GOOGLE_API_KEY
  - Ollama local  → OLLAMA_MODEL + OLLAMA_BASE_URL (por defecto qwen3:14b / localhost:11434)
"""

import json
import random
import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel

load_dotenv()


# ---------------------------------------------------------------------------
# Configuración del modelo
# ---------------------------------------------------------------------------

def get_model() -> LiteLLMModel:
    """Devuelve un LiteLLMModel según las variables de entorno disponibles."""
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    # Fallback: Ollama local
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen3:4b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _llamar_llm(model: LiteLLMModel, instruccion: str, datos: list[dict] | dict) -> str:
    """Envía una petición al LLM y devuelve el texto de respuesta."""
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": f"{instruccion}\n{json.dumps(datos, ensure_ascii=False)}"}],
        }
    ]
    respuesta = model(messages)
    content = respuesta.content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)


# ---------------------------------------------------------------------------
# Funciones públicas del procesador
# ---------------------------------------------------------------------------

def procesar_equipo(equipo: list[dict], model: LiteLLMModel) -> str:
    """
    Recibe la lista de 11 jugadores de shuffle_team() y devuelve
    un resumen natural del equipo.
    """
    instruccion = (
        "IMPORTANTE: Responde ÚNICAMENTE en español. "
        "Eres analista de fantasy fútbol Champions League. "
        "Describe este equipo de 11 jugadores de forma breve y natural (máx. 5 frases). "
        "Menciona 2-3 jugadores destacados por puntos o forma, y el precio medio aproximado."
    )
    return _llamar_llm(model, instruccion, equipo)


def procesar_mercado(mercado: list[dict], model: LiteLLMModel) -> str:
    """
    Recibe la lista de jugadores del mercado y devuelve
    las mejores recomendaciones de fichaje.
    """
    instruccion = (
        "IMPORTANTE: Responde ÚNICAMENTE en español. "
        "Eres analista de fantasy fútbol Champions League. "
        "De estos jugadores disponibles en el mercado, "
        "recomienda los 3 mejores fichajes de forma breve (máx. 4 frases). "
        "Justifica cada uno en una línea."
    )
    return _llamar_llm(model, instruccion, mercado)


def procesar_cambios(equipo: list[dict], mercado: list[dict], model: LiteLLMModel) -> str:
    """
    Analiza el equipo y el mercado simultáneamente para sugerir cambios.
    """
    datos = {"equipo": equipo, "mercado": mercado}
    instruccion = (
        "IMPORTANTE: Responde ÚNICAMENTE en español. "
        "Eres un analista experto de fantasy fútbol Champions League. "
        "Analiza mi equipo actual y las opciones disponibles en el mercado. "
        "Sugiere 2 o 3 cambios concretos (VENDER -> COMPRAR) que mejoren el equipo a corto plazo. "
        "Justifica brevemente la decisión basada en puntos, forma o valoración."
    )
    # _llamar_llm espera una lista de dicts o un objeto serializable
    # Modificamos _llamar_llm para aceptar cualquier objeto serializable
    return _llamar_llm(model, instruccion, datos)


def cargar_mercado(players_file: str = "players.json", excluidos: list[dict] | None = None) -> list[dict]:
    """
    Carga jugadores disponibles en el mercado excluyendo los ya seleccionados.
    Equivalente al muestreo de shuffle_mercado pero devuelve la lista.
    """
    with open(players_file, encoding="utf-8") as f:
        players = json.load(f)
    nombres_excluidos = {p.get("name") for p in (excluidos or [])}
    disponibles = [p for p in players if p.get("name") not in nombres_excluidos]
    return random.sample(disponibles, min(15, len(disponibles)))


# ---------------------------------------------------------------------------
# Ejecución directa
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from shuffle import shuffle_team, print_players_table

    model = get_model()

    print("Generando equipo aleatorio...\n")
    equipo = shuffle_team()

    if equipo:
        print("\n=== ANÁLISIS DEL EQUIPO (Procesador Simple) ===")
        print(procesar_equipo(equipo, model))

        mercado = cargar_mercado(excluidos=equipo)
        print_players_table(mercado, "MERCADO (15 Jugadores)")

        print("\n=== ANÁLISIS DEL MERCADO (Procesador Simple) ===")
        print(procesar_mercado(mercado, model))
