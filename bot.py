#!/usr/bin/env python3
"""
Bot de Telegram: noticias sobre la persecucion del cristiano.

Flujo:
  RSS de agencias especializadas (sondeo cada pocos minutos, solo noticias
  recientes) -> extraccion de foto o video del articulo -> redaccion en
  espanol + traduccion al ingles -> borrador al chat privado del admin con
  botones -> publicacion en el canal solo si tu la apruebas.

Ejecutar:  python bot.py
"""

import calendar
import html
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone

import feedparser
import requests

import redaccion as R

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")
FUENTES_PATH = os.path.join(BASE, "fuentes.json")
ESTADO_PATH = os.path.join(BASE, "estado.json")
LOG_PATH = os.path.join(BASE, "bot.log")

TG = "https://api.telegram.org/bot{token}/{method}"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"

PROMPT = """Eres el redactor de un canal de Telegram en espanol sobre la persecucion de los cristianos en el mundo. El estilo es el de un canal informativo de sucesos internacionales (tipo "Entre Guerras"): sobrio, directo, factual, sin sermones, sin adjetivos emotivos, sin inventar nada que no este en la noticia.

Te doy una noticia. Haz dos cosas:

1) Decide si es RELEVANTE para el canal. Es relevante si trata de: persecucion, discriminacion, violencia, detenciones, asesinatos, secuestros, leyes de blasfemia o apostasia, destruccion de templos, restricciones legales o sociales contra cristianos, informes sobre libertad religiosa, o testimonios de martires. NO es relevante: campanas de donacion, eventos internos de una iglesia, nombramientos eclesiasticos, teologia, liturgia, politica sin componente de persecucion, noticias de otras religiones sin cristianos afectados.

2) Si es relevante, redacta el post.

Devuelve UNICAMENTE un objeto JSON valido, sin texto alrededor, con esta forma exacta:
{
  "relevante": true/false,
  "motivo": "una frase corta si no es relevante",
  "pais": "Nombre del pais en espanol, o 'Internacional'",
  "bandera": "emoji de la bandera del pais, o 🌍",
  "gravedad": "alta" | "media" | "baja",
  "titular_es": "titular de 6-12 palabras, en mayuscula inicial, sin punto final",
  "cuerpo_es": "2 a 4 frases con los hechos: que ha pasado, donde, cuando, a quien, cifras si las hay",
  "titular_en": "traduccion fiel del titular al ingles",
  "cuerpo_en": "traduccion fiel del cuerpo al ingles",
  "hashtags": ["#Pais", "#Region", "#TemaCorto"]
}

Reglas: "gravedad" es alta si hay muertos, secuestros o condenas graves; media si hay detenciones, ataques a templos o leyes restrictivas; baja si es un informe o contexto. Los hashtags van sin espacios ni tildes (#CoreaDelNorte, #Africa). No uses comillas tipograficas dentro del JSON.

NOTICIA:
Fuente: {fuente}
Titulo: {titulo}
Fecha: {fecha}
Resumen: {resumen}
"""


# --------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------

