# ⚙️ Suite de Síntesis y Optimización Cinemática / Kinematic Synthesis & Optimization Suite

---

## 📌 Descripción General / Overview

**🇪🇸 Español:**
Esta suite es un entorno modular en Python diseñado para la **síntesis dimensional, exploración paramétrica por barrido en rejilla (grid search), filtrado cinemático de defectos y optimización de mecanismos planos**. A diferencia de los programas de síntesis tradicional que evalúan un solo punto, este algoritmo realiza **barridos continuos y por subintervalos** para evaluar miles de combinaciones en el espacio de parámetros, descartando automáticamente soluciones inviables y clasificando las válidas según su calidad cinemática.

**🇬🇧 English:**
This suite is a modular Python environment designed for **dimensional synthesis, parametric grid search, kinematic defect filtering, and optimization of planar mechanisms**. Unlike traditional synthesis programs that evaluate a single solution point, this algorithm performs **continuous and sub-interval grid searches** across thousands of parameter combinations, automatically discarding unfeasible linkages and sorting valid ones based on transmission quality.

---

## 📁 Estructura del Repositorio / Repository Structure

```text
Sintesis_Cinematica_Suite/
│
├── 01_Generacion_Movimiento_3Pos/
│   ├── main.py                     # Script principal ejecutable en español / Main interactive script (ES)
│   ├── kinematic_sweep_3pos.py     # Versión traducida e internacionalizada / Internationalized script (EN)
│   └── mecanismos_sintetizados.txt # Archivo de salida / Output text file
│
├── 02_Generacion_Funcion/          # Módulo para generación de función (próximamente / coming soon)
├── 03_Generacion_Trayectoria/      # Módulo para generación de trayectoria (próximamente / coming soon)
├── 04_Sintesis_4_Posiciones/       # Curvas de Burmester para 4 posiciones (próximamente / coming soon)
│
├── docs/                           # Documentación teórica / Theoretical background & documentation
├── tests/                          # Pruebas unitarias / Unit tests & validation
├── README.md                       # Documentación bilingüe / Bilingual README
└── requirements.txt                # Dependencias del proyecto / Project dependencies