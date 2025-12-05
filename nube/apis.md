---
title: APIs y Backend
layout: default
parent: Nube
nav_order: 2
redirect_from:
  - /deteccion-clasificacion/pipeline-vision/
---

# Backend y API REST

El servidor en la nube es el encargado de administrar el registro de usuarios, el conteo de materiales reciclados y la generación de rankings. Toda la lógica principal se centraliza en este backend, mientras que el robot, la aplicación web y las estaciones cliente únicamente realizan consultas o actualizaciones a través de la API.

---

## Arquitectura del Servidor

El backend está implementado mediante los siguientes componentes:

* **Servidor de Aplicaciones:** Python **Flask**, desplegado en **Render**. Procesa todas las solicitudes provenientes del robot, la web y cualquier cliente externo.
* **Base de Datos:** **Firebase Realtime Database**, utilizada para almacenar perfiles de usuario, contadores por categoría (lata, vidrio, tetrapak) y fechas de creación.
* **Manejo de CORS:** Configurado para permitir accesos desde cualquier origen, facilitando la conexión de dispositivos heterogéneos (robots, páginas web, aplicaciones móviles).

Además, las credenciales de Firebase se cargan mediante una **variable de entorno** (`FIREBASE_JSON`), dado que Render no permite subir archivos `.json` de llaves de servicio.

---

## Definición de Endpoints

La API contiene diferentes funciones que permiten consultar, crear usuarios, registrar reciclaje y generar rankings globales.

### 1. Registro de Usuario (`/crear_usuario/<user_id>/<nombre>`)

Permite crear un nuevo usuario en la base de datos. Se usa cuando un nuevo usuario escanea por primera vez su tarjeta RFID o se registra manualmente.

* **Método:** `POST`
* **Parámetros en URL:**
  * `user_id`: UID único del usuario.
  * `nombre`: Nombre del usuario.
* **Lógica:**
  * Valida que el usuario no exista.
  * Crea un registro con valores iniciales de todas las categorías en 0.
  * Registra la fecha de creación.

---

### 2. Consulta de Usuario (`/consulta/<user_id>`)

Devuelve toda la información asociada al usuario, incluyendo la cantidad de latas, vidrio y tetra acumulados.

* **Método:** `GET`
* **Parámetros en URL:**
  * `user_id`: Identificador del usuario.
* **Respuesta (JSON):**

```json
{
  "user_id": "1234",
  "nombre": "ABCDE",
  "lata": 10,
  "vidrio": 10,
  "tetra": 15
}
```

---

### 3. Registro de Reciclaje (`sumar/<user_id>/<categoria>`)

Permite registrar una nueva unidad reciclada por un usuario en una categoría específica.

* **Método:** `POST`
* **Parámetros en URL:**
  * `user_id`: Identificador del usuario.
  * `categoria`: Categoria de objeto identificada.

Lógica:
- Valida que el usuario exista en la base de datos
- Verifica que la categoría sea válida
- Incrementa en 1 el contador correspondiente
- Actualiza el registro en Firebase

* **Respuesta (JSON):**

```json
{
  "categoria_actualizada": "lata",
  "nuevo_valor": 15
}
```
---

### 4. Rankings (`top_total`), (`top_latas`), (`top_vidrio`), (`top_tetra`)
Para el caso de top_total muestra los primeros 100 usuarios con mayor puntuación total (suma de todas las categorías). En el caso de los demás tops entonces muestra la mayor puntuación por categoría.

---

### 5. Errores
Para los diferentes casos de error hay los siguientes
`Usuario no encontrado`

```json
{
  "error": "El usuario con ID '999' no existe"
}
```

`Categoría inválida`

```json
{
  "error": "Categoría inválida. Usa 'lata', 'vidrio' o 'tetra'."
}
```

`Usuario ya existe`

```json
{
  "error": "El usuario con ID '001' ya existe"
}
```

---
### 6. Configuración
Las variables de entorno a utilizar son:

```json
FIREBASE_JSON = {
  "type": "service_account",
  "project_id": "recicla-4ca43",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "...",
  "token_uri": "...",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
```

La configuración **CORS** consiste en:
```json
CORS(app, 
     origins="*", 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
     allow_headers="*", 
     supports_credentials=True)
```

---

### 7 Logs

Logs en Render:
Accesos: Todas las peticiones HTTP se registran automáticamente
Errores: Las excepciones de Python se capturan y registran
Tiempos de respuesta: Render proporciona métricas de rendimiento