def log(msg):
    linea = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(linea, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except Exception:
        pass


def cargar_json(path, defecto=None):
    if not os.path.exists(path):
        return defecto
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def guardar_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def limpiar_html(texto):
    texto = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", texto or "", flags=re.S | re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = html.unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def esc(t):
    return html.escape(t or "", quote=False)


def antiguedad_horas(entrada):
    """Horas transcurridas desde la publicacion. None si el feed no da fecha."""
    for campo in ("published_parsed", "updated_parsed"):
        t = entrada.get(campo)
        if t:
            ts = calendar.timegm(t)
            return (time.time() - ts) / 3600.0
    return None


# --------------------------------------------------------------------------
# extraccion de foto / video
# --------------------------------------------------------------------------

EXT_IMG = (".jpg", ".jpeg", ".png", ".webp")
EXT_VID = (".mp4", ".mov", ".m4v")


def _es_imagen(url):
    return url and url.lower().split("?")[0].endswith(EXT_IMG)


def _es_video(url):
    return url and url.lower().split("?")[0].endswith(EXT_VID)


def media_del_feed(e):
    """Busca foto o video dentro de la propia entrada RSS."""
    candidatos = []
    for m in e.get("media_content", []) or []:
        candidatos.append((m.get("url"), m.get("type", "")))
    for m in e.get("media_thumbnail", []) or []:
        candidatos.append((m.get("url"), "image"))
    for l in e.get("links", []) or []:
        if l.get("rel") == "enclosure":
            candidatos.append((l.get("href"), l.get("type", "")))
    for url, tipo in candidatos:
        if not url:
            continue
        if "video" in (tipo or "") or _es_video(url):
            return {"tipo": "video", "url": url}
    for url, tipo in candidatos:
        if url and ("image" in (tipo or "") or _es_imagen(url)):
            return {"tipo": "foto", "url": url}
    # imagen incrustada en el html del resumen
    cuerpo = (e.get("content", [{}])[0].get("value", "") if e.get("content") else "") \
        or e.get("summary", "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', cuerpo or "")
    if m and _es_imagen(m.group(1)):
        return {"tipo": "foto", "url": m.group(1)}
    return None


def media_del_articulo(url, timeout=12):
    """Abre el articulo y saca og:video / og:image. Es lo que ha subido el medio."""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        h = r.text[:400000]
    except Exception:
        return None

    def meta(*props):
        for p in props:
            m = re.search(
                r'<meta[^>]+(?:property|name)=["\']' + p + r'["\'][^>]+content=["\']([^"\']+)["\']',
                h, re.I)
            if m:
                return html.unescape(m.group(1))
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']' + p + r'["\']',
                h, re.I)
            if m:
                return html.unescape(m.group(1))
        return None

    v = meta("og:video:secure_url", "og:video:url", "og:video", "twitter:player:stream")
    if v and _es_video(v):
        return {"tipo": "video", "url": v}

    # video de YouTube incrustado -> lo dejamos como enlace, Telegram lo previsualiza
    y = re.search(r'(?:youtube\.com/embed/|youtu\.be/|youtube\.com/watch\?v=)([\w-]{11})', h)
    if y:
        return {"tipo": "youtube", "url": f"https://www.youtube.com/watch?v={y.group(1)}"}

    img = meta("og:image:secure_url", "og:image", "twitter:image")
    if img and img.startswith("http"):
        return {"tipo": "foto", "url": img}
    return None


def obtener_media(e, enlace, buscar_en_articulo=True):
    m = media_del_feed(e)
    if m:
        return m
    if buscar_en_articulo and enlace:
        return media_del_articulo(enlace)
    return None


# --------------------------------------------------------------------------
# Telegram
# --------------------------------------------------------------------------

class Telegram:
    def __init__(self, token):
        self.token = token
        self.offset = None
        self.ultimo_error = ""

    def _call(self, method, **params):
        self.ultimo_error = ""
        try:
            r = requests.post(TG.format(token=self.token, method=method),
                              json=params, timeout=60)
            data = r.json()
            if not data.get("ok"):
                self.ultimo_error = f"{method}: {data.get('description')}"
                log(f"Telegram {self.ultimo_error}")
                return None
            return data["result"]
        except Exception as e:
            self.ultimo_error = f"{method}: {e}"
            log(f"Telegram excepcion {self.ultimo_error}")
            return None

    def copiar(self, chat_id, from_chat_id, message_id):
        """Copia un mensaje tal cual (texto, formato y foto) a otro chat.
        No lleva 'reenviado de' ni los botones del original."""
        return self._call("copyMessage", chat_id=chat_id,
                          from_chat_id=from_chat_id, message_id=message_id)

    def enviar_post(self, chat_id, texto, media=None, botones=None):
        """Publica el post con su foto o video.

        - foto: se manda como vista previa grande encima del texto, asi no hay
          limite de 1024 caracteres y cabe el post completo en espanol e ingles.
        - video: sendVideo con el texto como pie (recortado si hace falta).
        """
        markup = {"inline_keyboard": botones} if botones else None

        if media and media["tipo"] == "video":
            res = self._call("sendVideo", chat_id=chat_id, video=media["url"],
                             caption=texto[:1020], parse_mode="HTML",
                             supports_streaming=True,
                             **({"reply_markup": markup} if markup else {}))
            if res:
                return res
            log("sendVideo fallido, publico como texto con enlace")
            media = {"tipo": "foto", "url": media["url"]}

        params = {"chat_id": chat_id, "text": texto[:4090], "parse_mode": "HTML"}
        if media and media["tipo"] in ("foto", "youtube"):
            params["link_preview_options"] = {
                "url": media["url"],
                "prefer_large_media": True,
                "show_above_text": True,
            }
        else:
            params["link_preview_options"] = {"is_disabled": False}
        if markup:
            params["reply_markup"] = markup
        return self._call("sendMessage", **params)

    def enviar(self, chat_id, texto, botones=None):
        params = {"chat_id": chat_id, "text": texto[:4090], "parse_mode": "HTML",
                  "link_preview_options": {"is_disabled": True}}
        if botones:
            params["reply_markup"] = {"inline_keyboard": botones}
        return self._call("sendMessage", **params)

    def quitar_botones(self, chat_id, message_id, etiqueta):
        ok = self._call("editMessageReplyMarkup", chat_id=chat_id,
                        message_id=message_id,
                        reply_markup={"inline_keyboard": [[{"text": etiqueta,
                                                            "callback_data": "noop"}]]})
        return ok

    def responder_callback(self, callback_id, texto=""):
        return self._call("answerCallbackQuery", callback_query_id=callback_id,
                          text=texto)

    def actualizaciones(self, timeout=10):
        params = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
        if self.offset is not None:
            params["offset"] = self.offset
        try:
            r = requests.post(TG.format(token=self.token, method="getUpdates"),
                              json=params, timeout=timeout + 20)
            data = r.json()
        except Exception:
            return []
        if not data.get("ok"):
            return []
        ups = data["result"]
        if ups:
            self.offset = ups[-1]["update_id"] + 1
        return ups


# --------------------------------------------------------------------------
# IA (Claude)
# --------------------------------------------------------------------------

def redactar_con_ia(cfg, fuente, titulo, resumen, fecha):
    api_key = cfg.get("anthropic_api_key", "").strip()
    if not api_key or api_key.startswith("PEGA"):
        return None
    prompt = (PROMPT.replace("{fuente}", fuente).replace("{titulo}", titulo)
              .replace("{resumen}", resumen[:2500]).replace("{fecha}", fecha))
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key,
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": cfg.get("modelo", "claude-sonnet-5"),
                  "max_tokens": 1200,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=90,
        )
        data = r.json()
        if "content" not in data:
            log(f"IA error: {json.dumps(data)[:300]}")
            return None
        texto = "".join(b.get("text", "") for b in data["content"])
        m = re.search(r"\{.*\}", texto, re.S)
        return json.loads(m.group(0)) if m else None
    except Exception as e:
        log(f"IA excepcion: {e}")
        return None


