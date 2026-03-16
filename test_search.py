import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from buscador import buscar
    print("Probando búsqueda de 'Victor Osimhen'...")
    resultado = buscar("Victor Osimhen champions league news")
    print("\nRESULTADO DE BÚSQUEDA:")
    print(resultado[:1000])
except Exception as e:
    print(f"ERROR EN BÚSQUEDA: {e}")
