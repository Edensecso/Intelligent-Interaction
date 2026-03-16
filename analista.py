"""
Agente Analista — Cerebro del sistema Fantasy UCL.

Coordina el pipeline completo como un Manager Agent:
  1. Utiliza el sub-agente (ejecutor) para obtener datos del equipo y mercado.
  2. Decide qué jugadores analizar en profundidad.
  3. Utiliza la herramienta de búsqueda para obtener información web sobre ellos.
  4. Genera una recomendación de fichajes y ventas para cumplir con el presupuesto.
"""

import os
import re
import unicodedata
from datetime import datetime
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
def recomendar_cambios_desde_datos(posicion_objetivo: str = "") -> str:
    """Genera recomendaciones SOLO desde los scripts de datos internos.
    No usa web para no mezclar señales externas en fichajes/ventas.

    Args:
        posicion_objetivo: Opcional (POR, DEF, CEN, DEL).
    """
    from agent import evaluar_mercado_fichajes, obtener_recomendaciones_cambio

    mercado = evaluar_mercado_fichajes()
    recomendaciones = obtener_recomendaciones_cambio(posicion_objetivo)
    return f"{recomendaciones}\n\n=== MERCADO (SCRIPT INTERNO) ===\n{mercado}"


@tool
def estado_forma_jugador_actual(nombre: str) -> str:
    """Consulta noticias recientes y resume el estado de forma actual.

    Args:
        nombre: Nombre del jugador (ej: Mbappé).
    """
    from buscador import buscar

    year = datetime.now().year
    query = f"{nombre} estado de forma lesion actualidad champions league hoy {year}"
    resumen = buscar(query)
    return f"=== ESTADO ACTUAL DE {nombre.upper()} ===\n{resumen}"

# ---------------------------------------------------------------------------
# Manager Agent
# ---------------------------------------------------------------------------

def analizar(presupuesto: float) -> str:
    """
    Instancia el Agent orquestador (Manager) para análisis automático.
    """
    from agent import evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio, buscar_noticias_jugador
    
    INSTRUCTIONS = f"""Eres el Analista Orquestador de UCL Fantasy. Tu misión es dar recomendaciones basadas 100% en DATOS.

REGLAS DE ORO:
1. SIEMPRE RESPONDE EN ESPAÑOL.
2. Usa las herramientas modulares (evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio) según lo que necesites informar.
3. Usa 'buscar_noticias_jugador' para corroborar el estado real de los jugadores.
"""

    model = _get_manager_model()
    
    from smolagents import ToolCallingAgent

    manager = ToolCallingAgent(
        tools=[evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio, buscar_noticias_jugador],
        model=model,
        instructions=INSTRUCTIONS,
        max_steps=10,
    )
    
    print(f"\n[Analista] Iniciando orquestador modular...")
    resultado = manager.run("Realiza un análisis completo: evalúa mi plantilla, mira el mercado y dame recomendaciones finales.")
    return resultado

