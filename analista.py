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

PLAN DE ACCIÓN OBLIGATORIO (ejecuta en orden):
1. **Analizar Plantilla**: Usa 'evaluar_plantilla_actual' para entender mi equipo.
2. **Analizar Mercado**: Usa 'evaluar_mercado_fichajes' para ver oportunidades.
3. **Recomendar**: Usa 'obtener_recomendaciones_cambio' para cruzar datos y sugerir fichajes.
4. **Verificar**: Usa 'buscar_noticias_jugador' SOLO si necesitas confirmar lesiones/bajas de los sugeridos.
5. **Respuesta Final**: Resume tus hallazgos recomendaciones finales claras.

REGLAS DE ORO:
- SIEMPRE RESPONDE EN ESPAÑOL.
- No inventes jugadores ni precios; usa los datos de las herramientas.
- Respeta el presupuesto disponible: {presupuesto}M.
"""

    model = _get_manager_model()
    
    # Asegúrate de importar las herramientas correctamente
    try:
        from agent import evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio, buscar_noticias_jugador
        tools_list = [evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio, buscar_noticias_jugador]
    except ImportError as e:
        return f"Error crítico de importación de herramientas: {str(e)}. Verifica agent.py."

    manager = CodeAgent(
        tools=tools_list,
        model=model,
        additional_authorized_imports=["json", "datetime"], # Permite imports comunes en el código generado
        max_steps=12, # Un poco más de margen
    )
    
    print(f"\n[Analista] Iniciando orquestador modular con presupuesto {presupuesto}...")
    
    # Prompt más explícito
    prompt = (
        f"Tengo un presupuesto de {presupuesto} millones. "
        "Realiza un análisis completo paso a paso según tu plan: "
        "primero evalúa mi plantilla, luego mira el mercado, "
        "generame recomendaciones de cambios y verifica el estado de los jugadores clave."
    )
    
    try:
        resultado = manager.run(prompt)
        return str(resultado)
    except Exception as e:
        return f"Error durante la ejecución del agente: {str(e)}"

def chatear(mensaje: str, historial: list, presupuesto: float, original_msg: str = "") -> tuple[str, list]:
    """Versión interactiva del analista para modo Chatbot.
    Pre-fetches structured data in Python, then asks the LLM only to search news + write analysis.
    """
    import re as _re
    from agent import evaluar_plantilla_actual, obtener_recomendaciones_cambio, buscar_noticias_jugador

    @tool
    def estado_forma_jugador_actual(nombre: str) -> str:
        """Busca noticias recientes sobre el estado de forma, lesiones o rendimiento de un jugador.
        Args:
            nombre: Nombre del jugador (ej: 'Mbappe', 'Grimaldo').
        """
        return buscar_noticias_jugador(nombre)

    msg_display = (original_msg or mensaje or "").strip()

    def _norm(txt):
        return unicodedata.normalize("NFD", txt or "").lower()

    msg_lower = _norm(msg_display)
    print(f"[Analista-Chat] Pregunta: {msg_display}")

    wants_plantilla = any(k in msg_lower for k in ["anali", "evalua", "plantilla", "equipo", "mi once"])
    wants_cambios   = any(k in msg_lower for k in ["fich", "comprar", "vend", "cambio", "recomenda", "suger", "mercado", "maximo"])

    pos = ""
    if "delan" in msg_lower: pos = "DEL"
    elif "medi" in msg_lower or "centr" in msg_lower: pos = "CEN"
    elif "defen" in msg_lower: pos = "DEF"
    elif "porte" in msg_lower: pos = "POR"

    # ------------------------------------------------------------------
    # PRE-FETCH: recoger datos estructurados ANTES de llamar al LLM
    # ------------------------------------------------------------------
    datos_context = ""
    jugadores_a_buscar = []  # nombres para que el agente busque noticias

    if wants_plantilla or wants_cambios:
        try:
            plantilla_txt = evaluar_plantilla_actual()
            datos_context += f"=== DATOS DE LA PLANTILLA ===\n{plantilla_txt}\n\n"
            # Estrella del equipo
            m = _re.search(r'Maximo Goleador: ([^\(\n]+)', plantilla_txt)
            if m:
                jugadores_a_buscar.append(m.group(1).strip())
        except Exception as e:
            datos_context += f"[Error al cargar plantilla: {e}]\n\n"

    if wants_cambios:
        try:
            cambios_txt = obtener_recomendaciones_cambio(pos)
            datos_context += f"=== CAMBIOS RECOMENDADOS ===\n{cambios_txt}\n\n"
            # Añadir jugadores de las operaciones a la lista de búsqueda
            for nombre in _re.findall(r'VENDER: ([^\(\n]+)', cambios_txt):
                jugadores_a_buscar.append(nombre.strip())
            for nombre in _re.findall(r'FICHAR: ([^\(\n]+)', cambios_txt):
                jugadores_a_buscar.append(nombre.strip())
        except Exception as e:
            datos_context += f"[Error al cargar cambios: {e}]\n\n"

    # Eliminar duplicados manteniendo orden
    seen = set()
    jugadores_unicos = [j for j in jugadores_a_buscar if not (j in seen or seen.add(j))]

    # Construir lista de búsquedas a realizar (el agente las ejecutará)
    busquedas_hint = ""
    if jugadores_unicos:
        calls = "\n".join(
            f'print(estado_forma_jugador_actual("{j}")[:600])' for j in jugadores_unicos
        )
        busquedas_hint = (
            f"JUGADORES A INVESTIGAR (busca noticias de cada uno):\n"
            f"```python\n{calls}\n```\n\n"
        )

    # ------------------------------------------------------------------
    # Instrucciones del agente: solo buscar noticias + redactar análisis
    # ------------------------------------------------------------------
    INSTRUCTIONS = """Eres un Director Técnico experto en Fantasy Football UCL.
