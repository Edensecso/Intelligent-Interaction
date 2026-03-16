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
    Instancia el Agent orquestador (Manager) para análisis automático.
    """
    from agent import evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio, buscar_noticias_jugador
    from smolagents import ToolCallingAgent
    
    INSTRUCTIONS = f"""Eres el Analista Orquestador de UCL Fantasy. Tu misión es dar recomendaciones basadas 100% en DATOS.

REGLAS DE ORO:
1. SIEMPRE RESPONDE EN ESPAÑOL.
2. Usa las herramientas modulares (evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio) según lo que necesites informar.
3. Usa 'buscar_noticias_jugador' para corroborar el estado real de los jugadores.
"""

    model = _get_manager_model()
    
    manager = ToolCallingAgent(
        tools=[evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio, buscar_noticias_jugador],
        model=model,
        instructions=INSTRUCTIONS,
        max_steps=10,
    )
    
    print(f"\n[Analista] Iniciando orquestador modular...")
    resultado = manager.run("Realiza un análisis completo: evalúa mi plantilla, mira el mercado y dame recomendaciones finales.")
    return resultado

def chatear(mensaje: str, historial: list, presupuesto: float) -> tuple[str, list]:
    """
    Versión interactiva del analista para modo Chatbot.
    Cada llamada es "fresca" sin memoria persistente para evitar errores.
    """
    from agent import buscar_noticias_jugador, evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio
    from smolagents import ToolCallingAgent
    
    INSTRUCTIONS = f"""Eres el Analista Quirúrgico de UCL Fantasy. Tu misión es responder EXCLUSIVAMENTE a lo que se te pide usando la herramienta adecuada.

REGLAS DE ORO:
1. SIEMPRE RESPONDE EN ESPAÑOL.
2. MODULARIDAD DE HERRAMIENTAS:
   - Si piden opinión del EQUIPO: Usa 'evaluar_plantilla_actual()'.
   - Si piden opinión del MERCADO: Usa 'evaluar_mercado_fichajes()'.
   - Si piden FICHAJES/RECOMENDACIONES: Usa 'obtener_recomendaciones_cambio()'.
3. BUSCADOR (Contexto Real): Si vas a recomendar un fichaje o evaluar a un crack, usa 'buscar_noticias_jugador(nombre)' para ver si está lesionado o en baja forma. ¡Aporta este valor extra!
4. RESPUESTA QUIRÚRGICA: Si preguntan por el equipo, no hables del mercado. Si preguntan por cambios, no listes a todo el equipo. Solo entrega la sección correspondiente.
5. SIN INTRODUCCIONES: Ve directo al grano con los datos.
6. BASO TODO EN DATOS (G, A, R, ROI).
"""

    model = _get_manager_model()
    
    manager = ToolCallingAgent(
        tools=[evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio, buscar_noticias_jugador],
        model=model,
        instructions=INSTRUCTIONS,
        max_steps=10, # Aumentamos para permitir búsqueda + análisis
    )
    
    prompt_final = f"""MENSAJE DEL USUARIO: {mensaje}

RECUERDA: Identifica la intención del usuario y usa SOLO la herramienta necesaria. Si es relevante, busca noticias del jugador antes de dar el veredicto final.
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