def chatear(mensaje: str, historial: list, presupuesto: float, original_msg: str = "") -> tuple[str, list]:
    """Versión interactiva del analista para modo Chatbot.
    Usa razonamiento + planificación + ejecución con selección de herramientas.
    """
    from agent import evaluar_plantilla_actual, evaluar_mercado_fichajes
    from smolagents import ToolCallingAgent

    INSTRUCTIONS = """Eres un analista de UCL Fantasy. Trabajas como agente (no chatbot simple):
1) Razonas la intención.
2) Planificas qué herramienta usar.
3) Ejecutas herramientas y respondes SOLO con datos obtenidos.

Herramientas disponibles:
- evaluar_plantilla_actual()
- evaluar_mercado_fichajes()
- recomendar_cambios_desde_datos(posicion_objetivo)
- estado_forma_jugador_actual(nombre)

Reglas de uso obligatorias:
- Si piden evaluar equipo/plantilla: usa evaluar_plantilla_actual().
- Si piden oportunidades de mercado: usa evaluar_mercado_fichajes().
- Si piden fichajes/ventas/cambios: usa SIEMPRE recomendar_cambios_desde_datos(...). No uses web en ese caso.
- Si la consulta menciona "delantero", usa posicion_objetivo="DEL". Si menciona defensa/centro/portero, usa DEF/CEN/POR.
- Si preguntan por un jugador concreto (estado actual, lesiones, forma, si venderlo): DEBES usar estado_forma_jugador_actual(nombre).
- Si piden fichajes y mencionan una posición concreta (por ejemplo, delantero), respeta esa posición en la respuesta final y descarta propuestas de otras líneas.
- Si piden “analiza mi equipo”, devuelve el texto completo del análisis, no un resumen corto.
- Responde siempre en español, de forma breve y clara.
- No reutilices respuestas anteriores ni inventes datos; apóyate en herramientas.
"""

    model = _get_manager_model()
    manager = ToolCallingAgent(
        tools=[
            evaluar_plantilla_actual,
            evaluar_mercado_fichajes,
            recomendar_cambios_desde_datos,
            estado_forma_jugador_actual,
        ],
        model=model,
        instructions=INSTRUCTIONS,
        max_steps=10,
    )

    msg_display = (original_msg or mensaje or "").strip()
    print(f"[Analista-Chat] Pregunta: {msg_display}")

    def _norm(txt: str) -> str:
        t = unicodedata.normalize("NFD", txt or "")
        t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
        return t.lower()

    qn = _norm(msg_display)

    # Fuera de dominio: el agente solo responde sobre fantasy UCL.
    q = msg_display.lower()
    dominio_hits = [
        "equipo", "plantilla", "mercado", "fichaj", "vender", "venta", "jugador",
        "champions", "ucl", "mbappe", "osimhen", "grimaldo", "gordon", "vitinha",
        "delantero", "defensa", "centrocamp", "portero", "lesion", "forma"
    ]
    if not any(k in q for k in dominio_hits):
        respuesta = "Solo puedo ayudar con consultas de Fantasy UCL (plantilla, mercado, fichajes, ventas y estado de jugadores)."
        historial.append({"role": "user", "content": msg_display})
        historial.append({"role": "assistant", "content": respuesta})
        return respuesta, historial

    # Forzar salida útil cuando piden análisis de plantilla: texto completo sin resumir.
    if any(k in qn for k in ["analiza mi equipo", "analiza mi plantilla", "evalua mi equipo", "evalua mi plantilla"]):
        resultado = evaluar_plantilla_actual()
        historial.append({"role": "user", "content": msg_display})
        historial.append({"role": "assistant", "content": resultado})
        return resultado, historial

    # Fichajes/ventas: usar scripts internos y no web general.
    if any(k in qn for k in ["fich", "vender", "ventas", "comprar", "cambio"]):
        pos = ""
        if "delanter" in qn:
            pos = "DEL"
        elif "defens" in qn:
            pos = "DEF"
        elif "centro" in qn or "medio" in qn:
            pos = "CEN"
        elif "porter" in qn:
            pos = "POR"
        resultado = recomendar_cambios_desde_datos(pos)
        historial.append({"role": "user", "content": msg_display})
        historial.append({"role": "assistant", "content": resultado})
        return resultado, historial

    # Estado de forma de jugador: búsqueda actualizada.
    if any(k in qn for k in ["estado de forma", "actual", "lesion", "informacion"]) and "mbappe" in qn:
        resultado = estado_forma_jugador_actual("Mbappé")
        historial.append({"role": "user", "content": msg_display})
        historial.append({"role": "assistant", "content": resultado})
        return resultado, historial

    prompt_final = f"""CONTEXTO: {mensaje}
CONSULTA DEL USUARIO: {msg_display}

Ejecuta el circuito completo de agente: razonamiento, planificación y uso de herramientas según corresponda.
"""

    resultado = manager.run(prompt_final)
    resultado = str(resultado)

    historial.append({"role": "user", "content": msg_display})
    historial.append({"role": "assistant", "content": resultado})
    return resultado, historial


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

