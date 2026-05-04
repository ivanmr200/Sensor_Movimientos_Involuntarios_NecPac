import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="InvoluntTrack",
    page_icon="./Plantilla_Latex_NecPac/img/logo_.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
section[data-testid="stAppViewContainer"] { background: #f8f9fb; }
.stApp > header { display: none; }
.main .block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1100px !important; }
.stButton > button {
    background: #2563eb !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-size: .85rem !important; font-weight: 500 !important;
    padding: .5rem 1.2rem !important;
}
.stButton > button:hover { background: #1d4ed8 !important; }
div[data-testid="stSelectbox"] label { font-size: .9rem; font-weight: 500; color: #374151; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 4, 1])

with col2:
  c1, c2 = st.columns([6, 2])
  
  with c1:
    st.markdown("# InvoluntTrack")
    st.markdown("## Detector de movimientos involuntarios")
    st.caption("Sigue la línea con el cursor. Detecta desviaciones y movimientos involuntarios (espasmos).")

  with c2:
      st.image("./Plantilla_Latex_NecPac/img/involunttrack_logo.png", width=400)

  
  st.divider()

# ── LEVELS ────────────────────────────────────────────────────────────────────
LEVELS = {
    "🟢 Fácil":   {"tolerance": 10, "path_type": "straight", "color": "#22c55e"},
    "🟡 Medio":   {"tolerance": 10, "path_type": "sine",     "color": "#f59e0b"},
    "🟠 Difícil": {"tolerance": 10, "path_type": "zigzag",   "color": "#f97316"},
    "🔴 Experto": {"tolerance": 10, "path_type": "spiral",   "color": "#ef4444"},
}


with col2:
    level_key = st.selectbox("Nivel de dificultad", list(LEVELS.keys()))


    level = LEVELS[level_key]
 
       # ajustar tolerancia manualmente
    custom_tol = st.slider(
        "Ajustar tolerancia (px)",
        min_value=1,
        max_value=30,
        value=level["tolerance"]
    )

    W, H = 800, 280
    TOL = custom_tol
    PT = level["path_type"]
    PC = level["color"]

    st.caption(f"Tolerancia: ±{TOL}px")

# ─────────────────────────────
# CANVAS
# ─────────────────────────────
canvas_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ margin:0; font-family:system-ui; background:#f8f9fb;}}

#wrap {{
  position:relative;
  width:{W}px;
  border:1px solid #e5e7eb;
  border-radius:10px;
  overflow:auto;
  background:white;
}}

canvas {{ cursor:crosshair; display:block; }}

#hud {{
  position:absolute;
  top:10px; left:12px;
  font-size:12px;
  color:#6b7280;
}}

#statuslbl {{
  position:absolute;
  top:10px; right:12px;
  font-size:12px;
  color:#9ca3af;
}}

#actions {{
  width:{W}px;
  margin-top:10px;
  display:flex;
  gap:8px;
  justify-content:flex-start;
}}

#actions.hidden {{
  display:none;
}}

#resultBox {{
  width:{W}px;
  margin-top:10px;
  font-size:14px;
  color:#111827;
  font-weight:500;
}}

