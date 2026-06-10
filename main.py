from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import json
from fastapi.responses import JSONResponse
import uuid
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

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "equipos.json"),
            "r",
            encoding="utf-8"
        ) as f:

            equipos = json.load(f)

    except:
        equipos = []

    return templates.TemplateResponse(
        request=request,
        name="acta.html",
        context={
            "mensaje": None,
            "equipos": equipos
        }
    )
@app.post("/guardar_acta")
async def guardar_acta(request: Request):

    form = await request.form()

    datos = dict(form)
    puntos_af = float(datos.get("puntos_af") or 0)
    puntos_ec = float(datos.get("puntos_ec") or 0)

    avisos_af = int(datos.get("avisos_af") or 0)
    avisos_ec = int(datos.get("avisos_ec") or 0)

    leves_af = int(datos.get("leves_af") or 0)
    leves_ec = int(datos.get("leves_ec") or 0)

    graves_af = int(datos.get("graves_af") or 0)
    graves_ec = int(datos.get("graves_ec") or 0)

    penalizacion_af = (leves_af * 0.5) + ((avisos_af // 2) * 0.5)
    penalizacion_ec = (leves_ec * 0.5) + ((avisos_ec // 2) * 0.5)

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

    oradores = []

    for clave in datos:

        if "_nota_" not in clave:
            continue

        nota = datos.get(clave)

        if nota == "":
            continue

        prefijo = clave.split("_nota_")[0]
        indice = clave.split("_nota_")[1]

        nombre = datos.get(
            f"{prefijo}_nombre_{indice}"
        )

        equipo = (
            datos["equipo_af"]
            if prefijo == "af"
            else datos["equipo_ec"]
        )

        oradores.append({
            "nombre": nombre,
            "equipo": equipo,
            "nota": float(nota)
        })
    nueva_acta = {
        "id": str(uuid.uuid4()),

        **datos,

        "oradores": oradores,

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

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "equipos.json"),
            "r",
            encoding="utf-8"
        ) as f:

            equipos = json.load(f)

    except:
        equipos = []

    for equipo in equipos:

        nombre = equipo["colegio"]

        clasificacion[nombre] = {
            "colegio": nombre,
            "pj": 0,
            "pg": 0,
            "pp": 0,
            "pts": 0,
            "faltas": 0
        }
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

        else:
            

            if puntos_af > puntos_ec:

                clasificacion[equipo_af]["pg"] += 1
                clasificacion[equipo_ec]["pp"] += 1

            elif puntos_ec > puntos_af:

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
@app.get("/clasificacion/oradores")
async def clasificacion_oradores():

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "debates.json"),
            "r",
            encoding="utf-8"
        ) as f:

            debates = json.load(f)

    except:
        debates = []

    ranking = {}

    for debate in debates:

        for orador in debate.get("oradores", []):

            nombre = orador["nombre"]

            if nombre not in ranking:

                ranking[nombre] = {
                    "nombre": nombre,
                    "equipo": orador["equipo"],
                    "puntos": 0
                }

            ranking[nombre]["puntos"] += float(
                orador["nota"]
            )

    resultado = sorted(
        ranking.values(),
        key=lambda x: x["puntos"],
        reverse=True
    )

    return JSONResponse(resultado)
@app.get("/debates/datos")
async def debates_datos():

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "debates.json"),
            "r",
            encoding="utf-8"
        ) as f:

            debates = json.load(f)

    except:
        debates = []

    return JSONResponse(debates)


@app.get("/debates", response_class=HTMLResponse)
async def debates(request: Request):

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "debates.json"),
            "r",
            encoding="utf-8"
        ) as f:

            actas = json.load(f)

    except:
        actas = []

    agrupados = {}

    for acta in actas:

        clave = (
            acta.get("ronda"),
            acta.get("sala")
        )

        if clave not in agrupados:

            agrupados[clave] = {
                "id": acta.get("id"),
                "ronda": acta.get("ronda"),
                "sala": acta.get("sala"),
                "favor": acta.get("equipo_af"),
                "contra": acta.get("equipo_ec"),
                "jueces": [],

                "avisos": (
                    int(acta.get("avisos_af", 0))
                    + int(acta.get("avisos_ec", 0))
                ),

                "faltas": (
                    int(acta.get("leves_af", 0))
                    + int(acta.get("leves_ec", 0))
                    + int(acta.get("graves_af", 0))
                    + int(acta.get("graves_ec", 0))
                )
            }

        agrupados[clave]["jueces"].append(
            acta.get("juez")
        )

       

    lista_debates = []

    for debate in agrupados.values():

        jueces = debate["jueces"]

        ganador_final = "-"

        equipo_af = debate["favor"]
        equipo_ec = debate["contra"]

        votos_af = 0
        votos_ec = 0

        clave = (
            debate["ronda"],
            debate["sala"]
        )

        for acta in actas:

            if (
                acta.get("ronda") == clave[0]
                and acta.get("sala") == clave[1]
            ):

                if acta.get("ganador") == equipo_af:
                    votos_af += 1

                elif acta.get("ganador") == equipo_ec:
                    votos_ec += 1

    if votos_af > votos_ec:
        ganador_final = equipo_af

    elif votos_ec > votos_af:
        ganador_final = equipo_ec

        lista_debates.append({
            "id": debate["id"],
            "ronda": debate["ronda"],
            "sala": debate["sala"],
            "favor": debate["favor"],
            "contra": debate["contra"],
            "jueces": jueces,
            "avisos": debate["avisos"],
            "faltas": debate["faltas"],
            "ganador": ganador_final
        })

    return templates.TemplateResponse(
        request=request,
        name="debates.html",
        context={
            "debates": lista_debates
        }
    )
