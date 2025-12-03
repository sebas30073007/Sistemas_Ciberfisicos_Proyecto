---
title: APIs y Backend
layout: default
parent: Nube
nav_order: 2
redirect_from:
  - /deteccion-clasificacion/pipeline-vision/
---

# Backend y API REST

El sistema de gestión de usuarios y puntuación reside en la nube, desacoplando la lógica de datos de la operación robótica local. Esta arquitectura asegura que los datos de reciclaje sean persistentes y accesibles remotamente.

## Arquitectura del Servidor

El backend está construido bajo una arquitectura de microservicios utilizando las siguientes tecnologías:

* **Servidor de Aplicaciones:** Python **Flask**, desplegado en **Render**. Se encarga de recibir las peticiones HTTP de la estación robótica, procesar la lógica de negocio y validar las transacciones.
* **Base de Datos:** **Google Firebase**. Se utiliza como almacén NoSQL en tiempo real para guardar los perfiles de usuario (vinculados a su Tag RFID) y su saldo de puntos.

## Definición de Endpoints

La API expone tres funciones principales que son consumidas por el controlador central (Raspberry Pi) mediante peticiones HTTP estándar.

### 1. Registro de Usuario (`/create_user`)
Permite dar de alta un nuevo usuario en el sistema asociando un identificador único de tarjeta.

* **Método:** `POST`
* **Parámetros:**
    * `rfid_uid` (string): Identificador único del Tag RFID leído.
* **Lógica:** Verifica si el ID ya existe en Firebase. Si no, crea un nuevo documento de usuario con saldo inicial de 0.

### 2. Consulta de Saldo (`/get_points`)
Se utiliza para mostrar al usuario sus puntos acumulados en la pantalla de la estación antes o después de reciclar.

* **Método:** `GET`
* **Parámetros:**
    * `rfid_uid`: El ID del usuario a consultar.
* **Respuesta (JSON):**

{% raw %}
~~~json
{
  "status": "success",
  "user": "Usuario_A1B2",
  "current_points": 1250
}
~~~
{% endraw %}

### 3. Sumar Puntos (`/add_point`)
Este es el endpoint crítico que se ejecuta automáticamente cuando el sistema de visión confirma que el residuo ha sido clasificado y el robot ha completado la trayectoria.

* **Método:** `POST`
* **Body (JSON):**

{% raw %}
~~~json
{
  "rfid_uid": "A1B2C3D4",
  "waste_type": "lata"
}
~~~
{% endraw %}

* **Lógica en Servidor:**
    1. Recibe el tipo de residuo (`lata`, `tetra`, `vidrio`).
    2. Asigna el valor en puntos predefinido (ej. Lata=10, Vidrio=20).
    3. Busca al usuario en **Firebase** y actualiza atómicamente su saldo.
    4. Devuelve el nuevo saldo confirmado.

## Implementación

El servidor Flask utiliza el SDK `firebase-admin` para comunicarse de forma segura con la base de datos. Un fragmento representativo de la lógica de sumatoria es:

{% raw %}
~~~python
@app.route('/add_point', methods=['POST'])
def add_point():
    data = request.json
    uid = data.get('rfid_uid')
    waste_type = data.get('waste_type')
    
    # Definición de valores
    points_map = {'lata': 10, 'tetra': 15, 'vidrio': 20}
    points_to_add = points_map.get(waste_type, 0)
    
    # Referencia a la base de datos
    user_ref = db.collection('users').document(uid)
    
    # Transacción de actualización
    user_ref.update({
        'points': firestore.Increment(points_to_add),
        'last_recycle': firestore.SERVER_TIMESTAMP
    })
    
    return jsonify({"success": True, "added": points_to_add}), 200
~~~
{% endraw %}