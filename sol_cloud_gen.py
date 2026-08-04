"""
SOL CLOUD GEN — Corre en GitHub Actions (gratis, sin PC)
Genera los scripts del día y los guarda en sol_queue.json
El PC los descarga al encenderse y ensambla los vídeos
"""
import json, random, datetime, os
from pathlib import Path

NICHOS = [
    {"id":"01","nombre":"FINANZAS_INVERSIONES",  "carpeta":"01_FINANZAS_INVERSIONES",  "tema":"finanzas e inversiones"},
    {"id":"02","nombre":"PSICOLOGIA_MENTE",       "carpeta":"02_PSICOLOGIA_MENTE",       "tema":"psicología y hacks mentales"},
    {"id":"03","nombre":"IA_TECNOLOGIA",           "carpeta":"03_IA_TECNOLOGIA",           "tema":"inteligencia artificial y tecnología"},
    {"id":"04","nombre":"HISTORIA_CRIMEN",         "carpeta":"04_HISTORIA_CRIMEN",         "tema":"historia oscura y crimen real"},
    {"id":"05","nombre":"MOTIVACION_ESTOICISMO",   "carpeta":"05_MOTIVACION_ESTOICISMO",   "tema":"motivación y estoicismo"},
    {"id":"06","nombre":"QUE_PASARIA_SI",          "carpeta":"06_QUE_PASARIA_SI",          "tema":"escenarios hipotéticos de ciencia"},
    {"id":"07","nombre":"INMOBILIARIO_NEGOCIOS",   "carpeta":"07_INMOBILIARIO_NEGOCIOS",   "tema":"inmobiliario y negocios"},
    {"id":"08","nombre":"SALUD_FITNESS",           "carpeta":"08_SALUD_FITNESS",           "tema":"salud y fitness"},
    {"id":"09","nombre":"LUJO_LIFESTYLE",          "carpeta":"09_LUJO_LIFESTYLE",          "tema":"lujo y estilo de vida premium"},
    {"id":"10","nombre":"EDUCACION_GLOBAL",        "carpeta":"10_EDUCACION_GLOBAL",        "tema":"educación y datos curiosos"},
]

PLANTILLAS = {
    "01":["El {pct}% de los millonarios tienen {n} fuentes de ingresos. Tú puedes tener la tuya.",
          "Con {euros}€ al mes y esta regla, en {anios} años alcanzas la libertad financiera.",
          "El error que comete el {pct}% de la gente: gastar antes de ahorrar. La regla del {n}%."],
    "02":["Tu cerebro decide en {ms} milisegundos si alguien te cae bien. Así puedes influir.",
          "El efecto Dunning-Kruger explicado en 30 segundos. Y cómo usarlo a tu favor.",
          "Cada vez que evitas una tarea tu cerebro genera {n}x más ansiedad. El truco para romperlo."],
    "03":["Esta IA hace en {min} minutos lo que antes tardaba {horas} horas. Y es gratis.",
          "Los {n} prompts que uso cada día para que la IA trabaje mientras duermo.",
          "Gané {euros}€ este mes con herramientas de IA completamente gratuitas."],
    "04":["El crimen sin resolver durante {anios} años que cambió la historia de {lugar}.",
          "La operación secreta que nadie conoce pero que cambió {pais} para siempre.",
          "En {anio}, {n} personas desaparecieron en {lugar}. Lo que encontraron fue perturbador."],
    "05":["Marco Aurelio tenía {n} reglas para el caos. La número {num} lo cambia todo.",
          "La disciplina supera al talento. Siempre. Los {n} hábitos que lo demuestran.",
          "El día que dejé de buscar motivación y empecé a construir sistemas, todo cambió."],
    "06":["¿Qué pasaría si la Tierra girase {n} veces más rápido? Te sorprenderá la respuesta.",
          "Si no necesitaras dormir tendrías {horas} horas extra al año. Pero habría un problema.",
          "¿Y si todos los humanos desapareciéramos mañana? Esto pasaría en {n} años."],
    "07":["El {pct}% de los inversores inmobiliarios cometen este error en su primera compra.",
          "Con {euros}€ puedes invertir en inmobiliario sin comprar ningún piso. Así funciona.",
          "Los {n} barrios que más se revalorizarán en {anio} según datos del Ministerio."],
    "08":["Hacer esto {min} minutos al día reduce el riesgo de diabetes en un {pct}%.",
          "Los {n} alimentos que destruyen tu energía por la mañana. El número {num} te sorprende.",
          "Tu postura al sentarte está dañando tu espalda. El ejercicio de {min} minutos que lo revierte."],
    "09":["Así es el interior del avión privado más caro del mundo: {precio} millones de euros.",
          "Los {n} hoteles más exclusivos donde una noche cuesta más que un coche de lujo.",
          "Cómo viven los {n} jóvenes más ricos del mundo antes de los {edad} años."],
    "10":["Un dato sobre {pais} que nadie te enseñó en el colegio pero que lo explica todo.",
          "Por qué el sistema educativo de {pais} es el mejor del mundo según {n} estudios.",
          "Aprende {idioma} en {min} días con este método. Sin apps, sin clases, sin dinero."],
}

