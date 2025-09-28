---
layout: default
title: Diagrama a bloques
parent: Conexiones
nav_order: 1
---


(assets/img/Diagrama_de_proyecto.png)
¿Cómo está armado?

La arquitectura tiene tres piezas que se hablan entre sí: el gabinete del robot (lo que está físicamente en la cabina), la nube (donde vive el registro, la IA y los dashboards) y las interfaces de usuario (pantalla local y sitio web/móvil).

En el gabinete vive la parte mecánica y de seguridad. El UR3 lleva una cámara (en la muñeca o fija dentro de la cabina) y un gripper para tomar el objeto. Alrededor hay sensores sencillos —barrera infrarroja, proximidad, peso e incluso uno inductivo para detectar metal— que avisan si ya metiste algo y si es seguro cerrar la compuerta. Un PLC se encarga de esos interlocks de seguridad (por ejemplo, que el robot no se mueva si la puerta está abierta), y una PC coordina al UR3, muestra la HMI local (instrucciones y resultado) y se comunica con la nube. Todo esto va conectado a un switch; es la red local del sistema.

La nube es el “cerebro administrativo”. Allí hay APIs en Python para recibir imágenes, correr la clasificación (ya sea en la nube o delegada desde el edge), guardar eventos y calcular conteos y puntuaciones. Una base de datos almacena usuarios, sesiones y evidencia (enlace a la foto con su fecha, material y confianza). Encima de eso hay dashboards web/móvil para ver KPIs del proyecto (actividad, exactitud, tiempos) y para mostrar el ranking y la tabla de puntos.

Las interfaces cierran el círculo. La pantalla de la cabina te guía paso a paso: te puedes identificar (RFID/QR), depositas el residuo, ves la foto y el resultado, y escuchas la confirmación. Fuera de la cabina, cualquier persona puede entrar al sitio para ver el ranking general, su propio historial y —cuando esté activo— las reglas de premios.

¿Qué pasa cuando alguien usa la máquina?

Cuando te acercas, puedes identificarte (o jugar anónimo). La cabina detecta el objeto y toma una foto; esa imagen se normaliza y se envía a la IA para decidir la clase. Con el resultado, el UR3 toma el residuo y lo deja en el contenedor correspondiente. En paralelo, la PC registra un evento en la base de datos con todo lo necesario para trazabilidad: quién (si hubo login), qué material, confianza del modelo, cuándo, en qué máquina, enlace a la foto y tiempo de ciclo. Si estabas identificado, el sistema actualiza tu score y tu posición en el ranking; la HMI te lo muestra al instante y el dashboard lo refleja en la web.

¿Qué datos son los importantes?

El sistema cuida pocos, pero muy claros: id de usuario (si aplica) y alias, id de la máquina, fecha/hora en UTC, material clasificado, confianza de la IA, link a la imagen, duración del ciclo y puntos otorgados. Con eso puedes auditar cada evento, medir la calidad del modelo y darle sentido al juego (ranking y premios).

¿Qué asegura que funcione bien?

La cabina prioriza la seguridad (interlocks del PLC, paro de emergencia, enclavamiento de puerta) y la confiabilidad (si se cae internet, la PC puede bufferizar eventos e imágenes y reintentarlos después). La comunicación con la nube viaja por HTTPS y las APIs usan tokens para evitar accesos no autorizados. En la parte social, la privacidad es simple: si no te identificas, el evento queda anónimo y solo alimenta métricas globales.

¿Qué valor aporta esta arquitectura?

Hace visible lo invisible del reciclaje: muestra el proceso (robot en acción), refuerza el comportamiento con feedback inmediato (resultado y puntos) y construye comunidad con el ranking. Técnicamente es modular: puedes mejorar el gripper, cambiar el modelo de IA, o sumar nuevos sensores sin reescribir todo. Socialmente, convierte un acto cotidiano en una experiencia memorable.