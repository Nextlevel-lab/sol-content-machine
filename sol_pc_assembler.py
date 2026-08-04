"""
SOL PC ASSEMBLER — Corre en tu PC al encenderlo (Task Scheduler)
Descarga la cola de GitHub, genera voz + vídeo, guarda en E:
Sin internet = salta silenciosamente hasta el próximo encendido
"""
import json, subprocess, datetime, sys, os, urllib.request
from pathlib import Path

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
GITHUB_USER    = "TU_USUARIO_GITHUB"          # <-- cambiar
GITHUB_REPO    = "sol-content-machine"        # <-- cambiar si usas otro nombre
QUEUE_URL      = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/sol_queue.json"

BASE           = Path("E:/SOL_CONTENT")
ENGINE         = BASE / "_SOL_ENGINE"
LOG_DIR        = BASE / "METRICAS"
PROCESADOS     = ENGINE / "sol_procesados.json"

# ── LOG ───────────────────────────────────────────────────────────────────────
def log(msg, nivel="INFO"):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{ts}] [{nivel}] {msg}"
    print(linea, flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / f"assembler_{datetime.date.today()}.log", "a", encoding="utf-8") as f:
        f.write(linea + "\n")

# ── ESTADO ────────────────────────────────────────────────────────────────────
def cargar_procesados():
    if PROCESADOS.exists():
        return set(json.loads(PROCESADOS.read_text()))
    return set()

def guardar_procesados(p):
    ENGINE.mkdir(parents=True, exist_ok=True)
    PROCESADOS.write_text(json.dumps(list(p)))

# ── DESCARGAR COLA ────────────────────────────────────────────────────────────
def descargar_cola():
    try:
        with urllib.request.urlopen(QUEUE_URL, timeout=10) as r:
            data = json.loads(r.read())
            log(f"Cola descargada: {data['total']} videos del {data['generado']}")
            return data
    except Exception as e:
        log(f"Sin internet o GitHub no accesible: {e}", "WARN")
        return None

# ── GENERAR VOZ ───────────────────────────────────────────────────────────────
def generar_voz(texto, out):
    try:
        r = subprocess.run(
            ["edge-tts","--voice","es-ES-AlvaroNeural","--text",texto,"--write-media",str(out)],
            capture_output=True, timeout=30)
        if r.returncode == 0 and Path(out).exists():
            return True
    except: pass
    try:
        import pyttsx3
        e = pyttsx3.init()
        e.setProperty('rate', 150)
        e.save_to_file(texto, str(out))
        e.runAndWait()
        if Path(out).exists(): return True
    except: pass
    return False