button {{
  background:#2563eb;
  color:white;
  border:none;
  padding:8px 14px;
  border-radius:8px;
  cursor:pointer;
}}
button:hover {{ background:#1d4ed8; }}
</style>
</head>

<body>

<div id="wrap">

<canvas id="c" width="{W}" height="{H}"></canvas>

<div id="hud">
Salidas: <b id="scount">0</b>
</div>

<div id="statuslbl">Haz click para empezar</div>

</div>

<div id="actions" class="hidden">
  <button onclick="showResults()">Ver resultados</button>
  <button onclick="saveImage()">Guardar imagen</button>
  <button onclick="resetCanvas()">Nuevo análisis</button>
</div>

<div id="resultBox"></div>

<script>

const C=document.getElementById('c'), ctx=C.getContext('2d');
const W={W}, H={H}, TOL={TOL}, PT="{PT}", PC="{PC}";

function buildPath(){{
  const pts=[], N=500, mg=50;
  for(let i=0;i<=N;i++){{
    const t=i/N;
    const x=mg+t*(W-mg*2);
    let y=H/2;

    if(PT==='sine') y+=Math.sin(t*Math.PI*5)*70;

    if(PT==='zigzag'){{
      const s=Math.floor(t*10);
      const l=(t*10)%1;
      const a=[.15,.85,.15,.85,.15,.85,.15,.85,.15,.85];
      y=H*(a[s%10]+(a[(s+1)%10]-a[s%10])*l);
    }}

    if(PT==='spiral')
      y+=Math.sin(t*Math.PI*7)*(80*(1-t));

    pts.push({{x,y}});
  }}
  return pts;
}}

const PATH=buildPath();

let state='idle';
let traced=[];
let exits=[];
let scount=0;
let outside=false;
let prevP=null;
let prevT=null;
let lvx=0;
let lvy=0;

function ndist(px,py){{
  let m=1e9;
  for(const p of PATH){{
    const d=Math.hypot(px-p.x,py-p.y);
    if(d<m) m=d;
  }}
  return m;
}}

function draw(){{
  ctx.clearRect(0,0,W,H);

  // tolerancia visual
  ctx.beginPath();
  PATH.forEach((p,i)=>{{
    if(i===0) ctx.moveTo(p.x,p.y);
    else ctx.lineTo(p.x,p.y);
  }});
  ctx.strokeStyle="rgba(37, 99, 235, 0.15)";
  ctx.lineWidth=TOL*2;
  ctx.lineCap="round";
  ctx.lineJoin="round";
  ctx.stroke();

  // camino principal
  ctx.beginPath();
  PATH.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
  ctx.strokeStyle=PC;
  ctx.lineWidth=3;
  ctx.stroke();

  const start=PATH[0];
  const end=PATH[PATH.length-1];

  ctx.beginPath();
  ctx.arc(start.x,start.y,7,0,Math.PI*2);
  ctx.fillStyle="#22c55e";
  ctx.fill();

  ctx.fillText("INICIO", start.x+10,start.y-15);

  ctx.beginPath();
  ctx.arc(end.x,end.y,7,0,Math.PI*2);
  ctx.fillStyle="#ef4444";
  ctx.fill();

  ctx.fillText("FIN", end.x-25,end.y-15);

  // trazo usuario
  ctx.beginPath();
  traced.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
  ctx.strokeStyle="#2563eb";
  ctx.lineWidth=2;
  ctx.stroke();

  // puntos de salida
  for(const e of exits){{
    ctx.beginPath();
    ctx.arc(e.x,e.y,6,0,Math.PI*2);
    ctx.fillStyle="#ef4444";
    ctx.fill();
  }}
}}

function gp(e){{
  const r=C.getBoundingClientRect();
  return {{x:e.clientX-r.left,y:e.clientY-r.top,t:e.timeStamp}};
}}

function startTrace(p){{
  state='tracking';
  traced=[p];
  exits=[];
  scount=0;
  outside=false;
  prevP=p;
  prevT=p.t;
  lvx=0;
  lvy=0;

  document.getElementById('scount').textContent=0;
  document.getElementById('actions').classList.add('hidden');
  document.getElementById('resultBox').textContent="";
}}

function updateTrace(p){{
  const dt=Math.max((p.t-(prevT||p.t))/1000,.001);
  const vx=(p.x-(prevP?.x||p.x))/dt;
  const vy=(p.y-(prevP?.y||p.y))/dt;

  traced.push({{x:p.x,y:p.y,t:p.t,vx,vy}});

  const d=ndist(p.x,p.y);
  const out=d>TOL;

  if(out && !outside){{
    scount++;
    document.getElementById('scount').textContent=scount;
    exits.push({{x:p.x,y:p.y}});
  }}

  outside=out;
  prevP=p;
  prevT=p.t;
  lvx=vx;
  lvy=vy;

  const end=PATH[PATH.length-1];
  if(Math.hypot(p.x-end.x,p.y-end.y)<20) finishTrace();

  draw();
}}

function finishTrace(){{
  if(state!=='tracking') return;
  state='done';
  document.getElementById('actions').classList.remove('hidden');
  draw();
}}

function resetCanvas(){{
  state='idle';
  traced=[];
  exits=[];
  scount=0;
  outside=false;
  prevP=null;
  prevT=null;
  lvx=0;
  lvy=0;

  document.getElementById('scount').textContent=0;
  document.getElementById('resultBox').innerHTML="";
  document.getElementById('actions').classList.add('hidden');

  draw();
}}

function saveImage(){{
  const img=C.toDataURL("image/png");
  const a=document.createElement('a');
  a.href=img;
  a.download="MovInvoluntario.png";
  a.click();
}}

function showResults(){{
  const box=document.getElementById('resultBox');

  let msg="";
  if(scount===0){{
    msg="No hay movimientos involuntarios";
  }}else if(scount<=10){{
    msg="Posible afectación";
  }}else{{
    msg="Movimientos involuntarios considerables";
  }}

  box.innerHTML=`
    <div>
      <b style="font-size:20px;">Resultado del análisis</b><br>
      Espasmos totales: <span style="color:#ef4444">${{scount}}</span><br><br>
      <b>Clasificación:</b> ${{msg}}
    </div>
  `;
}}

C.addEventListener('mousedown',e=>startTrace(gp(e)));
C.addEventListener('mousemove',e=>{{ if(state==='tracking') updateTrace(gp(e)); }});
C.addEventListener('mouseup',()=>finishTrace());

draw();

</script>
</body>
</html>
"""
with col2:
  components.html(canvas_html, height=450, scrolling=False)
  