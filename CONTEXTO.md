# Contexto del Proyecto: PSIQUIS-X

PSIQUIS-X es un motor de IA autónomo diseñado para el sector financiero, enfocado en la extracción, validación y auditoría de datos no estructurados con cero tolerancia a las alucinaciones.

## Arquitectura y Flujo de Trabajo (Pipeline)

Para modificar el repo o generar documentación, tu IA debe comprender estos 5 pilares:

1. **Deducción Inteligente de Objetivos (Orquestación):**
El sistema no procesa archivos a ciegas. Analiza el objetivo (ej. extraer métricas de 3 años) y determina si un solo archivo (como el reporte anual más reciente) ya contiene la información histórica, eliminando redundancias y ahorrando tokens.

2. **Fragmentación Dinámica (Slicing):**
Los documentos se dividen en bloques de 15,000 tokens. Para mantener el contexto y evitar el efecto de "pérdida en el medio", se inyecta una "huella digital" (metadatos de página y archivo) en cada bloque.

3. **Arquitectura de "Sala de Tribunal" (Adversarial Multi-Agent):**
- **Agente Escéptico:** Ataca los datos extraídos buscando fallos.
- **Agente Juez:** Evalúa la salida bajo reglas deterministas y matemáticas estrictas.
- **Validación:** Si una métrica no se puede verificar matemáticamente, es rechazada.

4. **Generación de Salidas Estructuradas (FinOps Ready):**
No solo entrega texto; genera dashboards de Excel nativos con cálculos de varianza año tras año ($YoY$), apalancamiento operativo y gráficos financieros automáticos.

5. **Trazabilidad Total (Data Lineage):**
Cada dato en el output final tiene un mapeo directo: Archivo de origen > Página específica > Fragmento de texto literal.

---

## Metadatos del Benchmark (Demo)
- **Caso de Uso:** Extracción de métricas GAAP de reportes financieros de NVIDIA (FY24-FY26).
- **Tiempo de Ejecución:** 290 segundos.
- **Costo de API:** $0.035 USD.
- **Puntaje de Confianza (Audit Confidence):** 98/100.
- **Capacidades Clave:**
  - Cálculo de ingresos totales, margen bruto, gastos operativos e ingresos netos.
  - Identificación de señales de riesgo y perspectivas estratégicas.
