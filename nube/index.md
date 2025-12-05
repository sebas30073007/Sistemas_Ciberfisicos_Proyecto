---
title: Nube
layout: default
nav_order: 3
has_children: true
permalink: /nube/
redirect_from:
  - /deteccion-clasificacion/
---

Esta sección reúne los servicios desplegados en la nube: bases de datos, APIs, IA, dashboards y contratos de integración. Conserva la información técnica previa sobre detección, clasificación y gestión de datos, ahora organizada por dominio lógico.

Se centraliza toda la informacion de los componentes fisicos para hacer contacto con la nube a traves del servidor.

**Código completo de Servidor**
   [📁 Ver código completo del servidor](https://github.com/sebas30073007/Sistemas_Ciberfisicos_Proyecto/blob/main/assets/documentos/servidor.py)

### **Flujo principal del robot:**

```python
def main():
    """Secuencia completa del robot UR3"""
    move_home()                    # 1. Ir a posición inicial
    obj = mover()                  # 2. Abrir puerta y detectar objeto
    if obj and obj != "bg":
        run_urp_sequence([         # 3. Ejecutar secuencia de recolección
            RECOLECCION_PROGS[obj]
        ])
        sumar()                    # 4. Sumar puntos al usuario
```
