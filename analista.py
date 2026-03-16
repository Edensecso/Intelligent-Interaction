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
    # Ollama: desactivar thinking mode para que el output sea limpio y parseable
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:7b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        extra_body={"think": False},
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
    from agent import analizar_mercado, obtener_recomendaciones_cambio

    mercado = analizar_mercado()
    recomendaciones = obtener_recomendaciones_cambio(posicion_objetivo)
    return f"{recomendaciones}\n\n=== MERCADO (ANÁLISIS DETALLADO) ===\n{mercado}"


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
        from agent import evaluar_plantilla_actual, analizar_mercado, obtener_recomendaciones_cambio, buscar_noticias_jugador
        tools_list = [evaluar_plantilla_actual, analizar_mercado, obtener_recomendaciones_cambio, buscar_noticias_jugador]
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
    from agent import evaluar_plantilla_actual, analizar_mercado, obtener_recomendaciones_cambio, buscar_noticias_jugador

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
    wants_mercado   = any(k in msg_lower for k in ["mercado", "opciones", "oportunidades", "ojeador"])
    wants_cambios   = any(k in msg_lower for k in ["fich", "vend", "cambio", "recomenda", "suger", "maximo", "intercambio"])
    # Detectar intención de pares directos (quién por quién) y si quiere solo uno
    wants_pairs     = any(k in msg_lower for k in ["quien por quien", "fichajes por separado", "par de cambios", "un fichaje", "el mejor", "recomiendame"])
    wants_single    = any(k in msg_lower for k in ["solo uno", "un solo", "el mejor", "cual seria", "elige uno", "me recomiendas uno", "recomiendame un", "recomienda un"])
    wants_forma     = any(k in msg_lower for k in ["estado", "forma", "lesion", "noticia", "como esta", "informacion", "info", "quien es", "que tal", "novedad"])

    pos = ""
    if "delan" in msg_lower: pos = "DEL"
    elif "medi" in msg_lower or "centr" in msg_lower: pos = "CEN"
    elif "defen" in msg_lower: pos = "DEF"
    elif "porte" in msg_lower: pos = "POR"

    # ------------------------------------------------------------------
    # PRE-FETCH: recoger datos estructurados ANTES de llamar al LLM
    # ------------------------------------------------------------------
    datos_context = ""
    jugadores_a_buscar = []

    if wants_plantilla or wants_cambios:
        try:
            plantilla_txt = evaluar_plantilla_actual()
            datos_context += f"=== DATOS DE LA PLANTILLA ===\n{plantilla_txt}\n\n"
            m = _re.search(r'Maximo Goleador: ([^\(\n]+)', plantilla_txt)
            if m:
                jugadores_a_buscar.append(m.group(1).strip())
        except Exception as e:
            datos_context += f"[Error al cargar plantilla: {e}]\n\n"

    if wants_mercado:
        try:
            mercado_txt = analizar_mercado()
            datos_context += f"=== OPORTUNIDADES DEL MERCADO ===\n{mercado_txt}\n\n"
            # Extraer nombres de jugadores del mercado para buscar noticias
            # Los nombres suelen estar en formato '1. **Nombre**' o similar
            for nombre in _re.findall(r'\*\*([^*]+)\*\*', mercado_txt):
                if len(nombre.strip()) > 3:
                    jugadores_a_buscar.append(nombre.strip())
        except Exception as e:
            datos_context += f"[Error al cargar mercado: {e}]\n\n"

    if wants_cambios or wants_pairs:
        try:
            # Si el usuario pregunta por "uno solo" o "el mejor", forzar resultado aunque la plantilla sea óptima
            cambios_txt = obtener_recomendaciones_cambio(pos, forzar=wants_single)
            datos_context += f"=== RECOMENDACIONES DE CAMBIO (Quién por Quién) ===\n{cambios_txt}\n\n"
            # Capturar nombres para buscar noticias
            for nombre in _re.findall(r'VENDER: ([^\(\n]+)', cambios_txt):
                jugadores_a_buscar.append(nombre.strip().split('(')[0].strip())
            for nombre in _re.findall(r'FICHAR: ([^\(\n]+)', cambios_txt):
                jugadores_a_buscar.append(nombre.strip().split('(')[0].strip())
        except Exception as e:
            datos_context += f"[Error al cargar cambios: {e}]\n\n"

    # Para preguntas de forma/información: extraer el nombre del jugador del mensaje
    if (wants_forma or True) and not jugadores_a_buscar:
        # Busca nombres complejos (K. Furo, Carlos Forbs, etc)
        nombres_msg = _re.findall(r'\b(?:[A-Z]\.\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b)*', msg_display)
        # También buscar en minúsculas si coinciden con palabras comunes de jugadores
        for word in _re.findall(r'\b[a-z]{4,}\b', msg_lower):
            if any(p in word for p in ["oshim", "osim", "mbap", "haala", "kane", "vini", "bellin", "furo", "forbis", "forbs"]):
                nombres_msg.append(word.capitalize())
        
        jugadores_a_buscar = [n.strip() for n in nombres_msg if len(n) > 3]

    # Eliminar duplicados manteniendo orden
    seen = set()
    jugadores_unicos = []
    for j in jugadores_a_buscar:
        j_clean = j.strip().strip(',').strip('.')
        if j_clean.lower() not in seen:
            jugadores_unicos.append(j_clean)
            seen.add(j_clean.lower())

    # Hint de búsquedas para el agente
    busquedas_hint = ""
    if jugadores_unicos:
        calls = "\n".join(
            f'print(estado_forma_jugador_actual("{j}")[:600])' for j in jugadores_unicos
        )
        busquedas_hint = (
            f"JUGADORES A INVESTIGAR (busca noticias de cada uno):\n"
            f"```python\n{calls}\n```\n\n"
        )

    # TAREA dinámica según tipo de pregunta
    if wants_plantilla and wants_cambios:
        tarea = (
            "TAREA: Busca noticias de los jugadores indicados y redacta un análisis estratégico en español que incluya:\n"
            "- Estado de cada línea (portería, defensa, centrocampo, delantera)\n"
            "- Qué vender y por qué (nombre, precio, ROI)\n"
            "- Qué fichar y por qué (nombre, precio, mejora ROI)\n"
            "- Cálculo: ventas + presupuesto = dinero total disponible vs coste fichajes\n"
            "- Estado de forma de cada jugador involucrado\n"
            "- Priorización de los cambios"
        )
    elif wants_mercado and not wants_cambios:
         tarea = (
            "TAREA: Redacta una OPINIÓN PROFESIONAL sobre el MERCADO actual en español.\n"
            "- Menciona los mejores jugadores disponibles según los datos pre-cargados.\n"
            "- Justifica por qué son buenas opciones (ROI, puntos, precio).\n"
            "- No hables de cambios específicos de mi plantilla a menos que se te pida."
        )
    elif wants_pairs:
        tipo = "UN SOLO FICHAJE" if wants_single else "QUIÉN POR QUIÉN"
        tarea = (
            f"TAREA: Responde a la petición de '{tipo}' en español.\n"
            "- El usuario quiere que elijas el mejor movimiento posible (o uno solo si lo pide).\n"
            "- Usa EXCLUSIVAMENTE los pares VENDER -> FICHAR pre-calculados arriba.\n"
            "- NO INVENTES JUGADORES (No Neymar, No Di Maria, No Pogba).\n"
            "- Si el usuario pide UNO SOLO, elige el que tenga mayor IMPACTO (+ pts/M) o la mejor nota.\n"
            "- DEBES llamar a estado_forma_jugador_actual() para verificar si el jugador a fichar o vender tiene noticias de última hora."
        )
    elif wants_forma or "informacion" in msg_lower or "noticia" in msg_lower:
        tarea = (
            "TAREA: Busca noticias del jugador o jugadores indicados y responde con un resumen de su estado de forma en español.\n"
            "- Usa OBLIGATORIAMENTE estado_forma_jugador_actual() para cada jugador mencionado.\n"
            "- No respondas 'No tengo información' sin antes haber usado la herramienta."
        )
    elif wants_plantilla:
        tarea = (
            "TAREA: Busca noticias del jugador estrella y redacta un análisis del estado del equipo en español:\n"
            "- Qué líneas rinden bien y cuáles necesitan mejora\n"
            "- Estado de forma de los jugadores más destacados\n"
            "- Jugadores con ROI 0 que podrían ser un problema"
        )
    elif wants_cambios:
        tarea = (
            "TAREA: Busca noticias de los jugadores de venta y fichaje, y redacta el análisis de cambios en español:\n"
            "- Por qué vender cada jugador (ROI, rendimiento)\n"
            "- Por qué fichar cada jugador (ROI, precio, mejora)\n"
            "- Cálculo presupuestario y priorización"
        )
    else:
        tarea = "TAREA: Responde directamente la pregunta anterior en español. Busca noticias si es necesario y responde solo lo que se pregunta."

    # ------------------------------------------------------------------
    # Instrucciones del agente: solo buscar noticias + responder
    # ------------------------------------------------------------------
    INSTRUCTIONS = """Eres un asistente experto de Fantasy Football UCL.
Responde EXACTAMENTE lo que te pregunta el usuario, ni más ni menos.
REGLA ANTI-ALUCINACIÓN:
1. SIEMPRE usa estado_forma_jugador_actual() para confirmar datos de jugadores desconocidos.
2. NUNCA inventes posiciones (un defensa no es portero).
3. NUNCA inventes equipos o habilidades extrañas.
4. Si no tienes datos en el contexto ni en el buscador, di simplemente que no tienes esa información.

Al finalizar tu análisis, debes llamar a final_answer() pasando un único argumento que sea tu respuesta redactada COMPLETAMENTE en español.
NO utilices textos de ejemplo como 'Tu respuesta aquí'. Escribe contenido real y útil basado en los datos.
MÁNDATORY: Si el usuario pregunta por un jugador específico (como Osimhen/Oshimen), DEBES llamar a estado_forma_jugador_actual() antes de responder.
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
        f"{tarea}\n\n"
        "Llama a final_answer() con la respuesta redactada."
    )

    try:
        respuesta_agente = manager.run(prompt)
        respuesta_texto = str(respuesta_agente)
    except Exception as e:
        error_str = str(e)
        print(f"[Analista-Chat] Error: {e}")
        # El modelo a veces escribe buen texto pero sin code tags → rescatarlo
        snippet = _re.search(
            r'Here is your code snippet:\s*(.*?)(?:Make sure to include|$)',
            error_str, _re.DOTALL
        )
        if snippet and len(snippet.group(1).strip()) > 50:
            respuesta_texto = snippet.group(1).strip()
            print("[Analista-Chat] Texto rescatado del error de parsing.")
        elif "AgentMaxStepsError" in error_str or "max_steps" in error_str.lower():
            respuesta_texto = (
                "El análisis tardó demasiado. Intenta con una pregunta más concreta, "
                "por ejemplo: '¿Qué cambios hacer en el centrocampo?' o '¿Cómo está Mbappé?'"
            )
        else:
            respuesta_texto = f"Ocurrió un error al procesar tu solicitud: {error_str}"

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

