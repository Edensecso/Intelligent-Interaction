"""
Agente Analista — Cerebro del sistema Fantasy UCL.

Punto de entrada principal del sistema. Coordina:
  1. Delega en el ejecutor (agent.py) para generar equipo/mercado, analizar y guardar .txt
  2. Busca información de actualidad sobre jugadores/equipos via buscador.py
  3. Toma decisiones de fichajes respetando el presupuesto disponible del usuario

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
# Herramientas propias del analista
# ---------------------------------------------------------------------------

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

REGLA CRÍTICA: Toda acción debe ir dentro de un bloque <code>...</code> y terminar con final_answer().
NUNCA generes texto fuera de bloques de código. Ejemplo de respuesta correcta:

<code>
datos = ejecutor("Prepara los datos del equipo y mercado.")
import glob
archivo = sorted(glob.glob("resultado_*.txt"))[-1]
with open(archivo, encoding="utf-8") as f:
    contenido = f.read()
info = buscar_jugador("¿Cuál es la forma actual de Erling Haaland en la UCL?")
final_answer("🔴 VENTAS: ...\n🟢 FICHAJES: ...\n💰 BALANCE: ...\n📋 RESUMEN: ...")
</code>

Tienes dos recursos:
- El agente `ejecutor`: prepara datos del equipo y mercado y guarda resultado_*.txt con todos los campos.
- La herramienta `buscar_jugador`: recibe una pregunta en lenguaje natural y devuelve info reciente de internet.

OBLIGATORIO: Usa buscar_jugador las veces necesarias. La búsqueda web es CLAVE para tomar buenas decisiones:
   sin información actual (lesiones, rachas, próximos rivales) no puedes hacer una recomendación fiable.
   Ejemplo: buscar_jugador("¿Está lesionado Vinicius Jr y cuál es su forma en la UCL 2025?")
   Combina los datos estadísticos del archivo con la información web para justificar cada decisión.

El presupuesto total = dinero del usuario + ingresos por ventas. No lo superes.

Respuesta final en final_answer():
  🔴 VENTAS recomendadas: jugador, precio, motivo (con dato estadístico + contexto web)
  🟢 FICHAJES recomendados: jugador, precio, motivo (con dato estadístico + contexto web)
  💰 BALANCE económico final
  📋 RESUMEN del objetivo"""


# ---------------------------------------------------------------------------
# Creación del analista con el ejecutor como managed_agent
# ---------------------------------------------------------------------------

def crear_analista() -> CodeAgent:
    from agent import crear_agente
    ejecutor = crear_agente()

    return CodeAgent(
        tools=[buscar_jugador],
        model=_get_model(),
        managed_agents=[ejecutor],
        instructions=INSTRUCTIONS,
        additional_authorized_imports=["json", "glob", "os"],
        max_steps=10,
        executor_kwargs={"timeout_seconds": 3600},
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
        f"Tengo {presupuesto}M disponibles para fichajes (sin contar ingresos por ventas). "
        "Analiza mi equipo actual y el mercado disponible, busca información reciente sobre "
        "los jugadores más relevantes y recomiéndame qué vender y qué fichar para mejorar "
        "mi plantilla de UCL Fantasy."
    )

    print("\nAnalizando plantilla y mercado...\n")
    resultado = analista.run(tarea)
    print(f"\n{'='*50}\nRECOMENDACIÓN DEL ANALISTA\n{'='*50}\n{resultado}")
