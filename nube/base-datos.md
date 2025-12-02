---
title: Base de datos
layout: default
parent: Nube
nav_order: 1
redirect_from:
  - /deteccion-clasificacion/gestion-datos/
---

Se uitlizó la base de datos Firebase Realtime Database ingresando la estructura siguiente
- `usuarios/`
  - `[ID_USUARIO]/`
    - `fecha_creacion`: "YYYY-MM-DD HH:MM:SS"
    - `lata`: 0
    - `nombre`: ""
    - `tetra`: 0
    - `vidrio`: 0

Cada usuario tiene esta misma estructura. Para acceder a la base de datos se necesita la llave de otra forma, no sería posible. Además se usa la librería firebase_admin y de esta credentials y db.
