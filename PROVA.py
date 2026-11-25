"""
Muestra los partidos de API-Sports en una página web local.

Uso:
    pip install requests
    python partidos_web.py
    -> abre http://localhost:8000 en el navegador
"""
import html
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

# ---------------- CONFIGURACIÓN ----------------
API_KEY = "32401a480690febb88061d9130b369a7"
URL = "https://v3.football.api-sports.io/fixtures"
FECHA = "2026-11-25"
PUERTO = 8000
CACHE_SEGUNDOS = 120  # evita gastar peticiones de la API al recargar la página
# -----------------------------------------------

_cache = {"t": 0, "datos": None}

VIVO = {"1H", "2H", "HT", "ET", "BT", "P", "LIVE", "INT"}
FINAL = {"FT", "AET", "PEN"}
PENDIENTE = {"NS", "TBD"}

ETIQUETAS = {
    "FT": "Finalizado", "AET": "Finalizado (prórroga)", "PEN": "Finalizado (penaltis)",
    "NS": "Pendiente", "TBD": "Por confirmar", "HT": "Descanso",
    "1H": "1ª parte", "2H": "2ª parte", "ET": "Prórroga", "BT": "Descanso prórroga",
    "P": "Penaltis", "LIVE": "En juego", "INT": "Interrumpido",
    "PST": "Aplazado", "CANC": "Cancelado", "ABD": "Abandonado",
    "SUSP": "Suspendido", "AWD": "Adjudicado", "WO": "Walkover",
}


def obtener_partidos():
    """Pide los partidos a la API (con caché corta para no gastar cuota)."""
    ahora = time.time()
    if _cache["datos"] is None or ahora - _cache["t"] > CACHE_SEGUNDOS:
        r = requests.get(
            URL,
            headers={"x-apisports-key": API_KEY},
            params={"date": FECHA},
            timeout=15,
        )
        r.raise_for_status()
        datos = r.json()
        if datos.get("errors"):
            raise RuntimeError(f"La API devolvió errores: {datos['errors']}")
        _cache["datos"] = datos["response"]
        _cache["t"] = ahora
    return _cache["datos"]


def categoria(short):
    if short in VIVO:
        return "vivo"
    if short in FINAL:
        return "final"
    if short in PENDIENTE:
        return "pendiente"
    return "otro"


def tarjeta_partido(p):
    esc = html.escape
    fx = p["fixture"]
    short = fx["status"]["short"]
    cat = categoria(short)
    local = p["teams"]["home"]
    visita = p["teams"]["away"]
    gl, gv = p["goals"]["home"], p["goals"]["away"]
    hora = time.strftime("%H:%M", time.localtime(fx["timestamp"]))

    if gl is None or gv is None:
        centro = f'<span class="hora">{hora}</span>'
    else:
        centro = f'<span class="goles">{gl} - {gv}</span>'

    estado = ETIQUETAS.get(short, fx["status"]["long"])
    if cat == "vivo" and fx["status"]["elapsed"] is not None:
        estado = f'<span class="punto"></span>{fx["status"]["elapsed"]}\' · {estado}'
    else:
        estado = esc(estado)

    texto = f'{local["name"]} {visita["name"]} {p["league"]["name"]} {p["league"]["country"]}'.lower()

    return f"""
    <div class="partido" data-estado="{cat}" data-texto="{esc(texto, quote=True)}">
      <div class="equipo local">
        <span>{esc(local["name"])}</span>
        <img src="{esc(local["logo"])}" alt="" loading="lazy">
      </div>
      <div class="centro">
        {centro}
        <span class="estado {cat}">{estado}</span>
      </div>
      <div class="equipo">
        <img src="{esc(visita["logo"])}" alt="" loading="lazy">
        <span>{esc(visita["name"])}</span>
      </div>
    </div>"""


CSS = """
:root{--bg:#0f172a;--card:#1e293b;--card2:#273449;--txt:#e2e8f0;--sub:#94a3b8;
--acc:#22c55e;--vivo:#ef4444;--azul:#38bdf8}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--txt)}
header{background:linear-gradient(135deg,#1d4ed8,#0f766e);padding:28px 20px;text-align:center}
header h1{margin:0 0 6px;font-size:1.9rem}
header p{margin:0;opacity:.85}
.resumen{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:18px}
.chip{background:rgba(255,255,255,.15);padding:8px 16px;border-radius:999px;font-size:.9rem}
.chip b{font-size:1.1rem}
main{max-width:900px;margin:0 auto;padding:20px}
.barra{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;position:sticky;top:0;
background:var(--bg);padding:10px 0;z-index:5}
.barra input{flex:1;min-width:200px;padding:10px 14px;border-radius:10px;border:1px solid #334155;
background:var(--card);color:var(--txt);font-size:1rem}
.filtro{padding:10px 14px;border-radius:10px;border:1px solid #334155;background:var(--card);
color:var(--txt);cursor:pointer;font-size:.9rem}
.filtro.activo{background:var(--azul);color:#0f172a;border-color:var(--azul);font-weight:700}
.liga{background:var(--card);border-radius:14px;margin-bottom:18px;overflow:hidden}
.liga h2{margin:0;padding:12px 16px;background:var(--card2);font-size:1rem;display:flex;
align-items:center;gap:10px}
.liga h2 img{width:24px;height:24px;object-fit:contain}
.liga h2 small{color:var(--sub);font-weight:400;margin-left:auto}
.partido{display:grid;grid-template-columns:1fr 120px 1fr;align-items:center;gap:10px;
padding:12px 16px;border-top:1px solid #334155}
.partido:hover{background:#243047}
.equipo{display:flex;align-items:center;gap:10px;font-weight:600}
.equipo.local{justify-content:flex-end;text-align:right}
.equipo img{width:30px;height:30px;object-fit:contain;flex-shrink:0}
.centro{display:flex;flex-direction:column;align-items:center;gap:4px}
.goles{font-size:1.4rem;font-weight:800}
.hora{font-size:1.2rem;font-weight:700;color:var(--azul)}
.estado{font-size:.72rem;color:var(--sub);text-align:center}
.estado.vivo{color:var(--vivo);font-weight:700}
.estado.final{color:var(--acc)}
.punto{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--vivo);
margin-right:5px;animation:pulso 1.2s infinite}
@keyframes pulso{50%{opacity:.25}}
.vacio,.error{text-align:center;padding:40px;color:var(--sub)}
.error{color:#fca5a5}
@media(max-width:600px){.partido{grid-template-columns:1fr 80px 1fr;padding:10px}
.equipo{font-size:.85rem}.equipo img{width:24px;height:24px}}
"""

