#!/usr/bin/env python3
"""Comprueba que el bot puede conectarse a tu canal.

Uso:  python probar_conexion.py

Verifica: token valido, tu chat id, que el bot es administrador del canal,
que puede publicar, y manda un mensaje de prueba con foto al canal.
"""
import json
import os
import sys

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(BASE, "config.json")
TG = "https://api.telegram.org/bot{token}/{method}"


def llamar(token, metodo, **params):
    r = requests.post(TG.format(token=token, method=metodo), json=params, timeout=30)
    return r.json()


def main():
    if not os.path.exists(CFG):
        sys.exit("❌ No existe config.json. Copia config.example.json a config.json y rellenalo.")
    cfg = json.load(open(CFG, encoding="utf-8"))
    token = cfg.get("telegram_bot_token", "").strip()
    canal = cfg.get("channel_id", "").strip()
    admin = cfg.get("admin_chat_id")

    # 1. token
    r = llamar(token, "getMe")
    if not r.get("ok"):
        sys.exit(f"❌ Token invalido: {r.get('description')}")
    bot = r["result"]
    print(f"✅ Token correcto. Bot: @{bot['username']} ({bot['first_name']})")

    # 2. canal existe y el bot esta dentro
    r = llamar(token, "getChat", chat_id=canal)
    if not r.get("ok"):
        sys.exit(f"❌ No encuentro el canal {canal}: {r.get('description')}\n"
                 "   Revisa que el nombre lleva @ y que has anadido el bot como administrador.")
    chat = r["result"]
    print(f"✅ Canal encontrado: {chat.get('title')} ({chat.get('type')})")

    # 3. permisos de administrador
    r = llamar(token, "getChatMember", chat_id=canal, user_id=bot["id"])
    if not r.get("ok"):
        sys.exit(f"❌ El bot no esta en el canal: {r.get('description')}")
    miembro = r["result"]
    if miembro.get("status") != "administrator":
        sys.exit(f"❌ El bot esta como '{miembro.get('status')}'. Tiene que ser administrador.")
    if not miembro.get("can_post_messages", False):
        sys.exit("❌ El bot es administrador pero SIN permiso de 'Publicar mensajes'. Activalo.")
    print("✅ El bot es administrador y puede publicar")

    # 4. numero de suscriptores
    r = llamar(token, "getChatMemberCount", chat_id=canal)
    if r.get("ok"):
        print(f"ℹ️  Suscriptores actuales: {r['result']}")

    # 5. chat privado del admin
    if admin:
        r = llamar(token, "sendMessage", chat_id=admin,
                   text="✅ Prueba de conexion correcta. Los borradores te llegaran aqui.")
        if r.get("ok"):
            print("✅ Puedo escribirte por privado")
        else:
            print(f"⚠️  No puedo escribirte por privado: {r.get('description')}\n"
                  "   Abre un chat con tu bot y mandale /start una vez.")
    else:
        print("⚠️  admin_chat_id sin rellenar. Escribe a @userinfobot para saber el tuyo.")

    # 6. mensaje de prueba en el canal, con foto grande, tal como se veran los posts
    texto = (
        "🧪 <b>PRUEBA</b> 🌍\n\n"
        "<b>Canal conectado correctamente</b>\n\n"
        "Este es el formato que tendran las publicaciones: titular, cuerpo en "
        "espanol, traduccion al ingles y enlace a la fuente original.\n\n"
        "➖➖➖\n"
        "🇬🇧 <b>Channel connected successfully</b>\n\n"
        "<i>This is a test message. You can delete it.</i>\n\n"
        "#Prueba #IglesiaPerseguida"
    )
    r = llamar(token, "sendMessage", chat_id=canal, text=texto, parse_mode="HTML",
               link_preview_options={"is_disabled": True})
    if r.get("ok"):
        print("✅ Mensaje de prueba publicado en el canal (puedes borrarlo)")
    else:
        print(f"❌ No he podido publicar: {r.get('description')}")
        return

    print("\n🎉 Todo listo. Arranca el bot con:  python bot.py")


if __name__ == "__main__":
    main()