# ── GENERAR IMAGEN FONDO ──────────────────────────────────────────────────────
def generar_imagen(nicho_nombre, tema, out):
    # Intenta ComfyUI local primero
    try:
        import urllib.request as ur, json as j, random, time, shutil
        prompt_img = f"cinematic photorealistic {tema}, professional lighting, 8k sharp"
        wf = {"3":{"inputs":{"seed":random.randint(0,999999),"steps":20,"cfg":7,"sampler_name":"euler","scheduler":"normal","denoise":1,"model":["4",0],"positive":["6",0],"negative":["7",0],"latent_image":["5",0]},"class_type":"KSampler"},"4":{"inputs":{"ckpt_name":"v1-5-pruned-emaonly.ckpt"},"class_type":"CheckpointLoaderSimple"},"5":{"inputs":{"width":1080,"height":1920,"batch_size":1},"class_type":"EmptyLatentImage"},"6":{"inputs":{"text":prompt_img,"clip":["4",1]},"class_type":"CLIPTextEncode"},"7":{"inputs":{"text":"blurry, bad, text, watermark","clip":["4",1]},"class_type":"CLIPTextEncode"},"8":{"inputs":{"samples":["3",0],"vae":["4",2]},"class_type":"VAEDecode"},"9":{"inputs":{"filename_prefix":"sol","images":["8",0]},"class_type":"SaveImage"}}
        data = j.dumps({"prompt":wf}).encode()
        req = ur.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
        with ur.urlopen(req, timeout=5):
            time.sleep(25)
            imgs = sorted(Path("E:/SOL_CONTENT/_SOL_ENGINE/COMFYUI/output").glob("sol*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
            if imgs:
                shutil.copy(imgs[0], out)
                return True
    except: pass

    # Fallback: imagen de color con PIL
    try:
        from PIL import Image, ImageDraw, ImageFont
        colores = {"01":(10,40,10),"02":(10,10,40),"03":(5,5,30),"04":(20,5,5),
                   "05":(30,20,5),"06":(5,20,30),"07":(15,30,15),"08":(5,25,10),
                   "09":(25,20,5),"10":(10,10,35)}
        nid = nicho_nombre[:2]
        color = colores.get(nid, (10,10,25))
        img = Image.new('RGB', (1080,1920), color=color)
        d = ImageDraw.Draw(img)
        d.rectangle([0,0,1080,8], fill=(255,215,0))
        d.rectangle([0,1912,1080,1920], fill=(255,215,0))
        nombre_limpio = nicho_nombre.replace("_"," ").replace("0123456789","")
        d.text((540,940), "SOL", fill=(255,215,0), anchor="mm")
        d.text((540,1000), nombre_limpio[:20], fill=(200,200,200), anchor="mm")
        img.save(str(out))
        return True
    except: pass
    return False

# ── MONTAR VÍDEO ──────────────────────────────────────────────────────────────
def montar_video(imagen, audio, out):
    try:
        cmd = ["ffmpeg","-y","-loop","1","-i",str(imagen)]
        if audio and Path(audio).exists():
            cmd += ["-i",str(audio),"-c:a","aac","-b:a","128k","-shortest"]
        else:
            cmd += ["-t","30"]
        cmd += ["-c:v","libx264","-preset","fast",
                "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
                "-pix_fmt","yuv420p", str(out)]
        r = subprocess.run(cmd, capture_output=True, timeout=120)
        return r.returncode == 0
    except Exception as e:
        log(f"FFmpeg error: {e}", "ERROR")
        return False

# ── MAIN ──────────────────────────────────────────────────────────────────────
def run():
    log("="*55)
    log("SOL PC ASSEMBLER — INICIO")
    log("="*55)

    cola_data = descargar_cola()
    if not cola_data:
        log("Sin cola disponible. Terminando.", "WARN")
        return

    procesados = cargar_procesados()
    videos_ok = 0

    for video in cola_data.get("videos", []):
        ts        = video["ts"]
        nicho     = video["nicho"]
        carpeta   = video["carpeta"]
        script    = video["script"]
        estado    = video.get("estado","pendiente")

        if ts in procesados:
            log(f"Ya procesado: {ts} — saltando")
            continue

        log(f"--- {nicho} | {ts} ---")
        base_nicho = BASE / carpeta
        base_nicho.mkdir(parents=True, exist_ok=True)

        # Guardar script
        script_out = base_nicho / "SCRIPTS" / f"script_{ts}.txt"
        script_out.parent.mkdir(parents=True, exist_ok=True)
        script_out.write_text(script, encoding="utf-8")

        # Imagen
        img_out = base_nicho / "ASSETS" / "FONDOS_IA" / f"fondo_{ts}.png"
        img_out.parent.mkdir(parents=True, exist_ok=True)
        generar_imagen(nicho, video["tema"], img_out)

        # Voz
        audio_out = base_nicho / "AUDIO" / "VOCES" / f"voz_{ts}.mp3"
        audio_out.parent.mkdir(parents=True, exist_ok=True)
        tiene_audio = generar_voz(script, audio_out)
        log(f"Voz: {'OK' if tiene_audio else 'sin audio'}")

        # Vídeos en 3 formatos
        for fmt in ["TIKTOK_9x16","YOUTUBE_16x9","INSTAGRAM_REELS"]:
            out_dir = base_nicho / "VIDEOS_FINALES" / fmt
            out_dir.mkdir(parents=True, exist_ok=True)
            ok = montar_video(img_out, audio_out if tiene_audio else None, out_dir / f"video_{ts}.mp4")
            log(f"  {fmt}: {'✓' if ok else '✗'}")
            if ok: videos_ok += 1

        procesados.add(ts)

    guardar_procesados(procesados)
    log(f"COMPLETADO: {videos_ok} vídeos ensamblados en E:")
    log("="*55)

if __name__ == "__main__":
    run()
