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
    from agent import obtener_analisis_squad
    
    INSTRUCTIONS = f"""Eres el Analista Orquestador de un equipo de UCL Fantasy. 
Tu objetivo es dar una recomendación final de fichajes y ventas con las herramientas que tienes.

PRESUPUESTO DISPONIBLE INICIAL: {presupuesto}M€ (tus ventas te darán más dinero para fichar).

Pasos obligatorios a seguir:
1. SIEMPRE RESPONDE EN ESPAÑOL. NUNCA USES INGLÉS.
2. EJECUTA 'obtener_analisis_squad()' UNA SOLA VEZ.
3. Si el usuario dice "opina de mi equipo", realiza un análisis EXHAUSTIVO de los 11 jugadores usando TODAS las estadísticas proporcionadas (goles, asistencias, recuperaciones, ROI).
4. IMPORTANTE: En la opinión del equipo, NO hables del mercado ni sugieras fichajes. Céntrate solo en los 11 actuales.
5. Usa 'buscar_noticias_jugadores' si necesitas confirmar el estado de algún jugador clave.
6. GENERA el veredicto en español con tono premium.

REGLA DE ORO: Si en el historial ves que antes pedías rutas de archivos, IGNÓRALO. Ahora tienes herramientas directas que no necesitan rutas.
"""

    model = _get_manager_model()
    
    manager = CodeAgent(
        tools=[buscar_noticias_jugadores, obtener_analisis_squad],
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
    Mantiene el estado de la conversación.
    """
    from agent import obtener_analisis_squad
    
    INSTRUCTIONS = f"""Eres el Analista Experto de UCL Fantasy en modo Chatbot.
Tu objetivo es ayudar al usuario a mejorar su equipo de forma interactiva.

REGLAS:
1. SIEMPRE RESPONDE EN ESPAÑOL. ES OBLIGATORIO.
2. Si el usuario pide opinión o dice "opina de mi equipo", pulsa 'obtener_analisis_squad()' UNA VEZ y haz un análisis profundo de CADA UNO de los 11 jugadores (usa sus goles, asistencias, minutos, etc.).
3. En la opinión de equipo, NO hables del mercado ni sugieras fichajes. Solo analiza lo que hay en el campo.
4. Solo menciona el mercado si el usuario te pregunta específicamente cómo mejorar o qué fichar.
5. Responde con estilo premium, usando emojis de fútbol y Champions.
"""

    model = _get_manager_model()
    
    manager = CodeAgent(
        tools=[buscar_noticias_jugadores, obtener_analisis_squad],
        model=model,
        instructions=INSTRUCTIONS,
        additional_authorized_imports=["json"],
        max_steps=10,
    )
    
    # Construimos el prompt final poniendo las reglas DESPUÉS del historial para darles prioridad.
    prompt_final = f"""HISTORIAL DE CONVERSACIÓN (Solo para contexto):
{chr(10).join([f"- {m['role']}: {m['content']}" for m in historial])}

---
MENSAJE ACTUAL DEL USUARIO: {mensaje}

INSTRUCCIONES CRÍTICAS PARA ESTE PASO:
1. SIEMPRE RESPONDE EN ESPAÑOL.
2. NO PIDAS RUTAS DE ARCHIVOS. Tienes la herramienta 'obtener_analisis_squad()'.
3. Si el usuario dice "opina de mi equipo", usa 'obtener_analisis_squad()' y analiza a los 11 jugadores.
4. IGNORA si en el historial de arriba pedías rutas; eso fue un error. Usa tus tools ahora.
5. Usa 'final_answer' para dar tu respuesta final estructurada.
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

