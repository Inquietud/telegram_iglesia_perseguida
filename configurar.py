#!/usr/bin/env python3
"""Asistente de configuracion. Te va guiando y deja el bot listo para arrancar.

Uso:  python configurar.py

Hace por ti: instalar dependencias, validar el token, detectar tu chat id,
comprobar que el bot es administrador del canal y escribir config.json.
"""
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(BASE, "config.json")
TG = "https://api.telegram.org/bot{token}/{method}"


def titulo(t):
    print("\n" + "=" * 62)
    print(t)
    print("=" * 62)


def preguntar(texto, defecto=None):
    sufijo = f" [{defecto}]" if defecto is not None else ""
    while True:
        v = input(f"{texto}{sufijo}: ").strip()
        if v:
            return v
        if defecto is not None:
            return defecto


# --- dependencias -----------------------------------------------------------

def asegurar_dependencias():
    try:
        import feedparser  # noqa
        import requests  # noqa
        return
    except ImportError:
        print("Instalando dependencias (feedparser, requests)...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        "-r", os.path.join(BASE, "requirements.txt")], check=False)
        try:
            import feedparser  # noqa
            import requests  # noqa
        except ImportError:
            sys.exit("No he podido instalar las dependencias. Prueba a mano:\n"
                     f"  {sys.executable} -m pip install feedparser requests")


asegurar_dependencias()
import requests  # noqa: E402


def api(token, metodo, **params):
    try:
        return requests.post(TG.format(token=token, method=metodo),
                             json=params, timeout=30).json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


# --- pasos ------------------------------------------------------------------

def paso_token(previo=""):
    titulo("PASO 1 · Token del bot")
    print("Es la cadena larga que te dio @BotFather, tipo 8123456789:AAF...")
    print("Si lo has revocado, usa el nuevo.\n")
    while True:
        token = preguntar("Token", previo or None)
        r = api(token, "getMe")
        if r.get("ok"):
            bot = r["result"]
            print(f"\n✅ Token correcto · bot @{bot['username']}")
            return token, bot
        print(f"\n❌ Token invalido ({r.get('description')}). Prueba otra vez.\n")


def paso_canal(token, bot, previo=""):
    titulo("PASO 2 · Canal")
    print("Escribe el nombre del canal con arroba (@mi_canal) o pega su enlace t.me.\n")
    while True:
        canal = preguntar("Canal", previo or None)
        canal = canal.strip()
        for pref in ("https://t.me/", "http://t.me/", "t.me/"):
            if canal.startswith(pref):
                canal = "@" + canal[len(pref):]
        if not canal.startswith("@"):
            canal = "@" + canal
        canal = canal.rstrip("/")

        r = api(token, "getChat", chat_id=canal)
        if not r.get("ok"):
            print(f"\n❌ No encuentro {canal} ({r.get('description')}).")
            print("   Comprueba que el canal es publico y que el nombre es exacto.\n")
            continue
        chat = r["result"]
        print(f"\n✅ Canal encontrado: {chat.get('title')}")
        return canal, chat


def paso_admin(token, bot, canal):
    titulo("PASO 3 · El bot como administrador del canal")
    print("Este es el UNICO paso que no puedo hacer yo: Telegram exige hacerlo")
    print("desde la app. Y ojo: en Telegram Web NO funciona, el buscador de")
    print("administradores no encuentra bots. Hazlo desde el movil o desde")
    print("Telegram Desktop (desktop.telegram.org).\n")
    print("  MOVIL:")
    print("   1. Abre el canal")
    print("   2. Toca el nombre del canal arriba")
    print("   3. Lapiz ✏️ (Editar), arriba a la derecha")
    print("   4. Administradores → Anadir administrador")
    print(f"   5. Busca:  {bot['username']}   (sin @, no hace falta entero)")
    print("   6. Tocalo → deja activado 'Publicar mensajes' → ✓\n")

    while True:
        r = api(token, "getChatMember", chat_id=canal, user_id=bot["id"])
        estado = r.get("result", {}) if r.get("ok") else {}
        if estado.get("status") == "administrator" and estado.get("can_post_messages"):
            print("✅ El bot ya es administrador y puede publicar")
            return True
        if estado.get("status") == "administrator":
            print("⚠️  Es administrador pero le falta el permiso 'Publicar mensajes'.")
        else:
            print("⏳ Todavia no aparece como administrador.")
        r = input("   Pulsa Enter cuando lo hayas hecho (o escribe 'saltar'): ").strip().lower()
        if r == "saltar":
            print("   Saltado. Recuerda que sin esto el bot no podra publicar.")
            return False


def paso_chat_id(token):
    titulo("PASO 4 · Tu chat id (donde recibiras los borradores)")
    print("Abre un chat privado con tu bot y mandale cualquier mensaje, por")
    print("ejemplo /start. Lo detecto solo.\n")
    print("Esperando tu mensaje", end="", flush=True)

    api(token, "getUpdates", offset=-1)  # limpia lo viejo
    limite = time.time() + 180
    while time.time() < limite:
        r = api(token, "getUpdates", timeout=10)
        if r.get("ok"):
            for up in r["result"]:
                msg = up.get("message") or up.get("edited_message")
                if msg and msg["chat"]["type"] == "private":
                    cid = msg["chat"]["id"]
                    nombre = msg["chat"].get("first_name", "")
                    print(f"\n✅ Detectado: {nombre} · chat id {cid}")
                    return cid
        print(".", end="", flush=True)
    print("\n⚠️  No he detectado ningun mensaje.")
    manual = preguntar("Escribe tu chat id a mano (te lo da @userinfobot)", "0")
    return int(manual)


def paso_traduccion():
    titulo("PASO 5 · Traduccion al espanol (gratis)")
    print("Las mejores fuentes publican en ingles. El bot puede traducir cada")
    print("noticia al espanol con MyMemory: gratuito, sin clave y sin tarjeta.")
    print("Limite: 5.000 caracteres al dia, o 50.000 si das un email (solo se")
    print("manda al traductor para ampliar la cuota; puedes dejarlo vacio).")
    print("Si la cuota se agota, el bot sigue funcionando en el idioma original.\n")

    trad = preguntar("Traducir al espanol? (s/n)", "s").lower().startswith("s")
    email = ""
    if trad:
        email = input("Email para ampliar la cuota (Enter para omitir): ").strip()
        probar = traducir_prueba(email)
        if probar:
            print(f"✅ Traductor funcionando · prueba: \"{probar}\"")
        else:
            print("⚠️  Ahora mismo no responde. Se queda activado igualmente:")
            print("    si falla, el bot publica en el idioma original.")

    original = preguntar("Incluir el texto original debajo del espanol? (s/n)", "s")
    return {
        "traducir": trad,
        "email_traductor": email,
        "publicar_ingles": original.lower().startswith("s"),
        "anthropic_api_key": "",
    }


def traducir_prueba(email=""):
    try:
        params = {"q": "Ten Christians were arrested in China.", "langpair": "en|es"}
        if email:
            params["de"] = email
        r = requests.get("https://api.mymemory.translated.net/get",
                         params=params, timeout=25).json()
        t = (r.get("responseData") or {}).get("translatedText", "")
        return t if r.get("responseStatus") in (200, "200") else ""
    except Exception:
        return ""


def paso_preferencias():
    titulo("PASO 6 · Preferencias")
    minutos = preguntar("Cada cuantos minutos mira las webs", "3")
    horas = preguntar("Descartar noticias de mas de X horas", "12")
    hashtag = preguntar("Hashtag fijo en todos los posts", "#IglesiaPerseguida")
    return {
        "minutos_entre_chequeos": int(minutos),
        "max_antiguedad_horas": int(horas),
        "hashtag_fijo": hashtag,
    }


def main():
    titulo("ASISTENTE DE CONFIGURACION · canal de la Iglesia perseguida")
    previo = {}
    if os.path.exists(CFG):
        try:
            previo = json.load(open(CFG, encoding="utf-8"))
            print("Encontrado config.json. Pulsa Enter para conservar lo que ya hay.")
        except Exception:
            previo = {}

    token, bot = paso_token(previo.get("telegram_bot_token", ""))
    canal, chat = paso_canal(token, bot, previo.get("channel_id", ""))
    paso_admin(token, bot, canal)
    admin_id = paso_chat_id(token)
    traduccion = paso_traduccion()
    prefs = paso_preferencias()

    cfg = {
        "telegram_bot_token": token,
        "channel_id": canal,
        "admin_chat_id": admin_id,
        "max_borradores_por_ciclo": 6,
        "buscar_media_en_articulo": True,
        "firma": "",
    }
    cfg.update(traduccion)
    cfg.update(prefs)
    json.dump(cfg, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n✅ Guardado en {CFG}")

    titulo("COMPROBACION FINAL")
    r = api(token, "sendMessage", chat_id=canal,
            text="🧪 <b>PRUEBA</b>\n\nCanal conectado correctamente. Puedes borrar este mensaje.",
            parse_mode="HTML")
    if r.get("ok"):
        print("✅ Mensaje de prueba publicado en el canal")
    else:
        print(f"❌ No he podido publicar: {r.get('description')}")
        print("   Repasa el PASO 3: el bot tiene que ser administrador con")
        print("   permiso de publicar. Vuelve a lanzar este asistente despues.")

    if admin_id:
        api(token, "sendMessage", chat_id=admin_id,
            text="✅ Configuracion terminada. Aqui te llegaran los borradores.")

    titulo("YA ESTA")
    print("Arranca el bot con:")
    print("   python bot.py")
    print("(o haz doble clic en ARRANCAR.bat)")
    print("\nEn el primer arranque no publica el historico: a partir de ahi te")
    print("llega cada noticia nueva a los pocos minutos de publicarse.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelado.")
