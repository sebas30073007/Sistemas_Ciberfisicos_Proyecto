"""
server.py — Servidor Flask central de la PC.

Reemplaza:
  - jetson/prueba.py   (proxy a Render)
  - jetson/oficial.py  (rutas de usuario — ahora con CSV local)
  - jetson/servidor.py (relay de clasificación)

Endpoints de usuario:
  GET  /consulta/<user_id>          → datos del usuario desde CSV
  POST /sumar/<user_id>/<categoria> → incrementa categoría (+1) en CSV
  POST /crear_usuario               → crea nuevo usuario en CSV
  GET  /existe/<user_id>            → verifica si el usuario existe

Endpoints de control:
  POST /empezarObjeto               → lanza orquestador en hilo daemon
  GET  /estado                      → {"ocupado": bool}
  GET  /health                      → estado general del servidor

Panel demo:
  GET  /demo                        → página HTML con toggles y botón ejecutar
  POST /demo/config                 → actualiza config.DEMO en runtime
  GET  /demo/estado                 → JSON con ocupado + config actual (para el panel)
"""

import csv
import io
import os
import contextlib
import threading
import traceback
from datetime import datetime
from collections import deque

from flask import Flask, jsonify, request, Response, send_file
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

import config
from config import DEMO, DB_PATH, PC_HOST, PC_PORT

app = Flask(__name__)
CORS(app)

# Lock para acceso concurrente al CSV
_csv_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Log de debug en memoria (últimas 300 líneas)
# ---------------------------------------------------------------------------
_debug_log   = deque(maxlen=300)
_debug_lock  = threading.Lock()

def _log(msg: str):
    """Registra en consola y en el buffer de debug."""
    ts  = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with _debug_lock:
        _debug_log.append(line)

def _run_capture(fn, *args, label="", **kwargs):
    """
    Ejecuta fn() redirigiendo stdout a un buffer.
    Devuelve (ok, output_str, error_str).
    """
    buf = io.StringIO()
    ok  = True
    err = ""
    with contextlib.redirect_stdout(buf):
        try:
            fn(*args, **kwargs)
        except Exception as e:
            ok  = False
            err = str(e)
            traceback.print_exc(file=buf)
    out = buf.getvalue()
    _log(f"{label} {'OK' if ok else 'ERROR: ' + err}")
    for line in out.splitlines():
        with _debug_lock:
            _debug_log.append(f"  {line}")
    return ok, out, err

# ---------------------------------------------------------------------------
# Helpers CSV
# ---------------------------------------------------------------------------

CAMPOS = ["user_id", "nombre", "fecha_creacion", "vidrio", "lata", "tetra"]
CATEGORIAS_VALIDAS = {"vidrio", "lata", "tetra"}


