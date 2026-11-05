"""
Versión en español de la Figura 1 (flujo metodológico), para la traducción del TCC.

Reutiliza el dibujo de fig_fluxo_metodologico.py sin modificarlo: solo sustituye
los textos de las etapas y de los grupos y guarda en reports/figuras_v27_es/.
"""

from pathlib import Path

import fig_fluxo_metodologico as base

SALIDA = Path(__file__).parent.parent / "reports" / "figuras_v27_es" / "fig00_flujo_metodologico.png"

base.ETAPAS = [
    ("Extracción", base.AZUL, base._navegador,
     ["Extracción automatizada", "(web scraping)", "3.962 reportes", "17 rutas, 2020 a 2026"]),
    ("Consolidación", base.AZUL, base._banco,
     ["Data Stitching: unión", "de los archivos en un", "panel único", "(Matriz Maestra)"]),
    ("Preprocesamiento", base.VERDE, base._funil,
     ["Desenlace reconstruido", "con los pagos diarios", "(umbral de 120 días)", "Exclusiones y cohorte"]),
    ("Ingeniería\nde atributos", base.VERDE, base._linha_do_tempo,
     ["Bloques de 7 días", "Historial del cliente", "Días de cobranza", "Región y contexto macro"]),
    ("Modelado", base.LARANJA, base._rede,
     ["Riesgos competitivos", "(default y cancelación)", "Fine-Gray y Cox", "RSF y DeepHit"]),
    ("Evaluación", base.LARANJA, base._curva,
     ["Validación por cliente", "AUC y C-index", "Defaults en el top 10%", "de mayor riesgo"]),
]

base.GRUPOS = [(0, 1, "Ingeniería de datos (ETL)", base.AZUL),
               (2, 3, "Preparación de los datos", base.VERDE),
               (4, 5, "Modelado y evaluación", base.LARANJA)]

if __name__ == "__main__":
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    base.desenhar(SALIDA)
    print(f"Figura guardada en {SALIDA}")