# --------------------------------------------------------------------------
# formato del post
# --------------------------------------------------------------------------

EMOJI_GRAVEDAD = {"alta": "🚨", "media": "⚠️", "baja": "📄"}


def formatear(post, enlace, fuente, cfg, media=None):
    gravedad = EMOJI_GRAVEDAD.get(post.get("gravedad", "media"), "⚠️")
    pais = esc(post.get("pais", "Internacional")).upper()
    bandera = post.get("bandera", "🌍")

    lineas = [f"{gravedad} <b>{pais}</b> {bandera}",
              "",
              f"<b>{esc(post.get('titular_es', ''))}</b>",
              "",
              esc(post.get("cuerpo_es", ""))]

    if cfg.get("publicar_ingles", True) and post.get("titular_en"):
        lineas += ["", "➖➖➖",
                   f"🇬🇧 <b>{esc(post.get('titular_en', ''))}</b>", "",
                   f"<i>{esc(post.get('cuerpo_en', ''))}</i>"]

    tags = [t if t.startswith("#") else "#" + t for t in post.get("hashtags", [])]
    tags = [re.sub(r"[^#\w]", "", t) for t in tags]
    fijo = cfg.get("hashtag_fijo", "#IglesiaPerseguida")
    if fijo and fijo not in tags:
        tags.append(fijo)

    lineas += [""]
    if media and media["tipo"] == "youtube":
        lineas.append(f'🎥 <a href="{esc(media["url"])}">Vídeo</a>')
    lineas += [f'📎 <a href="{esc(enlace)}">Fuente: {esc(fuente)}</a>',
               " ".join(tags)]

    firma = cfg.get("firma", "").strip()
    if firma:
        lineas += ["", esc(firma)]
    return "\n".join(lineas)


