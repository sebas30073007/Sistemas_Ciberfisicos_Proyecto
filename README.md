# Robot Clasificador de Residuos

Este repositorio contiene la documentación del proyecto final de la materia **Sistemas Ciberfísicos**. El sistema consiste en un robot móvil que recolecta residuos y los clasifica en vidrio, latas y envases Tetra Pak mediante visión artificial y una interfaz de usuario para monitoreo.

## Estructura del sitio

El sitio está construido con [Jekyll](https://jekyllrb.com/) y el tema [Just the Docs](https://just-the-docs.github.io/just-the-docs/). La navegación principal está organizada por secciones temáticas:

- `conexiones/`: Esquemas eléctricos, asignación de pines y distribución de alimentación.
- `estructura/`: Diseño mecánico del chasis, compartimentos y mecanismos de recolección.
- `ui/`: Interfaces para la operación del robot, paneles de monitoreo y flujos de interacción.
- `deteccion-clasificacion/`: Algoritmos de percepción, dataset y lógica de clasificación de residuos.

Cada directorio cuenta con un `index.md` que introduce la sección y varias páginas hijas con detalles específicos.

## Desarrollo local

1. Instala las dependencias: `bundle install`.
2. Levanta un servidor de desarrollo: `bundle exec jekyll serve`.
3. Abre el sitio en `http://localhost:4000` para revisar cambios.

## Contribuciones

- Documenta los cambios relevantes en la sección correspondiente.
- Usa títulos, tablas y diagramas que faciliten la comprensión.
- Mantén la navegación consistente actualizando `nav_order` y relaciones padre/hijo en el front matter.

## Licencia

Este proyecto mantiene la licencia original MIT del template.
