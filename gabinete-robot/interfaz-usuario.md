---
title: Interfaz Usuario
layout: default
parent: Gabinete Robot
nav_order: 2
has_children: true
---

# Interfaz de Usuario

La interfaz de usuario del robot es el punto de contacto directo con la persona que deposita los residuos. Está pensada para guiar la interacción de forma intuitiva, brindar retroalimentación inmediata y permitir un diagnóstico rápido por parte del equipo técnico.

---

![UI]({{ "/assets/img/UI.jpg" | relative_url }})

## Componentes principales

| Módulo | Función | Interacción clave |
| --- | --- | --- |
| **HMI basada en Raspberry Pi** | Presenta instrucciones, confirma acciones y habilita el flujo de trabajo del depósito. | Pantalla táctil de 7" con interfaz gráfica dedicada. |
| **Módulo RFID embebido** | Identifica tarjetas de usuarios autorizados y genera confirmaciones sonoras. | Antena frontal, lector integrado y buzzer de notificación. |

Ambos módulos comparten alimentación desde el gabinete y se comunican con el sistema principal a través de la red local interna.

## Flujo de interacción

1. La persona usuaria acerca su tarjeta RFID, activando la autenticación y el registro del depósito.
2. La HMI despliega el estado del sistema (disponible, en proceso o en mantenimiento) y guía los pasos a seguir.
3. Si se detecta alguna condición de error, la interfaz muestra mensajes específicos y ofrece instrucciones de recuperación.

Este flujo permite mantener la operación autónoma, al tiempo que habilita un modo de servicio donde el personal técnico puede acceder a opciones avanzadas desde la propia HMI.

## Cómo profundizar

- Revisa el **[diseño de la PCB del módulo RFID](./interfaz-usuario/diseno-pcb.html)** para conocer la distribución de componentes, el ruteo y la lógica de validación.
- Explora la página de la **[interfaz HMI](./interfaz-usuario/hmi.html)** para ver capturas de la aplicación, dependencias de software y pautas de despliegue.

Cada subpágina incluye diagramas, listas de materiales y notas de implementación que complementan este resumen de alto nivel.