def _leer_todos() -> list[dict]:
    """Lee todas las filas del CSV. Devuelve lista de dicts."""
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _escribir_todos(rows: list[dict]):
    """Escribe la lista completa de dicts al CSV (sobreescribe)."""
    with open(DB_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(rows)


def _buscar_usuario(user_id: str) -> dict | None:
    for row in _leer_todos():
        if row["user_id"] == user_id:
            return row
    return None


def _total(row: dict) -> int:
    return int(row.get("vidrio", 0)) + int(row.get("lata", 0)) + int(row.get("tetra", 0))


# ---------------------------------------------------------------------------
# Leaderboard — generación de imagen PNG top 10
# ---------------------------------------------------------------------------

_MEDAL = {0: "🥇", 1: "🥈", 2: "🥉"}
_POS_COLOR = {0: (255, 215, 0), 1: (192, 192, 192), 2: (205, 127, 50)}

def _generar_leaderboard_img():
    """Genera leaderboard.png con el top 10 de usuarios ordenado por total."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[leaderboard] Pillow no instalado (pip install Pillow). Imagen no generada.")
        return

    W, H = 1920, 1080
    BG        = (13,  17,  23)
    SURFACE   = (22,  27,  34)
    ACCENT    = (63, 185, 80)
    FG        = (230, 237, 243)
    FG2       = (125, 133, 144)
    WARN      = (245, 158, 11)

    CAT_CLR = {
        "vidrio": (130, 180, 250),
        "lata":   (250, 130, 130),
        "tetra":  (250, 180, 100),
    }

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    def font(size, bold=False):
        for name in (
            "arialbd.ttf" if bold else "arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                pass
        return ImageFont.load_default()

    F_TITLE  = font(72, bold=True)
    F_HDR    = font(34, bold=True)
    F_ROW    = font(42, bold=False)
    F_ROW_B  = font(42, bold=True)
    F_SUB    = font(28, bold=False)
    F_TS     = font(22, bold=False)

    # Título
    title = "TOP 10  RECICLADORES"
    draw.text((W // 2, 70), title, font=F_TITLE, fill=ACCENT, anchor="mm")

    # Subtítulo / fecha
    ts = datetime.now().strftime("%d/%m/%Y  %H:%M")
    draw.text((W // 2, 145), f"Actualizado: {ts}", font=F_TS, fill=FG2, anchor="mm")

    # Línea separadora
    draw.rectangle([(120, 168), (W - 120, 172)], fill=ACCENT)

    # Columnas: x, label, right-aligned?
    COLS = [
        (130,  "#",        False),
        (260,  "Nombre",   False),
        (900,  "Total",    True),
        (1150, "Vidrio",   True),
        (1450, "Lata",     True),
        (1720, "Tetra",    True),
    ]

    ROW_H   = 75
    HDR_Y   = 205
    START_Y = 255

    # Cabecera
    for x, lbl, right in COLS:
        ax = "rm" if right else "lm"
        draw.text((x, HDR_Y), lbl, font=F_HDR, fill=FG2, anchor=ax)

    # Datos
    with _csv_lock:
        rows = _leer_todos()

    top = sorted(rows, key=lambda r: _total(r), reverse=True)[:10]

    for i, row in enumerate(top):
        y    = START_Y + i * ROW_H
        total = _total(row)

        # Fondo alterno
        if i % 2 == 0:
            draw.rectangle([(115, y - 8), (W - 115, y + ROW_H - 12)], fill=SURFACE)

        medal = _MEDAL.get(i, "")
        pos_clr = _POS_COLOR.get(i, FG)
        nombre  = row.get("nombre", "—")[:16]

        # Posición
        draw.text((130, y + 26), f"{medal or str(i+1)+'.'}", font=F_ROW_B,
                  fill=pos_clr, anchor="lm")
        # Nombre
        draw.text((260, y + 26), nombre, font=(F_ROW_B if i < 3 else F_ROW),
                  fill=(FG if i >= 3 else pos_clr), anchor="lm")
        # Total
        draw.text((900, y + 26), str(total), font=F_ROW_B,
                  fill=ACCENT if i < 3 else FG, anchor="rm")
        # Categorías
        for x, key in [(1150, "vidrio"), (1450, "lata"), (1720, "tetra")]:
            val = int(row.get(key, 0))
            draw.text((x, y + 26), str(val), font=F_ROW,
                      fill=CAT_CLR[key], anchor="rm")

    # Footer
    draw.rectangle([(120, H - 55), (W - 120, H - 51)], fill=SURFACE)
    draw.text((W // 2, H - 30), "Sistema Clasificador de Reciclaje  •  192.168.1.50",
              font=F_TS, fill=FG2, anchor="mm")

    out_path = os.path.join(BASE_DIR, "leaderboard.png")
    img.save(out_path)
    print(f"[leaderboard] Imagen generada: {out_path}  ({len(top)} usuarios)")


@app.route("/leaderboard_img", methods=["GET"])
def leaderboard_img():
    """Sirve el PNG del top 10. Lo regenera si no existe."""
    path = os.path.join(BASE_DIR, "leaderboard.png")
    if not os.path.exists(path):
        _generar_leaderboard_img()
    if not os.path.exists(path):
        return jsonify({"error": "No se pudo generar la imagen (¿Pillow instalado?)"}), 500
    return send_file(path, mimetype="image/png")


# ---------------------------------------------------------------------------
# Endpoints de usuario
# ---------------------------------------------------------------------------

@app.route("/consulta/<user_id>", methods=["GET"])
def consulta(user_id):
    """
    Devuelve datos del usuario en el formato que espera la HMI:
    {"respuesta_render": {"nombre":…, "total":…, "user_id":…, "vidrio":…, "lata":…, "tetra":…}}
    """
    with _csv_lock:
        row = _buscar_usuario(user_id)

    if row is None:
        return jsonify({"error": "usuario no encontrado"}), 404

    return jsonify({
        "status": "ok",
        "respuesta_render": {
            "user_id":  row["user_id"],
            "nombre":   row["nombre"],
            "vidrio":   int(row["vidrio"]),
            "lata":     int(row["lata"]),
            "tetra":    int(row["tetra"]),
            "total":    _total(row),
        }
    }), 200


@app.route("/sumar/<user_id>/<categoria>", methods=["POST"])
def sumar(user_id, categoria):
    """Incrementa en 1 el campo categoria del usuario."""
    if categoria not in CATEGORIAS_VALIDAS:
        return jsonify({"error": f"categoría inválida '{categoria}'"}), 400

    updated_row = None
    with _csv_lock:
        rows = _leer_todos()
        for row in rows:
            if row["user_id"] == user_id:
                row[categoria] = int(row[categoria]) + 1
                _escribir_todos(rows)
                updated_row = row
                break

    if updated_row is None:
        return jsonify({"error": "usuario no encontrado"}), 404

    threading.Thread(target=_generar_leaderboard_img, daemon=True).start()
    return jsonify({
        "ok": True,
        "nuevos_puntos": {
            "vidrio": int(updated_row["vidrio"]),
            "lata":   int(updated_row["lata"]),
            "tetra":  int(updated_row["tetra"]),
            "total":  _total(updated_row),
        }
    }), 200


@app.route("/crear_usuario", methods=["POST"])
def crear_usuario():
    """
    Crea un nuevo usuario.
    Body JSON: {"user_id": "...", "nombre": "..."}
    """
    data = request.get_json(force=True, silent=True) or {}
    user_id = (data.get("user_id") or "").strip()
    nombre  = (data.get("nombre")  or "").strip()

    if not user_id or not nombre:
        return jsonify({"error": "user_id y nombre son requeridos"}), 400

    with _csv_lock:
        if _buscar_usuario(user_id):
            return jsonify({"error": "usuario ya existe"}), 409

        rows = _leer_todos()
        rows.append({
            "user_id":        user_id,
            "nombre":         nombre,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "vidrio":         0,
            "lata":           0,
            "tetra":          0,
        })
        _escribir_todos(rows)

    print(f"[DB] Usuario creado: {user_id} → {nombre}")
    return jsonify({"ok": True}), 201


@app.route("/existe/<user_id>", methods=["GET"])
def existe(user_id):
    """Verifica si el usuario existe. {"existe": true|false}"""
    with _csv_lock:
        found = _buscar_usuario(user_id) is not None
    return jsonify({"existe": found}), 200


# ---------------------------------------------------------------------------
# Endpoints de control del orquestador
# ---------------------------------------------------------------------------

@app.route("/empezarObjeto", methods=["POST"])
def empezar_objeto():
    """
    Lanza la secuencia completa en un hilo daemon.
    Body JSON opcional: {"start": 1, "user_id": "..."}
    """
    from orchestrator import run_full_sequence, is_busy

    if is_busy():
        return jsonify({"status": "ocupado", "mensaje": "Secuencia ya en curso"}), 409

    data    = request.get_json(force=True, silent=True) or {}
    user_id = data.get("user_id")

    t = threading.Thread(target=run_full_sequence, args=(user_id,), daemon=True)
    t.start()

    return jsonify({
        "status": "ok",
        "mensaje": "Secuencia iniciada",
        "user_id": user_id,
        "demo_activo": any(DEMO[k] for k in ("skip_robot", "skip_plc", "skip_vision"))
                       or DEMO["force_object"] is not None,
    }), 200


@app.route("/estado", methods=["GET"])
def estado():
    from orchestrator import is_busy
    return jsonify({"ocupado": is_busy()}), 200


@app.route("/estado_detalle", methods=["GET"])
def estado_detalle():
    """Devuelve estado + paso actual del robot. Usado por el HMI para pasos en tiempo real."""
    from orchestrator import is_busy, get_step
    return jsonify({
        "ocupado": is_busy(),
        "paso":    get_step(),
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok":    True,
        "demo":  DEMO,
        "db":    os.path.exists(DB_PATH),
    }), 200


# ---------------------------------------------------------------------------
# Panel demo
# ---------------------------------------------------------------------------

_DEMO_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Panel Demo — Clasificadora</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Courier New',monospace;background:#0d1117;color:#c9d1d9;min-height:100vh}
    header{background:#161b22;border-bottom:2px solid #e94560;padding:14px 24px;
           display:flex;align-items:center;gap:14px;flex-wrap:wrap}
    header h1{color:#e94560;font-size:1.3rem;flex:1}
    #badge{padding:5px 14px;border-radius:20px;font-weight:bold;font-size:.8rem;letter-spacing:1px}
    .libre{background:#196f3d;color:#abebc6}.ocupado{background:#78281f;color:#f1948a}
    nav{display:flex;gap:0;background:#161b22;border-bottom:1px solid #30363d}
    nav button{background:none;border:none;color:#8b949e;padding:10px 20px;cursor:pointer;
               font-size:.9rem;border-bottom:2px solid transparent}
    nav button.active{color:#e94560;border-bottom-color:#e94560}
    .tab{display:none;max-width:700px;margin:20px auto;padding:0 14px}
    .tab.show{display:block}
    .card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin-bottom:14px}
    .card h2{font-size:.8rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
    label{display:flex;align-items:center;gap:10px;padding:5px 0;cursor:pointer}
    input[type=checkbox]{width:16px;height:16px;accent-color:#e94560}
    select,input[type=text]{background:#0d1117;color:#c9d1d9;border:1px solid #30363d;
            border-radius:6px;padding:7px 10px;font-size:.9rem;width:100%}
    .btn-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}
    button.btn{padding:8px 16px;border:none;border-radius:6px;cursor:pointer;
               font-size:.88rem;font-weight:bold;transition:opacity .15s}
    button.btn:hover{opacity:.82}
    button.btn:disabled{opacity:.35;cursor:not-allowed}
    .blue{background:#1f6feb;color:#fff}.red{background:#e94560;color:#fff}
    .green{background:#196f3d;color:#abebc6}.orange{background:#9e6a03;color:#ffd680}
    .gray{background:#30363d;color:#c9d1d9}
    #log-box{background:#0d1117;border:1px solid #30363d;border-radius:6px;
             padding:10px;height:300px;overflow-y:auto;font-size:.75rem;
             color:#8b949e;line-height:1.7;white-space:pre-wrap;word-break:break-all}
    .ok{color:#3fb950}.warn{color:#d29922}.err{color:#f85149}.info{color:#79c0ff}
    .spin{display:inline-block;animation:spin .8s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
    input[type=text]{margin-top:6px}
  </style>
</head>
<body>
<header>
  <h1>Panel Demo — Clasificadora</h1>
  <span id="badge" class="libre">LIBRE</span>
  <span id="paso-badge" style="padding:5px 12px;border-radius:20px;background:#21262d;
        color:#79c0ff;font-size:.78rem;font-weight:bold;display:none"></span>
</header>
<nav>
  <button class="active" onclick="showTab('secuencia',this)">Secuencia</button>
  <button onclick="showTab('plc',this)">PLC Puerta</button>
  <button onclick="showTab('ur3',this)">UR3 Robot</button>
  <button onclick="showTab('vision',this)">Visión / Rasp</button>
  <button onclick="showTab('logview',this)">Log</button>
</nav>

<!-- ===================== TAB: SECUENCIA ===================== -->
<div id="tab-secuencia" class="tab show">
  <div class="card">
    <h2>Saltar pasos de hardware</h2>
    <label><input type="checkbox" id="skip_robot"> Saltar robot UR3 (movimientos)</label>
    <label><input type="checkbox" id="skip_plc">   Saltar puerta PLC</label>
    <label><input type="checkbox" id="skip_vision">Saltar visión (Rasp Sebas)</label>
  </div>
  <div class="card">
    <h2>Objeto forzado (anula visión)</h2>
    <select id="force_object">
      <option value="">— usar visión real —</option>
      <option value="lata">lata</option>
      <option value="vidrio">vidrio</option>
      <option value="tetra">tetra</option>
      <option value="bg">bg — vuelve a HOME sin depositar</option>
    </select>
  </div>
  <div class="card btn-row">
    <button class="btn blue" onclick="aplicar()">Aplicar config</button>
    <button class="btn red" id="btn-ej" onclick="ejecutar()">&#9654; Ejecutar secuencia</button>
  </div>
</div>

<!-- ===================== TAB: PLC ===================== -->
<div id="tab-plc" class="tab">
  <div class="card">
    <h2>Control individual de puerta</h2>
    <div class="btn-row">
      <button class="btn green" onclick="dbg('POST','/debug/plc_open')">Abrir puerta</button>
      <button class="btn orange" onclick="dbg('POST','/debug/plc_close')">Cerrar puerta</button>
      <button class="btn gray"  onclick="dbg('POST','/debug/plc_stop')">STOP</button>
    </div>
  </div>
  <div class="card">
    <h2>Secuencia completa (abrir → stop → cerrar)</h2>
    <div class="btn-row">
      <button class="btn red" onclick="dbg('POST','/debug/plc_sequence')">Ejecutar secuencia puerta</button>
    </div>
  </div>
</div>

<!-- ===================== TAB: UR3 ===================== -->
<div id="tab-ur3" class="tab">
  <div class="card">
    <h2>Estado y control básico</h2>
    <div class="btn-row">
      <button class="btn blue"  onclick="dbg('GET','/debug/ur3_state')">Ver estado</button>
      <button class="btn green" onclick="dbg('POST','/debug/ur3_home')">Mover a HOME</button>
      <button class="btn red"   onclick="dbg('POST','/debug/ur3_stop')">Stop programa</button>
    </div>
  </div>
  <div class="card">
    <h2>Ejecutar URP</h2>
    <input type="text" id="urp-path" placeholder="/programs/rutObservacion.urp"
           value="/programs/rutObservacion.urp">
    <div class="btn-row" style="margin-top:10px">
      <button class="btn orange" onclick="runUrp()">Cargar y ejecutar URP</button>
    </div>
  </div>
  <div class="card">
    <h2>Programas disponibles</h2>
    <div class="btn-row">
      <button class="btn gray" onclick="setUrp('/programs/rutObservacion.urp')">rutObservacion</button>
      <button class="btn gray" onclick="setUrp('/programs/rutRecolecionLata.urp')">recoleccion Lata</button>
      <button class="btn gray" onclick="setUrp('/programs/rutRecolecionTetra.urp')">recoleccion Tetra</button>
      <button class="btn gray" onclick="setUrp('/programs/rutRecolecionVidrio.urp')">recoleccion Vidrio</button>
      <button class="btn gray" onclick="setUrp('/programs/rutLata.urp')">deposito Lata</button>
      <button class="btn gray" onclick="setUrp('/programs/rutTetra.urp')">deposito Tetra</button>
      <button class="btn gray" onclick="setUrp('/programs/rutVid.urp')">deposito Vidrio</button>
    </div>
  </div>
</div>

<!-- ===================== TAB: VISION ===================== -->
<div id="tab-vision" class="tab">
  <div class="card">
    <h2>Rasp Sebas — salud y ventana</h2>
    <div class="btn-row">
      <button class="btn blue"   onclick="dbg('GET','/debug/rasp_health')">Health check</button>
      <button class="btn green"  onclick="dbg('POST','/debug/rasp_display_on')">Display ON</button>
      <button class="btn orange" onclick="dbg('POST','/debug/rasp_display_close')">Display CLOSE</button>
    </div>
  </div>
  <div class="card">
    <h2>Identificación de objeto</h2>
    <div class="btn-row">
      <button class="btn blue"  onclick="dbg('POST','/debug/vision?duration=5')">Identify headless (5s)</button>
      <button class="btn green" onclick="dbg('POST','/debug/vision_window?duration=5')">Identify con ventana (5s)</button>
    </div>
  </div>
</div>

<!-- ===================== TAB: LOG ===================== -->
<div id="tab-logview" class="tab">
  <div class="card">
    <h2>Log del servidor <span id="log-spin" style="display:none" class="spin">&#8635;</span></h2>
    <div id="log-box"></div>
    <div class="btn-row" style="margin-top:10px">
      <button class="btn gray" onclick="document.getElementById('log-box').innerHTML=''">Limpiar pantalla</button>
    </div>
  </div>
</div>

<script>
// ---- Tabs ----
function showTab(name, btn) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('show'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('show');
  btn.classList.add('active');
  if (name === 'logview') pollLog();
}

// ---- Estado badge ----
const badgeEl = document.getElementById('badge');
const btnEj   = document.getElementById('btn-ej');

const pasoBadge = document.getElementById('paso-badge');
const PASO_LABEL = {
  'HOME':'🏠 HOME', 'PUERTA':'🚪 Puerta', 'OBSERVACION':'👁 Observando',
  'CLASIFICANDO':'🔍 Clasificando', 'DEPOSITANDO':'📦 Depositando',
  'REGRESANDO':'↩ Regresando', 'LISTO':'✓ Listo', '':''
};

async function cargarEstado() {
  try {
    const r  = await fetch('/demo/estado');
    const rd = await fetch('/estado_detalle');
    const d  = await r.json();
    const dd = await rd.json();

    badgeEl.textContent = d.ocupado ? 'OCUPADO' : 'LIBRE';
    badgeEl.className   = 'badge ' + (d.ocupado ? 'ocupado' : 'libre');
    btnEj.disabled      = d.ocupado;

    const paso = dd.paso || '';
    if (paso && paso !== 'LISTO') {
      pasoBadge.textContent = PASO_LABEL[paso] || paso;
      pasoBadge.style.display = 'inline-block';
    } else {
      pasoBadge.style.display = 'none';
    }

    const c = d.config;
    document.getElementById('skip_robot') .checked = c.skip_robot;
    document.getElementById('skip_plc')   .checked = c.skip_plc;
    document.getElementById('skip_vision').checked = c.skip_vision;
    document.getElementById('force_object').value  = c.force_object || '';
  } catch(e) {}
}
setInterval(cargarEstado, 1000);
cargarEstado();

// ---- Config / Secuencia ----
async function aplicar() {
  const cfg = {
    skip_robot:   document.getElementById('skip_robot').checked,
    skip_plc:     document.getElementById('skip_plc').checked,
    skip_vision:  document.getElementById('skip_vision').checked,
    force_object: document.getElementById('force_object').value || null
  };
  await fetch('/demo/config', {method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify(cfg)});
  appendLog('Config aplicada: ' + JSON.stringify(cfg), 'ok');
}

async function ejecutar() {
  await aplicar();
  try {
    const r = await fetch('/empezarObjeto', {method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify({start:1})});
    const d = await r.json();
    appendLog(r.ok ? 'Secuencia iniciada' : 'Error: ' + (d.mensaje||d.error),
              r.ok ? 'ok' : 'err');
  } catch(e) { appendLog('Error de red: '+e,'err'); }
}

// ---- Debug genérico ----
async function dbg(method, url) {
  appendLog((method==='GET'?'GET ':'POST ') + url + ' ...', 'info');
  const spin = document.getElementById('log-spin');
  if (spin) spin.style.display='inline-block';
  try {
    const r = await fetch(url, {method});
    const d = await r.json();
    const ok = d.ok !== false && r.ok;
    if (d.log) d.log.split('\n').forEach(l => { if(l.trim()) appendLog('  '+l,''); });
    if (d.rasp) appendLog(JSON.stringify(d.rasp, null, 2), 'info');
    if (d.result) appendLog(JSON.stringify(d.result), 'info');
    appendLog(ok ? 'OK' : 'ERROR: '+(d.error||r.status), ok?'ok':'err');
  } catch(e) { appendLog('Error de red: '+e,'err'); }
  finally { if (spin) spin.style.display='none'; }
}

// ---- URP ----
function setUrp(path) { document.getElementById('urp-path').value = path; }
async function runUrp() {
  const prog = document.getElementById('urp-path').value.trim();
  if (!prog) { appendLog('Escribe la ruta del URP primero','warn'); return; }
  appendLog('POST /debug/ur3_urp  program='+prog,'info');
  try {
    const r = await fetch('/debug/ur3_urp',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify({program:prog})});
    const d = await r.json();
    if (d.log) d.log.split('\n').forEach(l=>{ if(l.trim()) appendLog('  '+l,''); });
    appendLog(r.ok?'OK':'ERROR: '+(d.error||r.status), r.ok?'ok':'err');
  } catch(e){ appendLog('Error: '+e,'err'); }
}

// ---- Log ----
const logBox = document.getElementById('log-box');
let lastLogLen = 0;

function appendLog(msg, cls='') {
  const line = document.createElement('span');
  line.className = cls;
  line.textContent = msg + '\n';
  logBox.appendChild(line);
  logBox.scrollTop = logBox.scrollHeight;
}

async function pollLog() {
  try {
    const r = await fetch('/debug/log?n=200');
    const d = await r.json();
    if (d.lines.length !== lastLogLen) {
      logBox.innerHTML = '';
      d.lines.forEach(l => {
        const s = document.createElement('span');
        s.className = l.includes('ERROR')||l.includes('ERR') ? 'err'
                    : l.includes('OK') ? 'ok'
                    : l.includes('WARN') ? 'warn' : '';
        s.textContent = l + '\n';
        logBox.appendChild(s);
      });
      lastLogLen = d.lines.length;
      logBox.scrollTop = logBox.scrollHeight;
    }
  } catch(e) {}
  setTimeout(pollLog, 1500);
}
</script>
</body>
</html>"""


@app.route("/demo", methods=["GET"])
def demo_panel():
    return Response(_DEMO_HTML, mimetype="text/html")


@app.route("/demo/config", methods=["POST"])
def demo_config():
    """Actualiza config.DEMO en runtime sin reiniciar el servidor."""
    data = request.get_json(force=True, silent=True) or {}

    allowed_bools = ("skip_robot", "skip_plc", "skip_vision")
    for key in allowed_bools:
        if key in data:
            DEMO[key] = bool(data[key])

    if "force_object" in data:
        val = data["force_object"]
        DEMO["force_object"] = val if val in ("lata", "vidrio", "tetra", "bg") else None

    print(f"[DEMO] Config actualizada: {DEMO}")
    return jsonify({"ok": True, "demo": DEMO}), 200


@app.route("/demo/estado", methods=["GET"])
def demo_estado():
    """Estado combinado para el panel JS."""
    from orchestrator import is_busy
    return jsonify({
        "ocupado": is_busy(),
        "config":  dict(DEMO),
    }), 200


# ---------------------------------------------------------------------------
# Debug endpoints — prueba individual de cada subsistema
# ---------------------------------------------------------------------------

@app.route("/debug/log", methods=["GET"])
def debug_log():
    """Devuelve las últimas líneas del log de debug."""
    n = int(request.args.get("n", 100))
    with _debug_lock:
        lines = list(_debug_log)[-n:]
    return jsonify({"lines": lines}), 200


@app.route("/debug/plc_open", methods=["POST"])
def debug_plc_open():
    from plc_door import door_open_only
    ok, out, err = _run_capture(door_open_only, label="[PLC] Abrir")
    return jsonify({"ok": ok, "log": out, "error": err}), (200 if ok else 500)


@app.route("/debug/plc_close", methods=["POST"])
def debug_plc_close():
    from plc_door import door_close_only
    ok, out, err = _run_capture(door_close_only, label="[PLC] Cerrar")
    return jsonify({"ok": ok, "log": out, "error": err}), (200 if ok else 500)


@app.route("/debug/plc_stop", methods=["POST"])
def debug_plc_stop():
    from plc_door import door_stop
    ok, out, err = _run_capture(door_stop, label="[PLC] Stop")
    return jsonify({"ok": ok, "log": out, "error": err}), (200 if ok else 500)


@app.route("/debug/plc_sequence", methods=["POST"])
def debug_plc_sequence():
    from plc_door import door_open_stop_close
    ok, out, err = _run_capture(door_open_stop_close, label="[PLC] Secuencia completa")
    return jsonify({"ok": ok, "log": out, "error": err}), (200 if ok else 500)


@app.route("/debug/ur3_home", methods=["POST"])
def debug_ur3_home():
    from robot_control import move_home
    ok, out, err = _run_capture(move_home, label="[UR3] HOME")
    return jsonify({"ok": ok, "log": out, "error": err}), (200 if ok else 500)


@app.route("/debug/ur3_urp", methods=["POST"])
def debug_ur3_urp():
    """Body JSON: {"program": "/programs/rutObservacion.urp"}"""
    data = request.get_json(force=True, silent=True) or {}
    prog = data.get("program", "").strip()
    if not prog:
        return jsonify({"error": "Falta campo 'program'"}), 400
    from robot_control import run_urp_sequence
    ok, out, err = _run_capture(run_urp_sequence, [prog], label=f"[UR3] URP {prog}")
    return jsonify({"ok": ok, "log": out, "error": err}), (200 if ok else 500)


@app.route("/debug/ur3_stop", methods=["POST"])
def debug_ur3_stop():
    """Detiene el programa activo en el UR3 via Dashboard."""
    from robot_control import Dashboard
    from config import UR3_IP
    ok, out, err = True, "", ""
    buf = io.StringIO()
    try:
        db = Dashboard(UR3_IP)
        resp = db.cmd("stop")
        db.close()
        print(f"[UR3] stop → {resp.strip()}", file=buf)
    except Exception as e:
        ok  = False
        err = str(e)
        print(f"ERROR: {e}", file=buf)
    out = buf.getvalue()
    _log(f"[UR3] Stop {'OK' if ok else 'ERROR: ' + err}")
    return jsonify({"ok": ok, "log": out, "error": err}), (200 if ok else 500)


@app.route("/debug/ur3_state", methods=["GET"])
def debug_ur3_state():
    """Devuelve el estado actual del Dashboard UR3."""
    from robot_control import Dashboard
    from config import UR3_IP
    try:
        db    = Dashboard(UR3_IP)
        state = db.cmd("programState").strip()
        mode  = db.cmd("robotmode").strip()
        db.close()
        _log(f"[UR3] state={state}  mode={mode}")
        return jsonify({"ok": True, "programState": state, "robotmode": mode}), 200
    except Exception as e:
        _log(f"[UR3] state ERROR: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/debug/vision", methods=["POST"])
def debug_vision():
    """Llama a /identify en la Rasp Sebas y muestra el resultado."""
    import requests as req
    from config import RASP_SEBAS_URL
    duration = int(request.args.get("duration", 5))
    try:
        r = req.get(f"{RASP_SEBAS_URL}/identify?duration={duration}", timeout=duration + 10)
        data = r.json()
        _log(f"[VISION] → {data}")
        return jsonify({"ok": True, "result": data}), 200
    except Exception as e:
        _log(f"[VISION] ERROR: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/debug/vision_window", methods=["POST"])
def debug_vision_window():
    """Llama a /identify_window en la Rasp Sebas (muestra cámara en la TV)."""
    import requests as req
    from config import RASP_SEBAS_URL
    duration = int(request.args.get("duration", 5))
    try:
        r = req.get(f"{RASP_SEBAS_URL}/identify_window?duration={duration}", timeout=duration + 10)
        data = r.json()
        _log(f"[VISION WINDOW] → {data}")
        return jsonify({"ok": True, "result": data}), 200
    except Exception as e:
        _log(f"[VISION WINDOW] ERROR: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/debug/rasp_health", methods=["GET"])
def debug_rasp_health():
    import requests as req
    from config import RASP_SEBAS_URL
    try:
        r = req.get(f"{RASP_SEBAS_URL}/health", timeout=5)
        data = r.json()
        _log(f"[RASP] health → {data}")
        return jsonify({"ok": True, "rasp": data}), 200
    except Exception as e:
        _log(f"[RASP] health ERROR: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/debug/rasp_display_on", methods=["POST"])
def debug_rasp_display_on():
    import requests as req
    from config import RASP_SEBAS_URL
    try:
        r = req.get(f"{RASP_SEBAS_URL}/display_on", timeout=5)
        _log(f"[RASP] display_on → {r.status_code}")
        return jsonify({"ok": r.ok}), 200
    except Exception as e:
        _log(f"[RASP] display_on ERROR: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/debug/rasp_display_close", methods=["POST"])
def debug_rasp_display_close():
    import requests as req
    from config import RASP_SEBAS_URL
    try:
        r = req.get(f"{RASP_SEBAS_URL}/display_close", timeout=5)
        _log(f"[RASP] display_close → {r.status_code}")
        return jsonify({"ok": r.ok}), 200
    except Exception as e:
        _log(f"[RASP] display_close ERROR: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _generar_leaderboard_img()
    print(f"[server] Iniciando en http://{config.PC_IP}:{PC_PORT}")
    print(f"[server] Panel demo: http://{config.PC_IP}:{PC_PORT}/demo")
    print(f"[server] Health:     http://{config.PC_IP}:{PC_PORT}/health")
    app.run(
        host=PC_HOST,
        port=PC_PORT,
        debug=False,
        threaded=True,
        use_reloader=False,
    )