VARS = {
    "pct":  lambda: random.choice([73,67,82,91,58,44]),
    "n":    lambda: random.choice([3,5,7,4,10,6]),
    "euros":lambda: random.choice([500,1000,100,50,2000,300]),
    "anio": lambda: random.choice([2025,2026,2024]),
    "anios":lambda: random.choice([10,20,5,15,30]),
    "ms":   lambda: random.choice([50,100,200,33,80]),
    "min":  lambda: random.choice([5,10,15,20,3]),
    "horas":lambda: random.choice([8,24,48,2920,4]),
    "lugar":lambda: random.choice(["Alemania","Perú","Canadá","Japón","los Alpes"]),
    "pais": lambda: random.choice(["España","Finlandia","Japón","Canadá","Singapur"]),
    "num":  lambda: random.choice([2,3,5,7,4]),
    "precio":lambda: random.choice([500,350,220,180,650]),
    "edad": lambda: random.choice([30,25,35,28]),
    "idioma":lambda: random.choice(["inglés","francés","alemán","japonés","italiano"]),
    "horas":lambda: random.choice([2920,1460,730,8760]),
}

def fill(plantilla):
    for k, fn in VARS.items():
        plantilla = plantilla.replace("{"+k+"}", str(fn()))
    return plantilla

def cargar_estado():
    f = Path("sol_estado_cloud.json")
    if f.exists():
        return json.loads(f.read_text())
    return {"nicho_actual": 0, "dias_generados": 0}

def guardar_estado(e):
    Path("sol_estado_cloud.json").write_text(json.dumps(e, indent=2))

def intentar_claude(tema):
    """Usa Claude API si CLAUDE_API_KEY está en secrets de GitHub"""
    try:
        api_key = os.environ.get("CLAUDE_API_KEY", "")
        if not api_key:
            return None
        import urllib.request, json as j
        body = j.dumps({
            "model": "claude-haiku-20240307",
            "max_tokens": 150,
            "messages": [{"role": "user", "content":
                f"Script viral 30 segundos sobre {tema}. Hook en 3 segundos. Máximo 70 palabras. Solo texto hablado. Español natural."}]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body, method="POST")
        req.add_header("x-api-key", api_key)
        req.add_header("anthropic-version", "2023-06-01")
        req.add_header("content-type", "application/json")
        with urllib.request.urlopen(req, timeout=15) as r:
            return j.loads(r.read())["content"][0]["text"].strip()
    except:
        return None

# ── MAIN ──────────────────────────────────────────────────────────────────────
estado = cargar_estado()
hoy = datetime.date.today().strftime("%Y-%m-%d")
idx_base = estado["nicho_actual"] % len(NICHOS)

VIDEOS_POR_DIA = 3
cola = []
log_lines = [f"=== SOL CLOUD GEN | {hoy} ==="]

for i in range(VIDEOS_POR_DIA):
    nicho = NICHOS[(idx_base + i) % len(NICHOS)]
    nid = nicho["id"]

    # Claude si hay créditos, sino plantilla
    script = intentar_claude(nicho["tema"])
    motor = "claude"
    if not script:
        script = fill(random.choice(PLANTILLAS.get(nid, PLANTILLAS["05"])))
        motor = "plantilla"

    entrada = {
        "fecha":   hoy,
        "nicho":   nicho["nombre"],
        "carpeta": nicho["carpeta"],
        "tema":    nicho["tema"],
        "script":  script,
        "motor":   motor,
        "estado":  "pendiente",
        "ts":      f"{hoy.replace('-','')}_{i:02d}",
    }
    cola.append(entrada)
    log_lines.append(f"[{nicho['nombre']}] ({motor}) {script[:70]}...")
    print(f"✓ {nicho['nombre']} | {motor} | {script[:60]}...")

# Guardar cola para que el PC la descargue
queue_data = {
    "generado": hoy,
    "total": len(cola),
    "videos": cola
}
Path("sol_queue.json").write_text(
    json.dumps(queue_data, ensure_ascii=False, indent=2), encoding="utf-8")

Path("sol_log.txt").write_text(
    "\n".join(log_lines), encoding="utf-8")

estado["nicho_actual"] = (idx_base + VIDEOS_POR_DIA) % len(NICHOS)
estado["dias_generados"] = estado.get("dias_generados", 0) + 1
guardar_estado(estado)

print(f"\n✅ Cola generada: {len(cola)} vídeos para {hoy}")
print(f"📁 Guardada en sol_queue.json — el PC la descarga al encenderse")
