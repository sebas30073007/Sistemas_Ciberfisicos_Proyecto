---
title: Interfaz HMI
layout: default
parent: Interfaz Usuario
nav_order: 2
---

## Vistas de la Interfaz

A continuación se presentan las pantallas principales del entorno gráfico desarrollado en **Tkinter** para la Raspberry Pi.  
Cada ventana está diseñada con imágenes de fondo y botones personalizados, asegurando una experiencia intuitiva para el usuario.

### Pantalla 1 – Bienvenida  
![Vista de pantalla de bienvenida]({{ "/assets/img/ini.png" | relative_url }})

### Pantalla 2 – Escaneo de Tarjeta (Inicio de sesión)  
![Vista de pantalla de escaneo de tarjeta para iniciar sesión]({{ "/assets/img/rfid.png" | relative_url }})

### Pantalla 3 – Escaneo de Tarjeta (Crear cuenta)  
![Vista de pantalla de escaneo de tarjeta para crear cuenta]({{ "/assets/img/rfid.png" | relative_url }})

### Pantalla 4 – Crear cuenta (Ingreso de nombre y foto)  
![Vista de pantalla para crear cuenta]({{ "/assets/img/crea1.png" | relative_url }})

### Pantalla 5 – Crear cuenta (Captura de foto)  
![Vista de pantalla para captura de foto al crear cuenta]({{ "/assets/img/crea2.png" | relative_url }})

### Pantalla 6 – Crear cuenta (Cuenta registrada)  
![Vista de pantalla al haber creado una cuenta]({{ "/assets/img/crea3.png" | relative_url }})

### Pantalla 5 – Inicio de sesión 
![Vista de pantalla de inicio de sesión]({{ "/assets/img/inises.png" | relative_url }})

### Pantalla 6 – Cargar objeto  
![Vista de pantalla de carga de objeto]({{ "/assets/img/rec.png" | relative_url }})

---

## Descripción general del sistema HMI

Esta interfaz gráfica actúa como el **puente entre el usuario y el sistema embebido**.  
Su propósito principal es permitir que los usuarios se registren o inicien sesión mediante una **tarjeta RFID**, y posteriormente interactúen con las funciones disponibles (como carga de objetos o consulta de puntos). De igual forma esta la posibilidad de cargar un objeto para reciclar sin la necesidad de una tarjeta RFID.

El HMI fue desarrollado en **Python 3**, utilizando las siguientes bibliotecas:
- `tkinter` → creación de ventanas, botones y eventos.
- `PIL (ImageTk)` → manejo y escalado de imágenes.
- `requests` → envío de datos JSON al servidor (para la comunicación con backend).
- `mfrc522` → lectura del identificador RFID.

---

## Flujo general del programa

1. **Pantalla de Bienvenida:**  
   El usuario selecciona si desea **iniciar sesión**, **crear una cuenta nueva** o **reciclar sin cuenta**.  Esta ultima opcion es por si el usuario no dispone de una tarjeta RFID aunque al seleccionar esta opción el usuario no dispondrá de un record de puntos.

2. **Lectura de Tarjeta RFID:**  
   Al acercar una tarjeta al lector **RC522**, el sistema obtiene su **ID único**.  
   Una vez leído el ID, el flujo continúa automáticamente:
   - Si se seleccionó “Iniciar sesión” → pasa a la pantalla de login.
   - Si se seleccionó “Crear cuenta” → pasa a la pantalla para ingresar nombre.
   - Si se seleccionó “Reciclar sin cuenta” → pasa a la pantalla cargar un objeto para reciclar.

3. **Registro de nuevo usuario:**  
   En la pantalla de registro, el usuario ingresa su nombre y se muestra un popup de **“Tomar Foto”** (simulado).
   Al confirmar, el sistema guarda el nombre y el id en un archivo `usuarios.txt` y envía los datos por **JSON** al servidor configurado (ej. `172.22.22.128`), con el siguiente formato:

   ```json
   {
     "rfid": "ID_de_la_tarjeta",
     "usuario": "Nombre_ingresado"
   }