JS = """
let filtro='todos';
const buscar=document.getElementById('buscar');
function aplicar(){
  const q=buscar.value.toLowerCase().trim();
  document.querySelectorAll('.liga').forEach(l=>{
    let n=0;
    l.querySelectorAll('.partido').forEach(p=>{
      const ok=(filtro==='todos'||p.dataset.estado===filtro)&&p.dataset.texto.includes(q);
      p.style.display=ok?'':'none';
      if(ok)n++;
    });
    l.style.display=n?'':'none';
  });
}
document.querySelectorAll('.filtro').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.filtro').forEach(x=>x.classList.remove('activo'));
  b.classList.add('activo');filtro=b.dataset.f;aplicar();
}));
buscar.addEventListener('input',aplicar);
"""


def pagina(cuerpo, resumen=""):
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Partidos {FECHA}</title><style>{CSS}</style></head><body>
<header><h1>⚽ Partidos del {FECHA}</h1><p>Datos de API-Sports</p>{resumen}</header>
<main>{cuerpo}</main></body></html>"""


def construir_pagina(partidos):
    # Agrupar por liga
    ligas = {}
    for p in partidos:
        l = p["league"]
        ligas.setdefault((l["id"], l["name"], l["country"], l["logo"]), []).append(p)

    cuentas = {"vivo": 0, "final": 0, "pendiente": 0, "otro": 0}
    for p in partidos:
        cuentas[categoria(p["fixture"]["status"]["short"])] += 1

    # Ligas con partidos en vivo primero, luego por país y nombre
    def orden(item):
        (_, nombre, pais, _), lista = item
        hay_vivo = any(categoria(x["fixture"]["status"]["short"]) == "vivo" for x in lista)
        return (not hay_vivo, pais, nombre)

    bloques = []
    for (lid, nombre, pais, logo), lista in sorted(ligas.items(), key=orden):
        lista.sort(key=lambda x: x["fixture"]["timestamp"])
        logo_html = f'<img src="{html.escape(logo)}" alt="">' if logo else ""
        bloques.append(
            f'<section class="liga"><h2>{logo_html}{html.escape(nombre)}'
            f'<small>{html.escape(pais)}</small></h2>'
            + "".join(tarjeta_partido(p) for p in lista)
            + "</section>"
        )

    resumen = (
        '<div class="resumen">'
        f'<div class="chip"><b>{len(partidos)}</b> partidos</div>'
        f'<div class="chip"><b>{cuentas["vivo"]}</b> en vivo</div>'
        f'<div class="chip"><b>{cuentas["final"]}</b> finalizados</div>'
        f'<div class="chip"><b>{cuentas["pendiente"]}</b> pendientes</div>'
        "</div>"
    )
    barra = (
        '<div class="barra">'
        '<input id="buscar" type="search" placeholder="Buscar equipo, liga o país...">'
        '<button class="filtro activo" data-f="todos">Todos</button>'
        '<button class="filtro" data-f="vivo">En vivo</button>'
        '<button class="filtro" data-f="final">Finalizados</button>'
        '<button class="filtro" data-f="pendiente">Pendientes</button>'
        '<button class="filtro" data-f="otro">Otros</button>'
        "</div>"
    )
    if not bloques:
        bloques = ['<div class="vacio">No hay partidos para esta fecha.</div>']
    return pagina(barra + "".join(bloques) + f"<script>{JS}</script>", resumen)


def pagina_error(e):
    msg = html.escape(str(e))
    return pagina(
        f'<div class="error"><h2>No se pudieron cargar los partidos</h2><p>{msg}</p>'
        "<p>Revisa que API_KEY tenga tu clave real y que tengas conexión a internet.</p></div>"
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        try:
            contenido = construir_pagina(obtener_partidos())
        except Exception as e:
            contenido = pagina_error(e)
        datos = contenido.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *args):
        pass  # silencia el log en la terminal


if __name__ == "__main__":
    servidor = HTTPServer(("127.0.0.1", PUERTO), Handler)
    direccion = f"http://localhost:{PUERTO}"
    print(f"Servidor en marcha: {direccion}  (Ctrl+C para parar)")
    try:
        webbrowser.open(direccion)
    except Exception:
        pass
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")