Se te proporcionan datos estructurados del equipo. Tu ÚNICA misión es:
1. Buscar noticias de los jugadores indicados con estado_forma_jugador_actual().
2. Redactar un análisis estratégico en español fluido con final_answer().

REGLAS:
- NUNCA copies tablas de datos en bruto. Interprétalas en texto fluido.
- NUNCA inventes datos. Usa solo los datos proporcionados y las búsquedas.
- SIEMPRE usa triple-quote para el texto y asígnalo a una variable antes de llamar final_answer.

EL ÚNICO FORMATO VÁLIDO ES ESTE (con variable y triple-quote):
```python
texto = \"\"\"Tu análisis aquí,
puede ocupar varias líneas,
sin problema.\"\"\"
final_answer(texto)
```

NUNCA escribas final_answer(...) directamente con el texto dentro sin usar una variable.
"""

    model = _get_manager_model()
    manager = CodeAgent(
        tools=[estado_forma_jugador_actual],
        model=model,
        instructions=INSTRUCTIONS,
        additional_authorized_imports=["re"],
        max_steps=10,
    )

    prompt = (
        f"PREGUNTA: '{msg_display}'\n"
        f"PRESUPUESTO: {presupuesto}M\n\n"
        f"{datos_context}"
        f"{busquedas_hint}"
        "TAREA: Busca las noticias de los jugadores indicados y redacta un análisis "
        "estratégico completo en español que incluya:\n"
        "- Estado de cada línea del equipo\n"
        "- Qué vender y por qué (nombre, precio, ROI)\n"
        "- Qué fichar y por qué (nombre, precio, mejora ROI)\n"
        "- Cálculo presupuestario (ventas + saldo = presupuesto total disponible)\n"
        "- Estado de forma de cada jugador involucrado\n"
        "- Priorización de los cambios\n\n"
        "Llama a final_answer() con el análisis redactado."
    )

    try:
        respuesta_agente = manager.run(prompt)
        respuesta_texto = str(respuesta_agente)
    except Exception as e:
        respuesta_texto = f"Ocurrió un error al procesar tu solicitud: {str(e)}"
        print(f"[Analista-Chat] Error: {e}")

    historial.append({"role": "user", "content": msg_display})
    historial.append({"role": "assistant", "content": respuesta_texto})
    return respuesta_texto, historial

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

