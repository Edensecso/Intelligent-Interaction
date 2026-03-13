"""
Agente Analista — Cerebro del sistema Fantasy UCL.

Coordina el pipeline completo:
  1. Ejecutor (agent.py) → genera equipo/mercado, analiza y guarda .txt
  2. Buscador (buscador.py) → busca info web de jugadores clave
  3. LLM (qwen3:14b) → genera recomendación final de fichajes/ventas

El analista es un orquestador Python, no un CodeAgent, para evitar
problemas de formato con modelos locales.
"""

import os
import json
from dotenv import load_dotenv
from smolagents import LiteLLMModel

load_dotenv()


# ---------------------------------------------------------------------------
# Modelo de lenguaje natural (qwen3:14b para síntesis final)
# ---------------------------------------------------------------------------

def _get_nl_model() -> LiteLLMModel:
    if os.getenv("GROQ_API_KEY"):
        return LiteLLMModel(model_id="groq/llama-3.1-8b-instant")
    if os.getenv("GOOGLE_API_KEY"):
        return LiteLLMModel(model_id="gemini/gemini-1.5-flash")
    return LiteLLMModel(
        model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen3:14b')}",
        api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


# ---------------------------------------------------------------------------
# Helpers para extraer jugadores del resumen compacto
# ---------------------------------------------------------------------------

def _extraer_peores_equipo(datos: str, n: int = 2) -> list[str]:
    """Devuelve los n jugadores del equipo con menos puntos totales."""
    jugadores = []
    en_equipo = False
    for line in datos.splitlines():
        if line.strip() == "EQUIPO:":
            en_equipo = True
            continue
        if line.strip().startswith("MERCADO:"):
            en_equipo = False
        if en_equipo and "|" in line:
            partes = line.split("|")
            try:
                nombre = partes[0].strip().split(None, 1)[1]  # quita posición
                pts = int(partes[1].replace("Pts:", "").strip())
                jugadores.append((nombre, pts))
            except Exception:
                pass
    jugadores.sort(key=lambda x: x[1])
    return [j[0] for j in jugadores[:n]]


def _extraer_mejores_mercado(datos: str, n: int = 2) -> list[str]:
    """Devuelve los n jugadores del mercado con mayor pts/euro."""
    jugadores = []
    en_mercado = False
    for line in datos.splitlines():
        if line.strip().startswith("MERCADO:"):
            en_mercado = True
            continue
        if line.strip().startswith("ANÁLISIS"):
            en_mercado = False
        if en_mercado and "|" in line:
            partes = line.split("|")
            try:
                nombre = partes[0].strip().split(None, 1)[1]
                pte = float(partes[3].replace("Pts/€:", "").strip())
                jugadores.append((nombre, pte))
            except Exception:
                pass
    jugadores.sort(key=lambda x: x[1], reverse=True)
    return [j[0] for j in jugadores[:n]]


# ---------------------------------------------------------------------------
# Función principal del analista
# ---------------------------------------------------------------------------

def analizar(presupuesto: float) -> str:
    """
    Orquesta el pipeline completo y devuelve la recomendación final.

    Args:
        presupuesto: Dinero disponible del usuario en millones (sin contar ventas).
    """
    # ── Paso 1: Ejecutor ────────────────────────────────────────────────────
    print("\n[Analista] Paso 1: Ejecutando pipeline de datos...")
    from agent import crear_agente
    ejecutor = crear_agente()
    datos = ejecutor.run("Prepara los datos del equipo y mercado.")

    # Extraer solo la parte compacta (por si el managed_agent añade prefijos)
    if "EQUIPO:" in datos:
        datos = datos[datos.index("EQUIPO:"):]

    # ── Paso 2: Búsquedas web ───────────────────────────────────────────────
    print("\n[Analista] Paso 2: Buscando información web de jugadores clave...")
    from buscador import buscar

    peores = _extraer_peores_equipo(datos)
    mejores = _extraer_mejores_mercado(datos)

    info_web = []
    for nombre in peores + mejores:
        print(f"  Buscando: {nombre}...")
        info = buscar(f"{nombre} forma actual Champions League 2025")
        info_web.append(f"[{nombre}]\n{info}")

    info_web_str = "\n\n".join(info_web) if info_web else "Sin información web disponible."

    # ── Paso 3: Recomendación final vía LLM ─────────────────────────────────
    print("\n[Analista] Paso 3: Generando recomendación final...")
    model = _get_nl_model()

    prompt = (
        "Eres el analista jefe de UCL Fantasy Champions League. Responde en español.\n\n"
        f"PRESUPUESTO DISPONIBLE: {presupuesto}M (sin contar ingresos por ventas)\n\n"
        f"DATOS DEL EQUIPO Y MERCADO:\n{datos}\n\n"
        f"INFORMACIÓN WEB ACTUALIZADA:\n{info_web_str}\n\n"
        "Con toda esta información, genera una recomendación de fichajes clara y concisa. "
        "Incluye exactamente estas secciones:\n"
        "🔴 VENTAS recomendadas: jugador, precio de venta, motivo\n"
        "🟢 FICHAJES recomendados: jugador, precio, motivo (con dato web si disponible)\n"
        "💰 BALANCE: ventas totales - fichajes totales = gasto neto vs presupuesto disponible\n"
        "📋 RESUMEN: una frase con el objetivo de la operación\n\n"
        "IMPORTANTE: no superes el presupuesto total (disponible + ingresos por ventas)."
    )

    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}],
        }
    ]
    respuesta = model(messages)
    return respuesta.content


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

    print("\nAnalizando plantilla y mercado...\n")
    resultado = analizar(presupuesto)
    print(f"\n{'='*50}\nRECOMENDACIÓN DEL ANALISTA\n{'='*50}\n{resultado}")
