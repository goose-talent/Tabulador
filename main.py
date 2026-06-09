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
            "datos/debates.json",
            "r",
            encoding="utf-8"
        ) as f:

            debates = json.load(f)

    except:
        debates = []

    debates.append(nueva_acta)

    with open(
        "datos/debates.json",
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
            "datos/debates.json",
            "r",
            encoding="utf-8"
        ) as f:

            debates = json.load(f)

    except:
        debates = []

    return JSONResponse(debates)


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
            "datos/equipos.json",
            "r",
            encoding="utf-8"
        ) as f:

            equipos = json.load(f)

    except:
        equipos = []

    return JSONResponse(equipos)