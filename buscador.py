"""
Agente Buscador Web — Fantasy UCL.

Flujo en dos fases:
  1. CodeAgent (qwen2.5-coder) usa DuckDuckGo para obtener resultados recientes.
  2. LLM de lenguaje natural (qwen3:14b) resume la información explicando
     la condición actual del jugador o equipo consultado.
"""

import os
from dotenv import load_dotenv
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

load_dotenv()


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

def _get_coder_model() -> LiteLLMModel:
    """Modelo para el CodeAgent que ejecuta la búsqueda."""
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_AGENT_MODEL', 'qwen2.5-coder:14b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


def _get_nl_model() -> LiteLLMModel:
    """Modelo de lenguaje natural para el resumen final."""
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen3:14b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Fase 1: búsqueda web
# ---------------------------------------------------------------------------

_SEARCH_INSTRUCTIONS = """Eres un agente de búsqueda especializado en fútbol de la Champions League.
Tu única tarea es buscar información reciente sobre el jugador o equipo indicado.
Realiza la búsqueda y devuelve los resultados crudos tal como los encuentras, sin resumir."""


def _buscar_raw(pregunta: str) -> str:
    """Lanza el CodeAgent para obtener resultados de búsqueda en crudo."""
    agente = CodeAgent(
        tools=[DuckDuckGoSearchTool()],
        model=_get_coder_model(),
        instructions=_SEARCH_INSTRUCTIONS,
        max_steps=3,
    )
    return agente.run(f"Busca información reciente sobre: {pregunta}")


# ---------------------------------------------------------------------------
# Fase 2: resumen en lenguaje natural
# ---------------------------------------------------------------------------

_RESUMEN_INSTRUCCION = (
    "Eres analista de fantasy fútbol Champions League. Responde siempre en español. "
    "A partir de los resultados de búsqueda web que te proporciono, explica en lenguaje natural "
    "la condición actual del jugador o equipo: forma reciente, lesiones, goles o asistencias "
    "destacadas, próximos partidos relevantes. Sé conciso (máx. 6 frases) y útil para "
    "tomar decisiones en UCL Fantasy."
)


def _resumir(resultados_raw: str, pregunta: str) -> str:
    """Pasa los resultados crudos al LLM de lenguaje natural para resumirlos."""
    model = _get_nl_model()
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"{_RESUMEN_INSTRUCCION}\n\n"
                        f"Pregunta original: {pregunta}\n\n"
                        f"Resultados de búsqueda:\n{resultados_raw}"
                    ),
                }
            ],
        }
    ]
    respuesta = model(messages)
    return respuesta.content


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def buscar(pregunta: str) -> str:
    """
    Busca información reciente sobre un jugador o equipo y devuelve
    un resumen en lenguaje natural explicando su condición actual.
    """
    resultados_raw = _buscar_raw(pregunta)
    return _resumir(resultados_raw, pregunta)


# ---------------------------------------------------------------------------
# Ejecución directa
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Agente Buscador Web UCL ===")
    print("Escribe una pregunta sobre un jugador o equipo (o 'salir' para terminar)\n")

    while True:
        pregunta = input("Pregunta: ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue

        print("\nBuscando informacion reciente...\n")
        respuesta = buscar(pregunta)
        print(f"Resultado:\n{respuesta}\n")