# --------------------------------------------------------------------------
# lectura de feeds
# --------------------------------------------------------------------------

def relevante_por_palabras(texto, especializada=False, titulo=""):
    """Filtro sin IA: contexto cristiano + termino de persecucion + vetos."""
    return R.es_relevante(texto, especializada, titulo)


def leer_feeds(fuentes, vistos, cache, max_horas, max_por_fuente=10):
    """Devuelve las entradas nuevas y recientes. Usa ETag / Last-Modified para
    que el sondeo cada pocos minutos no castigue a los servidores."""
    nuevos = []
    for f in fuentes:
        if not f.get("activa", True):
            continue
        c = cache.get(f["url"], {})
        try:
            d = feedparser.parse(f["url"], agent=UA,
                                 etag=c.get("etag"), modified=c.get("modified"))
        except Exception as e:
            log(f"Feed fallido {f['nombre']}: {e}")
            continue

        if getattr(d, "status", None) == 304:      # sin novedades
            continue
        nueva_cache = {}
        if getattr(d, "etag", None):
            nueva_cache["etag"] = d.etag
        if getattr(d, "modified", None):
            nueva_cache["modified"] = d.modified
        if nueva_cache:
            cache[f["url"]] = nueva_cache

        if not d.entries:
            continue

        for e in d.entries[:max_por_fuente]:
            uid = e.get("id") or e.get("link")
            if not uid or uid in vistos:
                continue
            edad = antiguedad_horas(e)
            if edad is not None and edad > max_horas:
                vistos[uid] = "antigua"
                continue
            titulo = limpiar_html(e.get("title", ""))
            resumen = limpiar_html(e.get("summary", "") or e.get("description", ""))
            especializada = not f.get("filtrar", False)
            if not relevante_por_palabras(titulo + " " + resumen, especializada, titulo):
                vistos[uid] = "descartado_palabras"
                continue
            nuevos.append({
                "uid": uid, "fuente": f["nombre"], "titulo": titulo,
                "resumen": resumen, "enlace": e.get("link", ""),
                "idioma": f.get("idioma", "en"),
                "fecha": e.get("published", "") or e.get("updated", ""),
                "edad": edad, "entrada": e,
            })
    nuevos.sort(key=lambda n: n["edad"] if n["edad"] is not None else 999)
    return nuevos


# --------------------------------------------------------------------------
# bot
# --------------------------------------------------------------------------

def config_desde_entorno(cfg):
    """Permite ejecutar sin config.json usando variables de entorno.
    Es lo que se usa en GitHub Actions, donde el token va en Secrets."""
    mapa = {
        "TELEGRAM_BOT_TOKEN": ("telegram_bot_token", str),
        "CHANNEL_ID": ("channel_id", str),
        "ADMIN_CHAT_ID": ("admin_chat_id", int),
        "TRADUCIR": ("traducir", lambda v: v.lower() in ("1", "true", "si", "s")),
        "EMAIL_TRADUCTOR": ("email_traductor", str),
        "MAX_ANTIGUEDAD_HORAS": ("max_antiguedad_horas", int),
        "HASHTAG_FIJO": ("hashtag_fijo", str),
    }
    for env, (clave, tipo) in mapa.items():
        valor = os.environ.get(env, "").strip()
        if valor:
            try:
                cfg[clave] = tipo(valor)
            except Exception:
                pass
    return cfg


