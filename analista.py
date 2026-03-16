"""
Agente Analista — Cerebro del sistema Fantasy UCL.

Coordina el pipeline completo como un Manager Agent:
  1. Utiliza el sub-agente (ejecutor) para obtener datos del equipo y mercado.
  2. Decide qué jugadores analizar en profundidad.
  3. Utiliza la herramienta de búsqueda para obtener información web sobre ellos.
  4. Genera una recomendación de fichajes y ventas para cumplir con el presupuesto.
"""

import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel, CodeAgent, tool

load_dotenv()


# ---------------------------------------------------------------------------
# Modelo de lenguaje principal (Manager)
# ---------------------------------------------------------------------------

def _get_manager_model() -> LiteLLMModel:
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.3-70b-versatile")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Herramientas Auxiliares del Manager
# ---------------------------------------------------------------------------

@tool
def buscar_noticias_jugadores(nombres: list[str]) -> str:
    """Busca información reciente en internet sobre el estado de forma, lesiones
    y situación actual de una lista de jugadores para el Fantasy de la Champions.
    Usa esta herramienta para conseguir contexto real antes de decidir fichajes.

    Args:
        nombres: Lista de nombres de jugadores a buscar, ej: ["Vinicius", "Haaland"].
    """
    from buscador import buscar
    
    resultados = []
    for nombre in nombres:
        print(f"[Buscador] Buscando: {nombre}...")
        try:
            info = buscar(f"{nombre} forma actual Champions League 2025")
            resultados.append(f"[{nombre}]\n{info}")
        except Exception as e:
            resultados.append(f"[{nombre}]\nError al buscar: {e}")
            
    return "\n\n".join(resultados) if resultados else "Sin información web disponible."


# ---------------------------------------------------------------------------
# Manager Agent
# ---------------------------------------------------------------------------

def analizar(presupuesto: float) -> str:
    """
    Instancia el Agent orquestador (Manager) y lanza la tarea de análisis.

    Args:
        presupuesto: Dinero disponible del usuario en millones (sin contar ventas).
    """
    from agent import generar_informe_detallado, buscar_noticias_jugador
    from smolagents import ToolCallingAgent
    
    INSTRUCTIONS = f"""Eres el Analista Orquestador de un equipo de UCL Fantasy. Tu misión es dar recomendaciones basadas 100% en DATOS.

REGLAS DE ORO:
1. SIEMPRE RESPONDE EN ESPAÑOL.
2. EJECUTA 'generar_informe_detallado()' DE INMEDIATO para obtener los datos.
3. Genera un análisis EXHAUSTIVO basado en Goles, Asistencias, Recuperaciones y ROI.
4. BASA TU VEREDICTO EN DATOS, no seas genérico. NO PIDAS ARCHIVOS.
"""

    model = _get_manager_model()
    
    manager = CodeAgent(
        tools=[buscar_noticias_jugadores, obtener_analisis_squad, buscar_noticias_jugador],
        model=model,
        instructions=INSTRUCTIONS,
        additional_authorized_imports=["json"],
        max_steps=10,
        executor_kwargs={"timeout_seconds": 3600},
    )
    
    print(f"\n[Analista] Iniciando orquestador CodeAgent con {presupuesto}M de presupuesto...")
    resultado = manager.run("Realiza el análisis y devuelve la recomendación final estructurada.")
    return resultado

def chatear(mensaje: str, historial: list, presupuesto: float) -> tuple[str, list]:
    """
    Versión interactiva del analista para modo Chatbot.
    Cada llamada es "fresca" sin memoria persistente para evitar errores.
    """
    from agent import buscar_noticias_jugador, generar_informe_detallado
    from smolagents import ToolCallingAgent
    
    INSTRUCTIONS = f"""Eres el Analista Experto de UCL Fantasy. Tu misión es dar opiniones TÉCNICAS y ESTADÍSTICAS basadas en DATOS.

REGLAS DE ORO:
1. SIEMPRE RESPONDE EN ESPAÑOL. Es innegociable.
2. NO PIDAS ARCHIVOS NI RUTAS. Ya tienes las herramientas para leer 'plantilla.json' automáticamente.
3. EJECUTA 'generar_informe_detallado()' DE INMEDIATO para obtener los datos.
4. BASA TU OPINIÓN EN: Puntos, Precio, ROI, Goles (G), Asistencias (A) y Recuperaciones (R).
5. FORMATO DE RESPUESTA OBLIGATORIO:
   - 📋 ANÁLISIS INDIVIDUAL (Lista los 11 jugadores): 
     * [Nombre]: [Price]M | [Pts] Pts | G:[G] A:[A] R:[R]. -> Veredicto estadístico claro.
   - 🏆 CONCLUSIÓN TÉCNICA
   - ⚠️ RECOMENDACIONES CLAVE
6. NO des explicaciones previas. Solo ejecuta la herramienta y entrega el informe estadístico.
"""

    model = _get_manager_model()
    
    manager = ToolCallingAgent(
        tools=[generar_informe_detallado, buscar_noticias_jugador],
        model=model,
        instructions=INSTRUCTIONS,
        max_steps=5,
    )
    
    prompt_final = f"""[TRANSACCIÓN ÚNICA - SIN MEMORIA]
PRESUPUESTO ACTUAL: {presupuesto}M
MENSAJE DEL USUARIO: {mensaje}

Instrucción final: Ejecuta 'generar_informe_detallado' y genera el informe estadístico exhaustivo solicitado.
"""
    
    resultado = manager.run(prompt_final)
    
    # Actualizar historial
    historial.append({"role": "user", "content": mensaje})
    historial.append({"role": "assistant", "content": str(resultado)})
    
    return str(resultado), historial


# ---------------------------------------------------------------------------
# Ejecución directa
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Manager Orquestador UCL Fantasy ===\n")

    presupuesto_str = input("¿Cuánto dinero tienes disponible para fichajes? (ej: 15.5): ").strip()
    try:
        presupuesto = float(presupuesto_str.replace(",", "."))
    except ValueError:
        print("Valor no válido, usando 0M.")
        presupuesto = 0.0

    print("\nAnalizando plantilla y mercado...\n")
    resultado = analizar(presupuesto)
    print(f"\n{'='*50}\nRECOMENDACIÓN FINAL DEL MANAGER\n{'='*50}\n{resultado}")

