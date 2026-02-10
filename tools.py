import re
from ddgs import DDGS

query = "Vinicius last player match rating Sofascore"

with DDGS() as ddgs:
    results = ddgs.text(query, max_results=3)

    text_blob = "\n".join(r.get("body", "") for r in results)

match = re.search(r"received\s+([0-9]+\.[0-9])\s+Sofascore rating", text_blob)
if match:
    rating = float(match.group(1))
    print("Rating detectado:", rating)
else:
    print("No se pudo extraer rating.")