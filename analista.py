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
    Usa razonamiento + planificación + ejecución con selección de herramientas.
    """
    # Importamos las herramientas REALES de agent.py (sin inventar nombres)
    from agent import evaluar_plantilla_actual, evaluar_mercado_fichajes, obtener_recomendaciones_cambio, buscar_noticias_jugador

    # Wrapper para buscar noticias con nombre descriptivo
    @tool
    def estado_forma_jugador_actual(nombre: str) -> str:
        """Consulta noticias recientes y resume el estado de forma actual de un jugador.
         Args:
            nombre: Nombre del jugador (ej: 'Mbappe').
        """
        return buscar_noticias_jugador(nombre)

    INSTRUCTIONS = """Eres un Agente de IA experto en Fantasy Football UCL (Champions League).
Tu objetivo es ayudar al usuario a gestionar su equipo y mercado.

ESTRATEGIA OBLIGATORIA:
1. Cuando el usuario pida algo, EJECUTA la herramienta correspondiente mediante código Python.
2. La herramienta devolverá texto con la información.
3. DEBES terminar la conversación llamando a `final_answer(texto_resultado)`.

HERRAMIENTAS:
- `evaluar_plantilla_actual()`: Para "analizar equipo/plantilla".
- `evaluar_mercado_fichajes()`: Para "ver mercado".
- `obtener_recomendaciones_cambio(posicion_objetivo=None)`: Para "fichajes", "recomendaciones" o "cambios".
- `estado_forma_jugador_actual(nombre="...")`: Para preguntas sobre un jugador.

EJEMPLOS DE CÓDIGO A GENERAR:

Caso 1: "Analiza mi equipo"
```python
resultado = evaluar_plantilla_actual()
final_answer(resultado) # ¡IMPORTANTE USAR final_answer!
```

Caso 2: "Recomienda delanteros"
```python
resultado = obtener_recomendaciones_cambio(posicion_objetivo="DEL")
final_answer(resultado)
```

REGLA CLAVE:
Si no llamas a `final_answer()`, la respuesta NO le llegará al usuario. ¡ÚSALO SIEMPRE AL FINAL!
"""

    model = _get_manager_model()
    
    # Lista de herramientas con los nombres correctos
    tools = [
        evaluar_plantilla_actual,
        evaluar_mercado_fichajes,
        obtener_recomendaciones_cambio,
        estado_forma_jugador_actual,
    ]

    manager = CodeAgent(
        tools=tools,
        model=model,
        instructions=INSTRUCTIONS,
        additional_authorized_imports=["json", "datetime"],
        max_steps=5, # Reduzco steps para evitar bucles tontos
    )

    msg_display = (original_msg or mensaje or "").strip()
    
    # Normalizar para búsquedas
    def _norm_light(txt: str) -> str:
        return unicodedata.normalize("NFD", txt or "").lower()

    msg_lower = _norm_light(msg_display)
    
    print(f"[Analista-Chat] Pregunta: {msg_display}")

    # --- ENRUTADOR HEURÍSTICO (Ayuda para modelos pequeños) ---
    # Detectamos la intención para guiar al modelo y evitar que se quede bloqueado.
    
    hint_instruction = ""
    # Detectar análisis de plantilla primero para evitar solape
    if any(k in msg_lower for k in ["anali", "evalua", "plantilla", "equipo", "mi once"]):
        hint_instruction = (
            "PISTA: El usuario quiere un análisis de su equipo. \n"
            "1. Ejecuta: `analisis = evaluar_plantilla_actual()`\n"
            "2. IMPORTANTE: Finaliza llamando a `final_answer(analisis)`."
        )

    # Caso 1: Fichajes / Ventas / Mercado (Tiene prioridad si la frase es mixta "analiza y ficha")
    if any(k in msg_lower for k in ["fich", "comprar", "vend", "cambio", "recomenda", "suger", "mercado"]):
        pos = ""
        if "delan" in msg_lower: pos = "DEL"
        elif "medi" in msg_lower or "centr" in msg_lower: pos = "CEN"
        elif "defen" in msg_lower: pos = "DEF"
        elif "porte" in msg_lower: pos = "POR"
        
        pos_arg = f'posicion_objetivo="{pos}"' if pos else ""
        hint_instruction = (
            f"PISTA: El usuario quiere hacer cambios o fichajes. \n"
            f"DEBES ejecutar: `resultado = obtener_recomendaciones_cambio({pos_arg})`\n"
            f"Y luego finalizar con: `final_answer(resultado)`"
        )

    # Caso 2: Jugador Específico (Estado / Lesión)
    if any(k in msg_lower for k in ["estado", "forma", "lesion", "noticia", "como esta"]):
        # Intentar extraer nombre simple (muy básico)
        hint_instruction = (
            "PISTA: El usuario pregunta por el estado de un jugador. \n"
            "Identifica el nombre del jugador en la pregunta y ejecuta: `resultado = estado_forma_jugador_actual(nombre='NombreJugador')`\n"
            "Y luego finalizar con: `final_answer(resultado)`"
        )


    # Prompt user message reforzado
    prompt = (
        f"PREGUNTA DEL USUARIO: '{msg_display}'\n"
        f"PRESUPUESTO: {presupuesto}M\n\n"
        f"{hint_instruction}\n\n"
        "TU ACCIÓN: Escribe el código Python necesario para ejecutar la herramienta correcta "
        "y devuelve el resultado con `final_answer(...)`."
    )

    try:
        # Ejecutamos el agente
        respuesta_agente = manager.run(prompt)
        # Convertimos a string por seguridad
        respuesta_texto = str(respuesta_agente)
    except Exception as e:
        respuesta_texto = f"Ocurrió un error al procesar tu solicitud: {str(e)}"
        print(f"[Analista-Chat] Error: {e}")

    # Guardar en historial
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

