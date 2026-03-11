┌─────────────────────────────────────┐
│         MANAGER (Orquestador)       │
│   Recibe petición del usuario y     │
│   delega en los agentes adecuados   │
└──────────┬──────────────────────────┘
           │
     ┌─────┼─────────┬───────────┐
     ▼     ▼         ▼           ▼
┌────────┐┌────────┐┌──────────┐┌──────────┐
│EJECUTOR││ANALISTA││PROCESADOR││ BUSCADOR │
│        ││        ││ SIMPLE   ││   WEB    │
│scrap   ││Decide  ││Texto     ││DuckDuck  │
│shuffle ││compras/││natural   ││Go/APIs   │
│        ││ventas  ││amigable  ││externas  │
└────────┘└────────┘└──────────┘└──────────┘