@app.get("/debate/editar/{id}", response_class=HTMLResponse)
async def editar_debate(request: Request, id: str):

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "debates.json"),
            "r",
            encoding="utf-8"
        ) as f:

            debates = json.load(f)

    except:
        debates = []

    acta = None

    for debate in debates:

        if debate.get("id") == id:
            acta = debate
            break

    if not acta:
        return HTMLResponse(
            "Acta no encontrada",
            status_code=404
        )

    try:
        with open(
            os.path.join(BASE_DIR, "datos", "equipos.json"),
            "r",
            encoding="utf-8"
        ) as f:

            equipos = json.load(f)

    except:
        equipos = []

    return templates.TemplateResponse(
        request=request,
        name="acta.html",
        context={
            "mensaje": None,
            "equipos": equipos,
            "acta": acta,
            "modo_edicion": True
        }
    )
@app.post("/debate/actualizar/{id}")
async def actualizar_debate(
    request: Request,
    id: str
):

    form = await request.form()

    datos = dict(form)

    puntos_af = float(datos.get("puntos_af") or 0)
    puntos_ec = float(datos.get("puntos_ec") or 0)

    avisos_af = int(datos.get("avisos_af") or 0)
    avisos_ec = int(datos.get("avisos_ec") or 0)

    leves_af = int(datos.get("leves_af") or 0)
    leves_ec = int(datos.get("leves_ec") or 0)

    graves_af = int(datos.get("graves_af") or 0)
    graves_ec = int(datos.get("graves_ec") or 0)

    penalizacion_af = (leves_af * 0.5) + ((avisos_af // 2) * 0.5)
    penalizacion_ec = (leves_ec * 0.5) + ((avisos_ec // 2) * 0.5)

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

    oradores = []

    for clave in datos:

        if "_nota_" not in clave:
            continue

        nota = datos.get(clave)

        if nota == "":
            continue

        prefijo = clave.split("_nota_")[0]
        indice = clave.split("_nota_")[1]

        nombre = datos.get(
            f"{prefijo}_nombre_{indice}"
        )

        equipo = (
            datos["equipo_af"]
            if prefijo == "af"
            else datos["equipo_ec"]
        )

        oradores.append({
            "nombre": nombre,
            "equipo": equipo,
            "nota": float(nota)
        })

    try:

        with open(
            os.path.join(BASE_DIR, "datos", "debates.json"),
            "r",
            encoding="utf-8"
        ) as f:

            debates = json.load(f)

    except:

        debates = []

    for i, debate in enumerate(debates):

        if debate.get("id") == id:

            debates[i] = {
                "id": id,
                **datos,
                "oradores": oradores,
                "penalizacion_af": penalizacion_af,
                "penalizacion_ec": penalizacion_ec,
                "final_af": final_af,
                "final_ec": final_ec,
                "ganador": ganador
            }

            break

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
            "mensaje": "✅ Acta actualizada correctamente",
            "equipos": [],
            "modo_edicion": False
        }
    )
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
@app.get("/equipo/{nombre}")
async def datos_equipo(nombre: str):

    with open(
        os.path.join(BASE_DIR, "datos", "equipos.json"),
        "r",
        encoding="utf-8"
    ) as f:

        equipos = json.load(f)

    for equipo in equipos:

        if equipo["colegio"] == nombre:
            return equipo

    return {}

@app.get("/borrar_actas")
async def borrar_actas():

    with open(
        os.path.join(BASE_DIR, "datos", "debates.json"),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump([], f)

    return {"ok": True}