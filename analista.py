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
import json
import time
import unicodedata
from datetime import datetime
from dotenv import load_dotenv
from smolagents import LiteLLMModel, CodeAgent, ToolCallingAgent, tool

STATS_FILE = os.path.join(os.path.dirname(__file__), "chat_stats.json")


def _guardar_stat(stat: dict):
    """Añade una entrada de métricas al archivo chat_stats.json."""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"consultas": []}
        data["consultas"].append(stat)
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Stats] Error guardando métricas: {e}")


def _extraer_tokens(agent) -> tuple[int, int]:
    """Extrae tokens totales de entrada y salida de agent.memory.steps."""
    tok_in = tok_out = 0
    try:
        steps = agent.memory.steps
    except AttributeError:
        return 0, 0
    for step in steps:
        usage = getattr(step, "token_usage", None)
        if usage:
            tok_in  += getattr(usage, "input_tokens",  0)
            tok_out += getattr(usage, "output_tokens", 0)
    return tok_in, tok_out


def _num_pasos(agent) -> int:
    """Número de steps ejecutados por el agente."""
    try:
        return len(agent.memory.steps)
    except AttributeError:
        return 0

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

    manager = ToolCallingAgent(
        tools=tools_list,
        model=model,
        max_steps=12,
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
            "TAREA: Realiza un INFORME ESTRATÉGICO INTEGRAL en español:\n"
            "1. ANÁLISIS POR LÍNEAS: Evalúa POR, DEF, CEN y DEL basándote en los puntos medios y ROI.\n"
            "2. DESGLOSE DE LA PLANTILLA: Menciona brevemente a los 11 jugadores y su rendimiento actual.\n"
            "3. RECOMENDACIONES TÉCNICAS: Detalla qué vender y qué fichar (usa los pares pre-calculados).\n"
            "4. ESTADO DE FORMA: Resume las noticias de los jugadores clave.\n"
            "5. CIERRE: Balance final de presupuesto y potencial de puntos."
        )
    elif wants_mercado and not wants_cambios:
         tarea = (
            "TAREA: Redacta una OPINIÓN PROFESIONAL sobre el MERCADO actual en español.\n"
            "- Identifica chollos (ROI alto) y jugadores de élite.\n"
            "- Justifica por qué son buenas inversiones.\n"
            "- No hables de mi plantilla a menos que sea para comparar valor."
        )
    elif wants_pairs:
        tipo = "UN SOLO FICHAJE" if wants_single else "QUIÉN POR QUIÉN"
        tarea = (
            f"TAREA: Selecciona el mejor movimiento de '{tipo}' en español.\n"
            "- Usa los pares VENDER -> FICHAR pre-calculados.\n"
            "- Justifica financieramente (ahorro vs coste) y por ROI.\n"
            "- Llama a estado_forma_jugador_actual() para confirmar disponibilidad."
        )
    elif wants_forma or "informacion" in msg_lower or "noticia" in msg_lower:
        tarea = (
            "TAREA: Busca noticias del jugador o jugadores indicados y responde con un resumen de su estado de forma en español.\n"
            "- Usa OBLIGATORIAMENTE estado_forma_jugador_actual() para cada jugador mencionado.\n"
            "- No respondas 'No tengo información' sin antes haber usado la herramienta."
        )
    elif wants_plantilla:
        tarea = (
            "TAREA: Genera un INFORME COMPLETO DE LA PLANTILLA en español:\n"
            "1. RESUMEN GLOBAL: Cómo rinde el equipo en general.\n"
            "2. ANÁLISIS DE LÍNEAS (POR, DEF, CEN, DEL): Comenta el nivel de cada zona.\n"
            "3. RENDIMIENTO INDIVIDUAL: Menciona a los 11 jugadores, destacando los mejores ROI y los 'puntos muertos' (ROI 0).\n"
            "4. ACTUALIDAD: Estado de los jugadores estrella según noticias."
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
    INSTRUCTIONS = """Eres un experto analista técnico de Fantasy Football UCL.
Tu estilo es profesional, directo y basado en datos.

REGLAS DE ORO:
1. INFORME COMPLETO: Cuando el usuario pide un análisis de equipo, DEBES comentar las 4 líneas (POR, DEF, CEN, DEL) y mencionar a los jugadores clave. NO te limites a una sola estrella.
2. DATOS REALES: Usa los 'DATOS DE LA PLANTILLA' proporcionados en el contexto. No inventes puntos ni precios.
3. ANTI-ALUCINACIÓN: Si un jugador no está en los datos ni en la búsqueda, dilo. No inventes que está 'en buena forma' si no tienes la noticia.
4. HERRAMIENTAS: Para noticias de actualidad, llama a estado_forma_jugador_actual().

MÁNDATORY: Si el usuario pide un 'informe completo', estructura tu respuesta con encabezados y analiza a los 11 jugadores.
"""

    model = _get_manager_model()
    manager = ToolCallingAgent(
        tools=[estado_forma_jugador_actual],
        model=model,
        instructions=INSTRUCTIONS,
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

    exito = 0
    error_parsing = 0
    t0 = time.time()

    try:
        respuesta_agente = manager.run(prompt)
        respuesta_texto = str(respuesta_agente)
        exito = 1 if len(respuesta_texto) > 30 else 0
    except Exception as e:
        error_str = str(e)
        print(f"[Analista-Chat] Error: {e}")
        snippet = _re.search(
            r'Here is your code snippet:\s*(.*?)(?:Make sure to include|$)',
            error_str, _re.DOTALL
        )
        if snippet and len(snippet.group(1).strip()) > 50:
            respuesta_texto = snippet.group(1).strip()
            print("[Analista-Chat] Texto rescatado del error de parsing.")
            exito = 1
            error_parsing = 1
        elif "AgentMaxStepsError" in error_str or "max_steps" in error_str.lower():
            respuesta_texto = (
                "El análisis tardó demasiado. Intenta con una pregunta más concreta, "
                "por ejemplo: '¿Qué cambios hacer en el centrocampo?' o '¿Cómo está Mbappé?'"
            )
        else:
            respuesta_texto = f"Ocurrió un error al procesar tu solicitud: {error_str}"

    tiempo_s = round(time.time() - t0, 2)
    tok_in, tok_out = _extraer_tokens(manager)

    _guardar_stat({
        "timestamp":      datetime.now().isoformat(),
        "modelo":         model.model_id,
        "mensaje":        msg_display[:120],
        "tipo":           ("plantilla+cambios" if (wants_plantilla and wants_cambios)
                           else "plantilla" if wants_plantilla
                           else "cambios"   if wants_cambios
                           else "forma"),
        "exito":          exito,
        "pasos":          _num_pasos(manager),
        "tiempo_s":       tiempo_s,
        "tokens_entrada": tok_in,
        "tokens_salida":  tok_out,
        "tokens_por_seg": round(tok_out / tiempo_s, 2) if tiempo_s > 0 else 0,
        "longitud_resp":  len(respuesta_texto),
        "error_parsing":  error_parsing,
    })

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

