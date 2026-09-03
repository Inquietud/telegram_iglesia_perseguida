#!/usr/bin/env python3
"""Vigila en directo si tus pulsaciones llegan a Telegram.

Uso:  python ver_pulsaciones.py

No consume nada: solo consulta cuantas actualizaciones hay esperando. Dejalo
abierto y pulsa un boton de un borrador en Telegram. El contador deberia subir.
"""
import json
import os
import time

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
TOKEN = cfg["telegram_bot_token"]


def api(metodo, **p):
    try:
        return requests.post(f"https://api.telegram.org/bot{TOKEN}/{metodo}",
                             json=p, timeout=20).json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


yo = api("getMe")
print("Bot:", yo.get("result", {}).get("username") if yo.get("ok") else yo.get("description"))

info = api("getWebhookInfo").get("result", {})
print("Webhook:", info.get("url") or "ninguno (correcto)")
print()
print("=" * 60)
print(" PULSA AHORA un boton (✅ / 🗑) en un borrador de Telegram.")
print(" El contador de abajo deberia subir a 1 en menos de 2 segundos.")
print(" Ctrl+C para salir.")
print("=" * 60)
print()

previo = None
subidas = 0
inicio = time.time()
while time.time() - inicio < 180:
    n = api("getWebhookInfo").get("result", {}).get("pending_update_count", 0)
    if n != previo:
        marca = time.strftime("%H:%M:%S")
        if previo is not None and n > previo:
            subidas += 1
            print(f"[{marca}] En cola: {n}   <-- ¡PULSACION REGISTRADA!")
        elif previo is not None and n < previo:
            print(f"[{marca}] En cola: {n}   <-- alguien acaba de recogerlas")
        else:
            print(f"[{marca}] En cola: {n}")
        previo = n
    time.sleep(2)

print()
if subidas:
    print("RESULTADO: tus pulsaciones SI llegan a Telegram.")
    print("Si el contador bajo a 0 sin que se publicara nada, hay otro proceso")
    print("robandolas: cierra ARRANCAR.bat y PUBLICAR-AHORA.bat.")
    print("Si se quedan en cola, las recogera GitHub en la siguiente pasada.")
else:
    print("RESULTADO: el contador nunca subio.")
    print("Tus pulsaciones no llegan a Telegram. Comprueba que estas pulsando")
    print("los botones del BOT (chat actualizador_cristiano), no otra cosa.")
