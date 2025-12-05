# codigo.py
import os, json, time, threading, queue, traceback, requests
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import RPi.GPIO as GPIO
from datetime import datetime
import serial
import firebase_admin
from firebase_admin import credentials, db

# Configura Firebase
cred = credentials.Certificate("recicla.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://recicla-4ca43-default-rtdb.firebaseio.com/'
})

servidor="http://192.168.1.60:5000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#apirecicla="https://recicla.onrender.com" # api de render
class FirebaseWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.queue = queue.Queue(maxsize=10)
        self.stop_ev = threading.Event()

    def guardar_en_firebase(self, data):
        """Guarda los datos en Firebase Firestore"""
        try:
            # Verificar que tenemos conexión a Firebase
            if not firebase_admin._apps:
                print("[ERR] Firebase no está inicializado")
                return False
                
            # Crear referencia a la colección 'registros'
            doc_ref = db.collection('registros').document()
            
            # Agregar timestamp
            data['timestamp'] = firestore.SERVER_TIMESTAMP
            data['fecha_registro'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Guardar en Firebase
            doc_ref.set(data)
            print(f"Datos guardados en Firebase: {data}")
            return True
            
        except Exception as e:
            print(f"[ERR] Error guardando en Firebase: {e}")
            return False

    def run(self):
        while not self.stop_ev.is_set():
            try:
                task = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                data = task.get("data")
                if not data:
                    continue
                    
                self.guardar_en_firebase(data)
                    
            except Exception as e:
                print(f"[ERR] No se pudo guardar en Firebase: {e}")
            finally:
                self.queue.task_done()

    def enqueue(self, data):
        try:
            self.queue.put_nowait({"data": data})
        except queue.Full:
            print("[WARN] Cola llena -> descartado")

    def stop(self):
        self.stop_ev.set()

firebase_worker = FirebaseWorker()
firebase_worker.start()

ventana_principal = None
ventanas_activas = {}
id_tarjeta_actual = None

# Cache para imágenes
imagenes_cache = {}

def cargar_imagen(nombre):
    """Carga imágenes y las mantiene en cache"""
    if nombre not in imagenes_cache:
        ruta = os.path.join(BASE_DIR, nombre)
        imagenes_cache[nombre] = ImageTk.PhotoImage(Image.open(ruta))
    return imagenes_cache[nombre]

def ocultar_todas_las_ventanas():
    """Oculta todas las ventanas excepto la principal"""
    for nombre, ventana in ventanas_activas.items():
        try:
            ventana.withdraw()
        except:
            pass
    ventanas_activas.clear()

def mostrar_ventana(nombre, ventana):
    """Muestra una ventana y oculta las demás"""
    ocultar_todas_las_ventanas()
    ventanas_activas[nombre] = ventana
    ventana.deiconify()

def verificar_conexion_firebase():
    """Verifica si Firebase está disponible"""
    try:
        if firebase_admin._apps:
            return True
        else:
            return False
    except:
        return False

def verificar_conexion_y_mostrar_error():
    """Verifica la conexión a Firebase y muestra error si no hay"""
    if not verificar_conexion_firebase():
        messagebox.showerror("Error de Conexión", 
                           "No hay conexión a Firebase. Verifique su conexión a internet.")
        mostrarBienvenido()
        return False
    return True

def leer_tarjeta(callback):
    """
    Lee una tarjeta RFID en un hilo para no congelar la GUI.
    Llama a callback(id_tarjeta) cuando se detecta.
    """
    def tarea():
        global id_tarjeta_actual
        try:
            print("Esperando tarjeta RFID...")
            ser=serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            time.sleep(0.5)
            while True:
                linea=ser.readline().decode('utf-8', errors='ignore').strip()
                if linea:
                    print(f"Tarjeta detectada: {linea}")
                    id_tarjeta_actual=linea
                    try:
                        callback(linea)
                    except Exception as cb_e:
                        print(f"[ERR] Al leer tarjeta: {cb_e}")
                    break
        except Exception as e:
            print(f"[ERR] Al leer tarjeta por USB {e}")
        finally:
            try:
                if 'ser' in locals() and ser.is_open:
                    ser.close()
            except Exception:
                pass
            
    threading.Thread(target=tarea, daemon=True).start()
    
def activar_inactividad(ventana, inactivo_ms):
    timer_id = None
    def reiniciar_timer(event=None):
        nonlocal timer_id
        if timer_id:
            ventana.after_cancel(timer_id)
        timer_id = ventana.after(inactivo_ms, mostrarBienvenido)
    ventana.bind_all("<Motion>", reiniciar_timer)
    ventana.bind_all("<Key>", reiniciar_timer)
    ventana.bind_all("<Button>", reiniciar_timer)
    reiniciar_timer()

def validar_nombre(nombre):
    nombre = nombre.strip()
    if not nombre:
        return False, "El nombre no puede estar vacío"
    if len(nombre) > 20:
        return False, "El nombre no puede tener más de 20 caracteres"
    if nombre.isspace():
        return False, "El nombre no puede contener solo espacios"
    return True, ""

def crear_ventana_base(titulo):
    global ventana_principal
    
    if ventana_principal is None:
        ventana_principal = tk.Tk()
        ventana_principal.title(titulo)
        ventana_principal.geometry("480x800")
        ventana_principal.configure(background="#C3EEAF")
    else:
        for widget in ventana_principal.winfo_children():
            widget.destroy()
        ventana_principal.title(titulo)

    imgfondo = cargar_imagen("latagrande.png")
    tk.Label(ventana_principal, image=imgfondo, bg="#C3EEAF").place(x=-35, y=11)

    imgbien = cargar_imagen("bienvenidos.png")
    tk.Label(ventana_principal, image=imgbien, bg="#C3EEAF").place(x=51, y=33)

    imgpara = cargar_imagen("paraempezar.png")
    tk.Label(ventana_principal, image=imgpara, bg="#C3EEAF").place(x=41, y=111)

    crear_boton(ventana_principal, 108, 226,
                cargar_imagen("btnini.png"),
                cargar_imagen("btninis.png"),
                cargar_imagen("btninip.png"),
                comando=escanearTarjeta)

    crear_boton(ventana_principal, 108, 370,
                cargar_imagen("btncrea.png"),
                cargar_imagen("btncreas.png"),
                cargar_imagen("btncreap.png"),
                comando=escanearTarjetaCta)

    crear_boton(ventana_principal, 63, 514,
                cargar_imagen("btnrec.png"),
                cargar_imagen("btnrecs.png"),
                cargar_imagen("btnrecp.png"),
                comando=cargarObj)

    extra_img = cargar_imagen("reclama.png")
    tk.Label(ventana_principal, image=extra_img, bg="#C3EEAF").place(x=78, y=640)
    
    return ventana_principal

def crear_boton(win, x, y, normal, hover, pressed, comando=None):
    btn = tk.Label(win, image=normal, bd=0, bg="#C3EEAF")
    btn.image_normal = normal
    btn.image_hover = hover
    btn.image_pressed = pressed

    def on_enter(e): btn.config(image=hover)
    def on_leave(e): btn.config(image=normal)
    def on_press(e): btn.config(image=pressed)
    def on_release(e):
        btn.config(image=hover)
        if comando: 
            # Verificar conexión antes de ejecutar comandos que envían datos
            if comando in [escanearTarjeta, escanearTarjetaCta, cargarObj]:
                if not verificar_conexion_y_mostrar_error():
                    return
            comando()
            
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.bind("<ButtonPress-1>", on_press)
    btn.bind("<ButtonRelease-1>", on_release)
    btn.place(x=x, y=y)
    return btn

def mostrarBienvenido():
    ocultar_todas_las_ventanas()
    ventana = crear_ventana_base("Bienvenido")
    mostrar_ventana("principal", ventana)

def escanearTarjeta():
    # Verificar conexión antes de proceder
    if not verificar_conexion_y_mostrar_error():
        return
        
    ocultar_todas_las_ventanas()
    
    ventana = tk.Toplevel()
    ventana.title("Escaneo")
    ventana.geometry("480x800")
    ventana.configure(background="#C3EEAF")

    aviso = cargar_imagen("acercatrj.png")
    tk.Label(ventana, image=aviso, bg="#C3EEAF").place(x=117, y=150)
    aviso2 = cargar_imagen("tarjeta.png")
    tk.Label(ventana, image=aviso2, bg="#C3EEAF").place(x=67, y=445)
    
    def on_card(id_tarjeta):
        #ventana.withdraw()
        cargarObjCta(id_tarjeta, ventana)

    leer_tarjeta(on_card)
    mostrar_ventana("escanear", ventana)

def escanearTarjetaCta():
    if not verificar_conexion_y_mostrar_error():
        return
    ocultar_todas_las_ventanas()
    ventana = tk.Toplevel()
    ventana.title("Escaneo")
    ventana.geometry("480x800")
    ventana.configure(background="#C3EEAF")

    aviso = cargar_imagen("acercatrj.png")
    tk.Label(ventana, image=aviso, bg="#C3EEAF").place(x=117, y=150)
    aviso2 = cargar_imagen("tarjeta.png")
    tk.Label(ventana, image=aviso2, bg="#C3EEAF").place(x=67, y=445)

    def on_card(id_tarjeta):
        ref = db.reference(f"usuarios/{id_tarjeta}")
        usuario = ref.get()
        if usuario is not None: # Ya existe -> NO crear cuenta
            yaexiste = tk.Toplevel(ventana)
            yaexiste.geometry("290x200")
            yaexiste.title("Cuenta existente")
            yaexiste.configure(bg="#95D279")
            yaexiste.transient(ventana)
            yaexiste.grab_set()
            img_ctr = cargar_imagen("existe.png")
            tk.Label(yaexiste, image=img_ctr, bg="#95D279").place(relx=0.5, rely=0.5, anchor="center")
            def cerrarExiste():
                yaexiste.destroy()
                mostrarBienvenido()
            yaexiste.after(2000, cerrarExiste)
            return
        ventana.withdraw()
        creaCta(id_tarjeta, ref)
    leer_tarjeta(on_card)
    mostrar_ventana("escanear_cta", ventana)

def creaCta(id_tarjeta, ref):
    ventana = tk.Toplevel()
    ventana.title("Crear Cuenta")
    ventana.geometry("480x800")
    ventana.configure(background="#C3EEAF")

    activar_inactividad(ventana, 50000)

    nom = cargar_imagen("escribe.png")
    tk.Label(ventana, image=nom, bg="#C3EEAF").place(x=59, y=163)

    entry_nombre = tk.Entry(ventana, font=("Arial", 28), justify="center")
    entry_nombre.place(x=59, y=217, width=347, height=60)

    # teclado táctil
    teclado = tk.Frame(ventana, width=460, height=385, bg="#95D279")
    teclado.place(x=15, y=424)

    def escribir(c):
        entry_nombre.insert(tk.END, c)
    def borrar():
        entry_nombre.delete(len(entry_nombre.get())-1, tk.END)

    letras = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
    fila, col = 0, 0
    for letra in letras:
        tk.Button(teclado, text=letra, font=("Arial", 22),
                  width=2, height=1, command=lambda l=letra: escribir(l)).grid(row=fila, column=col, padx=2, pady=2)
        col += 1
        if col > 6:
            col, fila = 0, fila + 1
    tk.Button(teclado, text="BORRAR", font=("Arial", 20),
              command=borrar).grid(row=fila+1, column=0, columnspan=8, pady=10)

    def guardar_nombre():
        nombre = entry_nombre.get()
        es_valido, msg = validar_nombre(nombre)
        if not es_valido:
            popno = tk.Toplevel(ventana)
            popno.geometry("250x130")
            popno.title("No aceptado")
            popno.configure(bg="#95D279")
            popno.transient(ventana)  # Hacerla hija de la ventana principal
            popno.grab_set()  # Modal
            
            imgcenter = cargar_imagen("nomno.png")
            tk.Label(popno, image=imgcenter, bg="#95D279").place(relx=0.5, rely=0.5, anchor="center")
            popno.after(3000, popno.destroy)
            return
        
        # Verificar conexión antes de guardar
        if not verificar_conexion_y_mostrar_error():
            return

        nuevo_usuario = {
            "nombre": nombre,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "vidrio": 0,
            "lata": 0,
            "tetra": 0
        }
        ref.set(nuevo_usuario)
        print(f"Usuario '{nombre}' creado con ID {id_tarjeta}.")

        popup = tk.Toplevel(ventana)
        popup.geometry("220x114")
        popup.title("Cuenta creada")
        popup.configure(bg="#95D279")
        popup.transient(ventana)  # Hacerla hija de la ventana principal
        popup.grab_set()  # Modal
        
        img_centro = cargar_imagen("usureg.png")
        tk.Label(popup, image=img_centro, bg="#95D279").place(relx=0.5, rely=0.5, anchor="center")
        
        def cerrar_todo():
            popup.destroy()
            ventana.withdraw()
            mostrarBienvenido()
            
        popup.after(2000, cerrar_todo)
    
    crear_boton(ventana, 125, 322,
                cargar_imagen("btnenviar.png"),
                cargar_imagen("btnenviars.png"),
                cargar_imagen("btnenviarp.png"),
                comando=guardar_nombre)
    
    mostrar_ventana("crear_cuenta", ventana)
    
def cargarObjCta(id_tarjeta, ventana_escanear=None):
    
    def tarea_api():
        print(f"\n[API] Consultando tarjeta {id_tarjeta} ...")
        url = f"{servidor}/consulta/{id_tarjeta}"

        data = None
        try:
            r = requests.get(url, timeout=25)
            print(f"[API] Status: {r.status_code}")
            print("[API] RAW:", r.text[:1000])  # imprime primer bloque por debug

            if r.status_code == 200:
                try:
                    data = r.json()
                    print("[API] JSON recibido:")
                    print(json.dumps(data, indent=4))
                except Exception as e:
                    print("[API] Error decodificando JSON:", e)
                    data = None
            else:
                print("[API] Status no OK:", r.status_code)
                data = None

        except Exception as e:
            print("[API] Excepción consultando API:", e)
            data = None

        # Llamar a la UI en hilo principal (sin bloquear)
        ventana_principal.after(0, lambda: procesar_respuesta_ui(data, id_tarjeta, ventana_escanear))

    def popup_no_existe_and_back():
        # Popup centrado 409x211 con imagen noexiste.png, cierra y vuelve a inicio
        popup = tk.Toplevel()
        popup.title("No encontrado")
        w, h = 409, 211
        # centrar en pantalla
        x = (popup.winfo_screenwidth() // 2) - (w // 2)
        y = (popup.winfo_screenheight() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.resizable(False, False)
        popup.configure(bg="#C3EEAF")

        img = cargar_imagen("noexiste.png")
        tk.Label(popup, image=img, bg="#C3EEAF").pack(expand=True)
        popup.img = img  # mantener referencia

        def cerrar():
            try:
                popup.destroy()
            except:
                pass
            mostrarBienvenido()

        popup.after(2000, cerrar)

    def procesar_respuesta_ui(data, tarjeta, ventana_escanear_local):
        # Si la ventana de escaneo fue cerrada por otro flujo, ignorar
        if ventana_escanear_local is not None:
            try:
                # solo withdraw/destroy si aún existe y es una ventana válida
                if str(ventana_escanear_local) in ventana_escanear_local.winfo_toplevel().wm_geometry():
                    # no reliably check, but attempt safe withdraw/destroy
                    ventana_escanear_local.withdraw()
            except Exception:
                # Si no podemos withdraw, ignorar (no crítico)
                pass

        # Si no hay data válida -> popup y volver a inicio
        if not data or "respuesta_render" not in data:
            popup_no_existe_and_back()
            return

        # JSON válido -> construimos la ventana Cargar Objeto
        construir_cargar_objeto(data)

    def construir_cargar_objeto(data):
        url = f"{servidor}/empezarObjeto"
        payload = {"start": 1}
        try:
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status() 
            try:
                respuesta_json = response.json()
                print("--- Respuesta del Servidor (JSON) ---")
                print(json.dumps(respuesta_json, indent=4))
            except requests.exceptions.JSONDecodeError:
                print("--- Respuesta del Servidor (Texto) ---")
                print(response.text)
        except requests.exceptions.Timeout:
            print(f"Error: La solicitud a {url} ha expirado (timeout).")
        except requests.exceptions.RequestException as e:
            print(f"Error al hacer la solicitud a {url}: {e}")
    
        ocultar_todas_las_ventanas()
        info=data["respuesta_render"]
        
        ventana = tk.Toplevel()
        ventana.title("Cargar Objeto")
        ventana.geometry("480x800")
        ventana.configure(background="#C3EEAF")
        
        activar_inactividad(ventana, 90000)
        imgfondo = cargar_imagen("latagrande.png")
        tk.Label(ventana, image=imgfondo, bg="#C3EEAF").place(x=0, y=100)
        ventana.imgfondo = imgfondo

        lblusu = cargar_imagen("usu.png")
        tk.Label(ventana, image=lblusu, bg="#C3EEAF").place(x=42, y=40)
        ventana.lblusu = lblusu
        
        lblnom=tk.Label(ventana, text=f"{info['nombre']}", font=("Arial", 28), bg="#C3EEAF", fg="#000000")
        lblnom.place(x=182, y=29)
        
        lblpts = cargar_imagen("pts.png")
        tk.Label(ventana, image=lblpts, bg="#C3EEAF").place(x=42, y=87)
        ventana.lblpts = lblpts
        
        lbltot=tk.Label(ventana, text=f"{info['total']}", font=("Arial", 28), bg="#C3EEAF", fg="#000000")
        lbltot.place(x=182, y=80)
        
        lblidd = cargar_imagen("idd.png")
        tk.Label(ventana, image=lblidd, bg="#C3EEAF").place(x=42, y=134)
        ventana.lblidd = lblidd
        
        lbluid=tk.Label(ventana, text=f"{info['user_id']}", font=("Arial", 28), bg="#C3EEAF", fg="#000000")
        lbluid.place(x=182, y=127)
        
        # Botón cargar objeto (reutiliza la misma función, pasando la ventana actual si quieres)
        crear_boton(
            ventana, 63, 457,
            cargar_imagen("btncargar.png"),
            cargar_imagen("btncargars.png"),
            cargar_imagen("btncargarp.png"),
            comando=lambda: cargarObjCta(info.get("user_id"), ventana)  # recargar si quieres
        )

        crear_boton(
            ventana, 143, 607,
            cargar_imagen("btnterm.png"),
            cargar_imagen("btnterms.png"),
            cargar_imagen("btntermp.png"),
            comando=mostrarBienvenido
        )

        mostrar_ventana("cargar_objeto", ventana)

    # arrancar hilo de consulta
    threading.Thread(target=tarea_api, daemon=True).start()


def cargarObj():
    url = f"{servidor}/empezarObjeto"
    payload = {"start": 1}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status() 
        try:
            respuesta_json = response.json()
            print("--- Respuesta del Servidor (JSON) ---")
            print(json.dumps(respuesta_json, indent=4))
        except requests.exceptions.JSONDecodeError:
            print("--- Respuesta del Servidor (Texto) ---")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print(f"Error: La solicitud a {url} ha expirado (timeout).")
        mostrarBienvenido()
    except requests.exceptions.RequestException as e:
        print(f"Error al hacer la solicitud a {url}: {e}")
        mostrarBienvenido()
    
    ventana = tk.Toplevel()
    ventana.title("Cargar Objeto")
    ventana.geometry("480x800")
    ventana.configure(background="#C3EEAF")
    activar_inactividad(ventana, 90000)
    
    imgfondo = cargar_imagen("latagrande.png")
    tk.Label(ventana, image=imgfondo, bg="#C3EEAF").place(x=0, y=100)
    ventana.imgfondo = imgfondo

    crear_boton(ventana, 63, 457,
                cargar_imagen("btncargar.png"),
                cargar_imagen("btncargars.png"),
                cargar_imagen("btncargarp.png"),
                comando=cargarObj)
    
    crear_boton(ventana, 143, 607,
                cargar_imagen("btnterm.png"),
                cargar_imagen("btnterms.png"),
                cargar_imagen("btntermp.png"),
                comando=mostrarBienvenido)
    mostrar_ventana("cargar_objeto", ventana)

# ==========================================================
if __name__ == "__main__":
    try:
        mostrarBienvenido()
        if ventana_principal:
            ventana_principal.mainloop()
    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
    finally:
        firebase_worker.stop()
        firebase_worker.join(timeout=1.0)
        GPIO.cleanup()
        print("Fin del programa limpio.")