# main.py
import os
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel, DuckDuckGoSearchTool

# 1. IMPORTAR TUS HERRAMIENTAS
from tools import ver_estado, operar_crypto

load_dotenv()

# 2. Configurar Modelo
model = LiteLLMModel(
    model_id="gemini/gemini-2.5-flash", 
    api_key=os.getenv("GEMINI_API_KEY")
)

# 3. Crear Agente con la lista de herramientas importadas
agent = CodeAgent(
    tools=[DuckDuckGoSearchTool(), ver_estado, operar_crypto], # <--- Aquí las añades
    model=model,
    add_base_tools=True
)

# 4. Loop de interacción
print("---Agente Criptobro---")
print("Ejemplo: 'Compra 0.05 BTC al precio actual si tengo dinero'")

while True:
    user_input = input("\nUsuario: ")
    if user_input.lower() in ['salir', 'exit']:
        break
    
    try:
        agent.run(user_input)
    except Exception as e:
        print(f"Ocurrió un error: {e}")