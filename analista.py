"""
Agente Analista — Cerebro del sistema Fantasy UCL.

Punto de entrada principal del sistema. Coordina:
  1. Ejecutar el pipeline de agent.py (equipo + mercado + análisis + .txt)
  2. Buscar información de actualidad sobre jugadores/equipos via buscador.py
  3. Tomar decisiones de fichajes respetando el presupuesto disponible del usuario

Uso:
    python analista.py
"""

import os
from dotenv import load_dotenv
from smolagents import tool, CodeAgent, LiteLLMModel

load_dotenv()


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------

def _get_model() -> LiteLLMModel:
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_AGENT_MODEL', 'qwen2.5-coder:14b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Herramientas
# ---------------------------------------------------------------------------

@tool
def ejecutar_pipeline() -> str:
    """Genera un equipo y mercado aleatorios de UCL Fantasy, los analiza con el
    procesador simple y guarda los resultados en un archivo .txt.
    Devuelve el contenido completo del archivo con el equipo, mercado y análisis."""
    import agent as ag

    # Reset estado compartido del ejecutor
    ag._estado["equipo"] = None
    ag._estado["mercado"] = None

    # Pipeline completo
    ag.generate_team()
    ag.generate_market()
    analisis_equipo = str(ag.analyze_team())
    analisis_mercado = str(ag.analyze_market())
    resultado_msg = str(ag.save_result(analisis_equipo, analisis_mercado))

    # Extraer nombre del archivo y devolver su contenido completo
    # resultado_msg tiene la forma: "Resultado guardado en resultado_xxx.txt"
    filename = resultado_msg.strip().split()[-1]
    with open(filename, encoding="utf-8") as f:
        content = f.read()
    return f"[Archivo guardado: {filename}]\n\n{content}"


@tool
def buscar_jugador(pregunta: str) -> str:
    """Busca información reciente en internet sobre un jugador o equipo concreto.
    Devuelve un resumen en lenguaje natural sobre su forma actual, lesiones,
    goles recientes y próximos rivales relevantes para UCL Fantasy.

    Args:
        pregunta: Consulta sobre el jugador o equipo. Sé específico para obtener
                  mejores resultados (ej: 'Vinicius Jr forma actual Champions League 2025').
    """
    from buscador import buscar
    return buscar(pregunta)


# ---------------------------------------------------------------------------
# Instrucciones del analista
# ---------------------------------------------------------------------------

INSTRUCTIONS = """Eres el analista jefe de UCL Fantasy. Responde siempre en español.

Tu flujo de trabajo es el siguiente:

PASO 1 — Ejecuta el pipeline:
  Llama a `ejecutar_pipeline()` para obtener el equipo actual, el mercado disponible
  y el análisis inicial generado por el procesador simple.

PASO 2 — Identifica candidatos:
  Del contenido del archivo lee:
  - Los jugadores del equipo con peor rendimiento (pocos puntos, mala forma) → candidatos a vender
  - Los jugadores del mercado con mejor rendimiento (muchos puntos, buena forma) → candidatos a fichar

PASO 3 — Busca información de actualidad (opcional pero recomendado):
  Para los 2-3 jugadores más relevantes (top candidatos a vender o fichar), llama a
  `buscar_jugador()` con su nombre y "UCL 2025 forma actual". Esto te dará contexto
  real y reciente para justificar la decisión.

PASO 4 — Toma las decisiones respetando el presupuesto:
  El presupuesto total disponible = dinero del usuario + ingresos por ventas.
  No lo superes en ningún caso.

En tu respuesta final incluye:
  🔴 VENTAS recomendadas: jugador, precio de venta, motivo
  🟢 FICHAJES recomendados: jugador, precio de fichaje, motivo (incluye info web si la tienes)
  💰 BALANCE: ventas totales - fichajes totales = gasto neto vs presupuesto disponible
  📋 RESUMEN: una frase con el objetivo de la operación (mejorar forma, reducir precio, ...)"""


# ---------------------------------------------------------------------------
# Creación del agente
# ---------------------------------------------------------------------------

def crear_analista() -> CodeAgent:
    return CodeAgent(
        tools=[ejecutar_pipeline, buscar_jugador],
        model=_get_model(),
        instructions=INSTRUCTIONS,
        max_steps=10,
        executor_kwargs={"timeout_seconds": 600},
    )


# ---------------------------------------------------------------------------
# Ejecución directa
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Analista UCL Fantasy ===\n")

    presupuesto_str = input("¿Cuánto dinero tienes disponible para fichajes? (ej: 15.5): ").strip()
    try:
        presupuesto = float(presupuesto_str.replace(",", "."))
    except ValueError:
        print("Valor no válido, usando 0M.")
        presupuesto = 0.0

    analista = crear_analista()

    tarea = (
        f"Tengo {presupuesto}M disponibles para fichajes (sin contar lo que ingrese por ventas). "
        "Analiza mi equipo actual y el mercado disponible, busca información reciente sobre "
        "los jugadores más relevantes y recomiéndame qué vender y qué fichar para mejorar "
        "mi plantilla de UCL Fantasy."
    )

    print("\nAnalizando plantilla y mercado...\n")
    resultado = analista.run(tarea)
    print(f"\n{'='*50}\nRECOMENDACIÓN DEL ANALISTA\n{'='*50}\n{resultado}")
