"""
Agente Fantasy UCL — Punto de entrada principal.

Lanza el Coordinador multi-agente que gestiona:
  - Agente Generador  (agente_generador.py)
  - Agente Analista   (procesador_simple.py)
  - Agente Exportador (agente_exportador.py)

El coordinador recibe el mensaje del usuario en lenguaje natural
y decide a qué sub-agente delegar sin necesidad de router de palabras clave.
"""

from dotenv import load_dotenv
from coordinador import crear_coordinador

load_dotenv()


if __name__ == "__main__":
    coordinador = crear_coordinador()

    print("=== Agente Fantasy UCL ===")
    print("Sub-agentes activos: generador · analista · exportador")
    print("Ejemplos: 'genera un equipo', 'analiza el equipo', 'guarda el resultado'")
    print("(escribe 'salir' para terminar)\n")

    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() in ("salir", "exit", "q"):
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue
        respuesta = coordinador.run(pregunta)
        print(f"\nAgente: {respuesta}\n")