class Bot:
    def __init__(self):
        self.cfg = config_desde_entorno(cargar_json(CONFIG_PATH, {}) or {})
        if not self.cfg.get("telegram_bot_token"):
            sys.exit("Falta config.json (o la variable TELEGRAM_BOT_TOKEN).\n"
                     "Ejecuta:  python configurar.py")
        self.fuentes = cargar_json(FUENTES_PATH, {}).get("fuentes", [])
        estado = cargar_json(ESTADO_PATH, {}) or {}
        self.vistos = estado.get("vistos", {})
        self.cache = estado.get("cache", {})
        self.primer_arranque = not estado
        self.tg = Telegram(self.cfg["telegram_bot_token"])
        self.admin = int(self.cfg["admin_chat_id"]) if self.cfg.get("admin_chat_id") else None
        self.canal = self.cfg["channel_id"]

        # los borradores sin decidir sobreviven a reinicios: sus botones
        # siguen funcionando aunque cierres la ventana y la abras dias despues
        self.pendientes = estado.get("pendientes", {})
        self.purgar_pendientes()
        self.contador = max([int(k) for k in self.pendientes if k.isdigit()] or [0])

        self.editando = estado.get("editando")
        self.pausado = False
        self.ultimo_chequeo = 0

    def purgar_pendientes(self):
        """Tira los borradores muy viejos que nunca decidiste."""
        dias = self.cfg.get("dias_guardar_borradores", 14)
        limite = time.time() - dias * 86400
        antes = len(self.pendientes)
        self.pendientes = {k: v for k, v in self.pendientes.items()
                           if v.get("creado", time.time()) > limite}
        if antes != len(self.pendientes):
            log(f"Purgados {antes - len(self.pendientes)} borradores de mas de {dias} dias")

    def guardar_estado(self):
        items = list(self.vistos.items())[-5000:]
        guardar_json(ESTADO_PATH, {"vistos": dict(items), "cache": self.cache,
                                   "pendientes": self.pendientes,
                                   "editando": self.editando})

    # ---------------- ciclo de feeds ----------------

    def ciclo_feeds(self, forzar=False):
        intervalo = self.cfg.get("minutos_entre_chequeos", 3) * 60
        if not forzar and time.time() - self.ultimo_chequeo < intervalo:
            return
        self.ultimo_chequeo = time.time()
        if self.pausado:
            return

        max_horas = self.cfg.get("max_antiguedad_horas", 12)
        nuevos = leer_feeds(self.fuentes, self.vistos, self.cache, max_horas)

        # en el primer arranque no volcamos el historico: marcamos y a partir de
        # ahora solo llega lo que se publique de nuevo
        if self.primer_arranque:
            self.primer_arranque = False
            cuantos = self.cfg.get("borradores_en_primer_arranque", 5)
            estreno, resto = nuevos[:cuantos], nuevos[cuantos:]
            for n in resto:
                self.vistos[n["uid"]] = "arranque"
            self.guardar_estado()
            log(f"Primer arranque: {len(estreno)} borradores de estreno, "
                f"{len(resto)} noticias antiguas marcadas como vistas")
            if self.admin:
                self.tg.enviar(self.admin,
                               f"🟢 Primer arranque. Te mando {len(estreno)} noticias "
                               "recientes para estrenar el canal; el resto del historico "
                               "queda descartado. A partir de ahora solo lo nuevo.")
            nuevos = estreno

        if not nuevos:
            self.guardar_estado()
            return
        log(f"{len(nuevos)} noticias nuevas")

        maximo = self.cfg.get("max_borradores_por_ciclo", 6)
        enviados = 0
        for n in nuevos:
            if enviados >= maximo:
                break
            self.vistos[n["uid"]] = "procesado"

            # con clave de IA (opcional) se redacta con ella; sin clave, con reglas
            post = redactar_con_ia(self.cfg, n["fuente"], n["titulo"],
                                   n["resumen"], n["fecha"])
            if post is not None and not post.get("relevante", False):
                log(f"Descartada por IA: {n['titulo'][:60]} ({post.get('motivo', '')})")
                continue

            media = obtener_media(n["entrada"], n["enlace"],
                                  self.cfg.get("buscar_media_en_articulo", True))
            if post is None:
                texto = R.construir_post(n["titulo"], n["resumen"], n["enlace"],
                                         n["fuente"], self.cfg,
                                         idioma_fuente=n.get("idioma", "en"),
                                         media=media)
            else:
                texto = formatear(post, n["enlace"], n["fuente"], self.cfg, media)
            self.enviar_borrador(texto, n, media)
            enviados += 1
            time.sleep(1.5)
        self.guardar_estado()

    def enviar_borrador(self, texto, noticia, media):
        self.contador += 1
        pid = str(self.contador)
        edad = noticia.get("edad")
        cuando = f"hace {int(edad * 60)} min" if edad is not None and edad < 2 else \
                 (f"hace {edad:.1f} h" if edad is not None else "sin fecha")
        icono = {"foto": "🖼", "video": "🎬", "youtube": "🎥"}.get(
            media["tipo"] if media else "", "📄")

        # La cabecera va en un mensaje aparte: asi el mensaje del borrador es
        # exactamente el post final y se puede copiar tal cual al canal.
        self.tg.enviar(self.admin,
                       f"📝 <b>BORRADOR</b> · {esc(noticia['fuente'])} · {cuando} · {icono}")

        botones = [[
            {"text": "✅ Publicar", "callback_data": f"pub:{pid}"},
            {"text": "✏️ Editar", "callback_data": f"edit:{pid}"},
            {"text": "🗑 Descartar", "callback_data": f"del:{pid}"},
        ]]
        res = self.tg.enviar_post(self.admin, texto, media=media, botones=botones)
        if res:
            self.pendientes[pid] = {"texto": texto, "media": media,
                                    "msg_id": res["message_id"],
                                    "fuente": noticia["fuente"],
                                    "titulo": noticia["titulo"][:120],
                                    "creado": time.time()}
            self.guardar_estado()

    # ---------------- interaccion ----------------

    def publicar(self, pid, msg_id=None, preferir_texto=False):
        """Publica en el canal.

        Via principal: copiar el propio mensaje del borrador (copyMessage). No
        depende de nada guardado, asi que funciona aunque el estado se pierda.
        Via de respaldo: reenviar el texto guardado en estado.json.
        """
        p = self.pendientes.get(pid)
        msg_id = msg_id or (p or {}).get("msg_id")
        errores = []

        res = None
        # 1) el texto guardado, que sale limpio (sin la cabecera del borrador)
        if p and p.get("texto"):
            res = self.tg.enviar_post(self.canal, p["texto"], media=p.get("media"))
            if not res:
                errores.append(self.tg.ultimo_error)

        # 2) si eso falla o no hay estado, copiar el propio mensaje del borrador
        if not res and msg_id and not preferir_texto:
            res = self.tg.copiar(self.canal, self.admin, msg_id)
            if not res:
                errores.append(self.tg.ultimo_error)

        if res:
            if msg_id:
                self.tg.quitar_botones(self.admin, msg_id, "✅ Publicado en el canal")
            if pid in self.pendientes:
                del self.pendientes[pid]
            self.guardar_estado()
            log("Publicado en el canal")
            return True

        if not msg_id and not p:
            errores.append("no encuentro ese borrador ni su mensaje")
        log("Fallo al publicar: " + " | ".join(errores))
        self.tg.enviar(self.admin,
                       "❌ <b>No he podido publicar en el canal.</b>\n\n"
                       f"Canal configurado: <code>{esc(str(self.canal))}</code>\n"
                       f"Error de Telegram: <code>{esc(' | '.join(errores) or 'desconocido')}</code>\n\n"
                       "Manda /probar para un diagnostico completo.")
        return False

    def manejar_callback(self, cq):
        data = cq.get("data", "")
        if ":" not in data:
            self.tg.responder_callback(cq["id"])
            return
        accion, pid = data.split(":", 1)
        # el id del mensaje viene en la propia pulsacion: no dependemos del estado
        msg_id = (cq.get("message") or {}).get("message_id")
        self.tg.responder_callback(cq["id"], {"pub": "Publicando...",
                                              "del": "Descartado",
                                              "edit": "Mandame el texto"}.get(accion, ""))

        if accion == "pub":
            self.publicar(pid, msg_id)
        elif accion == "del":
            self.pendientes.pop(pid, None)
            self.guardar_estado()
            if msg_id:
                self.tg.quitar_botones(self.admin, msg_id, "🗑 Descartado")
        elif accion == "edit":
            self.editando = pid
            if msg_id and pid not in self.pendientes:
                self.pendientes[pid] = {"msg_id": msg_id, "texto": "", "media": None,
                                        "fuente": "", "titulo": "", "creado": time.time()}
            self.guardar_estado()
            self.tg.enviar(self.admin,
                           "✏️ Mandame el texto corregido tal cual quieres que salga "
                           "(puedes usar <b>negrita</b> con etiquetas HTML). "
                           "/cancelar para dejarlo.")

    def manejar_mensaje(self, msg):
        chat_id = msg["chat"]["id"]
        texto = msg.get("text", "")
        if self.admin and chat_id != self.admin:
            if texto.startswith("/start") or texto.startswith("/id"):
                self.tg.enviar(chat_id, f"Tu chat id es: <code>{chat_id}</code>")
            return

        if self.editando and not texto.startswith("/"):
            pid, self.editando = self.editando, None
            if pid in self.pendientes:
                self.pendientes[pid]["texto"] = texto
                if self.publicar(pid, preferir_texto=True):
                    self.tg.enviar(self.admin, "✅ Publicado con tus cambios.")
            self.guardar_estado()
            return

        cmd = texto.split()[0].lower() if texto else ""
        if cmd in ("/start", "/id"):
            self.tg.enviar(chat_id,
                           f"Bot activo.\nTu chat id: <code>{chat_id}</code>\n\n"
                           "/chequear · buscar noticias ahora\n"
                           "/probar · comprobar que puede publicar\n"
                           "/pendientes · borradores sin decidir\n"
                           "/estado · ver estado\n"
                           "/pausa y /reanudar\n"
                           "/cancelar · cancelar edicion")
        elif cmd == "/probar":
            self.diagnostico(chat_id)
        elif cmd == "/pendientes":
            if not self.pendientes:
                self.tg.enviar(chat_id, "No hay borradores pendientes.")
            else:
                lineas = [f"📝 <b>{len(self.pendientes)} borradores sin decidir</b>",
                          "Sus mensajes siguen en este chat con sus botones activos.", ""]
                for pid, p in sorted(self.pendientes.items(), key=lambda x: x[1].get("creado", 0)):
                    dias = (time.time() - p.get("creado", time.time())) / 86400
                    cuando = f"hace {int(dias * 24)} h" if dias < 1 else f"hace {int(dias)} d"
                    lineas.append(f"· {esc(p.get('titulo', '')[:70])} — {esc(p.get('fuente', ''))}, {cuando}")
                self.tg.enviar(chat_id, "\n".join(lineas[:60]))
        elif cmd == "/chequear":
            self.tg.enviar(chat_id, "🔎 Buscando...")
            self.ciclo_feeds(forzar=True)
            self.tg.enviar(chat_id, "Listo.")
        elif cmd == "/estado":
            activas = sum(1 for f in self.fuentes if f.get("activa", True))
            self.tg.enviar(chat_id,
                           f"Fuentes activas: {activas}\n"
                           f"Sondeo: cada {self.cfg.get('minutos_entre_chequeos', 3)} min\n"
                           f"Antiguedad maxima: {self.cfg.get('max_antiguedad_horas', 12)} h\n"
                           f"Noticias vistas: {len(self.vistos)}\n"
                           f"Borradores pendientes: {len(self.pendientes)}\n"
                           f"Pausado: {'si' if self.pausado else 'no'}\n"
                           f"Traduccion al espanol: {'si (MyMemory, gratis)' if self.cfg.get('traducir', True) else 'no'}\n"
                           f"IA de pago: {'si' if self.cfg.get('anthropic_api_key', '').startswith('sk-') else 'no (no hace falta)'}")
        elif cmd == "/pausa":
            self.pausado = True
            self.tg.enviar(chat_id, "⏸ Pausado.")
        elif cmd == "/reanudar":
            self.pausado = False
            self.tg.enviar(chat_id, "▶️ Reanudado.")
        elif cmd == "/cancelar":
            self.editando = None
            self.tg.enviar(chat_id, "Edicion cancelada.")

    # ---------------- diagnostico ----------------

    def diagnostico(self, chat_id):
        """Comprueba de verdad si el bot puede publicar en el canal y lo cuenta."""
        lineas = ["🔎 <b>DIAGNOSTICO</b>", ""]

        yo = self.tg._call("getMe")
        lineas.append(f"Bot: @{yo['username']}" if yo else
                      f"❌ Token: {esc(self.tg.ultimo_error)}")

        lineas.append(f"Canal configurado: <code>{esc(str(self.canal))}</code>")
        chat = self.tg._call("getChat", chat_id=self.canal)
        if not chat:
            lineas.append(f"❌ No encuentro el canal: <code>{esc(self.tg.ultimo_error)}</code>")
            self.tg.enviar(chat_id, "\n".join(lineas))
            return
        lineas.append(f"✅ Canal encontrado: {esc(str(chat.get('title')))}")

        if yo:
            miembro = self.tg._call("getChatMember", chat_id=self.canal, user_id=yo["id"])
            if not miembro:
                lineas.append(f"❌ El bot no esta en el canal: <code>{esc(self.tg.ultimo_error)}</code>")
            else:
                estado = miembro.get("status")
                puede = miembro.get("can_post_messages")
                lineas.append(f"Rol en el canal: <b>{esc(str(estado))}</b>")
                if estado != "administrator":
                    lineas.append("❌ Tiene que ser <b>administrador</b>.")
                elif not puede:
                    lineas.append("❌ Le falta el permiso <b>Publicar mensajes</b>.")
                else:
                    lineas.append("✅ Es administrador y puede publicar")

        prueba = self.tg.enviar(self.canal, "🔎 Prueba del bot. Puedes borrar este mensaje.")
        if prueba:
            lineas.append("✅ <b>Mensaje de prueba publicado en el canal</b>")
        else:
            lineas.append(f"❌ No he podido publicar: <code>{esc(self.tg.ultimo_error)}</code>")

        lineas += ["", f"Borradores pendientes: {len(self.pendientes)}"]
        self.tg.enviar(chat_id, "\n".join(lineas))

    # ---------------- una sola pasada (hosting gratuito) ----------------

    def run_once(self, segundos_escucha=20):
        """Una pasada y sale. Pensado para GitHub Actions:
        1) atiende los botones que pulsaste desde la ultima ejecucion
           (Telegram guarda esas pulsaciones hasta 24 h)
        2) revisa las webs y manda los borradores nuevos
        3) guarda el estado y termina
        """
        log("Pasada unica")
        fin = time.time() + segundos_escucha
        total = 0
        while time.time() < fin:
            ups = self.tg.actualizaciones(timeout=5)
            if not ups:
                break
            total += len(ups)
            for up in ups:
                if "callback_query" in up:
                    log(f"Pulsacion recibida: {up['callback_query'].get('data')}")
                    self.manejar_callback(up["callback_query"])
                elif "message" in up:
                    self.manejar_mensaje(up["message"])
        log(f"Actualizaciones procesadas: {total}")
        self.tg.actualizaciones(timeout=0)   # confirma lo procesado
        self.ciclo_feeds(forzar=True)
        self.guardar_estado()
        log(f"Fin de la pasada · {len(self.pendientes)} borradores pendientes")

    # ---------------- bucle principal ----------------

    def run(self):
        log("Bot arrancado")
        if self.admin and not self.primer_arranque:
            aviso = "🟢 Bot en marcha. /chequear para buscar ahora."
            if self.pendientes:
                aviso += (f"\n\n📝 Tienes <b>{len(self.pendientes)}</b> borradores sin decidir "
                          "de sesiones anteriores. Busca sus mensajes en este chat: "
                          "sus botones siguen funcionando.")
            self.tg.enviar(self.admin, aviso)
        while True:
            try:
                for up in self.tg.actualizaciones(timeout=10):
                    if "callback_query" in up:
                        self.manejar_callback(up["callback_query"])
                    elif "message" in up:
                        self.manejar_mensaje(up["message"])
                self.ciclo_feeds()
            except KeyboardInterrupt:
                log("Parado por el usuario")
                self.guardar_estado()
                return
            except Exception:
                log("Error inesperado:\n" + traceback.format_exc())
                time.sleep(15)


if __name__ == "__main__":
    if "--una-vez" in sys.argv:
        Bot().run_once()
    else:
        Bot().run()
