from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import json
from fastapi.responses import JSONResponse
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("BASE_DIR =", BASE_DIR)
print("STATIC =", os.path.join(BASE_DIR, "static"))
print("EXISTE =", os.path.exists(os.path.join(BASE_DIR, "static")))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/acta", response_class=HTMLResponse)
async def acta(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="acta.html",
        context={"mensaje": None}
    )
@app.post("/guardar_acta")
async def guardar_acta(request: Request):

    form = await request.form()

    datos = dict(form)
    puntos_af = float(datos.get("puntos_af", 0))
    puntos_ec = float(datos.get("puntos_ec", 0))

    avisos_af = int(datos.get("avisos_af", 0))
    avisos_ec = int(datos.get("avisos_ec", 0))

    leves_af = int(datos.get("leves_af", 0))
    leves_ec = int(datos.get("leves_ec", 0))

    graves_af = int(datos.get("graves_af", 0))
    graves_ec = int(datos.get("graves_ec", 0))

    penalizacion_af = leves_af + (avisos_af // 2)
    penalizacion_ec = leves_ec + (avisos_ec // 2)

    final_af = puntos_af - penalizacion_af
    final_ec = puntos_ec - penalizacion_ec

    if graves_af > 0:
        ganador = datos["equipo_ec"]

    elif graves_ec > 0:
        ganador = datos["equipo_af"]

    elif final_af > final_ec:
        ganador = datos["equipo_af"]

    elif final_ec > final_af:
        ganador = datos["equipo_ec"]

    else:
        ganador = "Empate"

    nueva_acta = {

        **datos,

        "penalizacion_af": penalizacion_af,
        "penalizacion_ec": penalizacion_ec,

        "final_af": final_af,
        "final_ec": final_ec,

        "ganador": ganador

    }

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "debates.json"),
            "r",
            encoding="utf-8"
        ) as f:

            debates = json.load(f)

    except:
        debates = []

    debates.append(nueva_acta)

    with open(
        os.path.join(BASE_DIR, "datos", "debates.json"),
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            debates,
            f,
            ensure_ascii=False,
            indent=4
        )
    return templates.TemplateResponse(
        request=request,
        name="acta.html",
        context={
            "mensaje": "✅ Acta guardada correctamente"
            }
)


@app.get("/clasificacion", response_class=HTMLResponse)
async def clasificacion(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="clasificacion.html",
        context={}
    )
@app.get("/clasificacion/datos")
async def clasificacion_datos():

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "debates.json"),
            "r",
            encoding="utf-8"
        ) as f:
            debates = json.load(f)

    except:
        debates = []

    clasificacion = {}

    
    grupos = {}

    for acta in debates:

        clave = (
            acta.get("ronda"),
            acta.get("sala")
        )

        if clave not in grupos:
            grupos[clave] = []

        grupos[clave].append(acta)

    
    for grupo in grupos.values():

        if not grupo:
            continue

        primera = grupo[0]

        equipo_af = primera["equipo_af"]
        equipo_ec = primera["equipo_ec"]

        for equipo in [equipo_af, equipo_ec]:

            if equipo not in clasificacion:

                clasificacion[equipo] = {
                    "colegio": equipo,
                    "pj": 0,
                    "pg": 0,
                    "pp": 0,
                    "pts": 0,
                    "faltas": 0
                }

        votos_af = 0
        votos_ec = 0

        puntos_af = 0
        puntos_ec = 0

        for acta in grupo:

            puntos_af += float(acta.get("final_af", 0))
            puntos_ec += float(acta.get("final_ec", 0))

            ganador = acta.get("ganador")

            if ganador == equipo_af:
                votos_af += 1

            elif ganador == equipo_ec:
                votos_ec += 1

        clasificacion[equipo_af]["pj"] += 1
        clasificacion[equipo_ec]["pj"] += 1

        clasificacion[equipo_af]["pts"] += puntos_af
        clasificacion[equipo_ec]["pts"] += puntos_ec

        
        faltas_af = (
            int(primera.get("leves_af", 0))
            + int(primera.get("graves_af", 0))
        )

        faltas_ec = (
            int(primera.get("leves_ec", 0))
            + int(primera.get("graves_ec", 0))
        )

        clasificacion[equipo_af]["faltas"] += faltas_af
        clasificacion[equipo_ec]["faltas"] += faltas_ec

        
        if votos_af > votos_ec:

            clasificacion[equipo_af]["pg"] += 1
            clasificacion[equipo_ec]["pp"] += 1

        elif votos_ec > votos_af:

            clasificacion[equipo_ec]["pg"] += 1
            clasificacion[equipo_af]["pp"] += 1

    resultado = sorted(
        clasificacion.values(),
        key=lambda x: (
            -x["pg"],
            -x["pts"],
            x["faltas"]
        )
    )

    return JSONResponse(resultado)


@app.get("/faltas", response_class=HTMLResponse)
async def faltas(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="faltas.html",
        context={}
    )
@app.get("/equipos", response_class=HTMLResponse)
async def equipos(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="equipos.html",
        context={}
    )
@app.get("/equipos/datos")
async def equipos_datos():

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "equipos.json"),
            "r",
            encoding="utf-8"
        ) as f:

            equipos = json.load(f)

    except:
        equipos = []

    return JSONResponse(equipos)