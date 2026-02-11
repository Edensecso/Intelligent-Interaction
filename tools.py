#import re
#from ddgs import DDGS
#
#query = "Vinicius last player match rating Sofascore"
#
#with DDGS() as ddgs:
#    results = ddgs.text(query, max_results=3)
#
#    text_blob = "\n".join(r.get("body", "") for r in results)
#
#match = re.search(r"received\s+([0-9]+\.[0-9])\s+Sofascore rating", text_blob)
#if match:
#    rating = float(match.group(1))
#    print("Rating detectado:", rating)
#else:
#    print("No se pudo extraer rating.")

# tools.py
import json
import os
from smolagents import tool

# --- HERRAMIENTA 1: LEER ---
@tool
def ver_estado() -> str:
    """
    Lee el archivo JSON local y devuelve el saldo en euros y las criptomonedas actuales.
    Úsala cuando necesites saber cuánto dinero tiene el usuario.
    """
    try:
        with open('cartera.json', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: No se encontró el archivo cartera.json"

# --- HERRAMIENTA 2: ACTUAR (COMPRAR/VENDER) ---
@tool
def operar_crypto(accion: str, cantidad: float, precio_actual: float) -> str:
    """
    Realiza una compra o venta de Bitcoin actualizando la cartera.
    
    Args:
        accion: 'comprar' o 'vender'.
        cantidad: La cantidad de BITCOIN a operar (ej: 0.1).
        precio_actual: El precio de 1 Bitcoin en Euros en ese momento.
    """
    archivo = 'cartera.json'
    try:
        with open(archivo, 'r') as f:
            data = json.load(f)
            
        coste = cantidad * precio_actual
        
        if accion == 'comprar':
            if data['saldo_eur'] >= coste:
                data['saldo_eur'] -= coste
                data['criptomonedas']['BTC'] += cantidad
                msg = f"✅ Comprado {cantidad} BTC por {coste:.2f}€. Saldo restante: {data['saldo_eur']:.2f}€"
            else:
                return f"❌ Fondos insuficientes. Tienes {data['saldo_eur']}€ y necesitas {coste:.2f}€"
                
        elif accion == 'vender':
            # Asumimos que BTC existe en el JSON
            btc_actual = data['criptomonedas'].get('BTC', 0)
            if btc_actual >= cantidad:
                data['criptomonedas']['BTC'] -= cantidad
                data['saldo_eur'] += coste
                msg = f"✅ Vendido {cantidad} BTC por {coste:.2f}€. Nuevo saldo: {data['saldo_eur']:.2f}€"
            else:
                return f"❌ No tienes suficientes BTC. Tienes {btc_actual}"
        
        # Guardar cambios
        with open(archivo, 'w') as f:
            json.dump(data, f, indent=2)
            
        return msg
        
    except Exception as e:
        return f"Error crítico al operar: {str(e)}"