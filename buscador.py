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
        model_id=f"ollama/{os.getenv('OLLAMA_AGENT_MODEL', 'qwen2.5-coder:7b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


def _get_nl_model() -> LiteLLMModel:
    """Modelo de lenguaje natural para el resumen final."""
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen:7b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Búsqueda y Resumen Directo
# ---------------------------------------------------------------------------

def buscar(pregunta: str) -> str:
    """
    Busca información reciente directamente y devuelve un resumen.
    Optimizado para evitar los lentos loops de agentes anidados.
    """
    search_tool = DuckDuckGoSearchTool()
    
    try:
        # 1. Búsqueda directa (sin agente intermedio)
        print(f"  [Web] Consultando DuckDuckGo: {pregunta}")
        resultados_raw = search_tool(pregunta)
        
        if not resultados_raw or "no results" in str(resultados_raw).lower():
            return "No se han encontrado noticias recientes en la web."
            
        # 2. Resumen con el modelo de lenguaje natural
        model = _get_nl_model()
        
        instruccion = (
            "Eres analista de fantasy fútbol Champions League. Responde siempre en español. "
            "A partir de estos resultados de búsqueda, resume la situación del jugador/equipo: "
            "lesiones, estado de forma, si es titular probable y rendimiento reciente. "
            "Sé muy conciso (máx. 4 frases)."
        )
        
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": f"{instruccion}\n\nResultados:\n{resultados_raw}"}],
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
    except Exception as e:
        return f"Error en la b\u00fasqueda web: {str(e)}"


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
