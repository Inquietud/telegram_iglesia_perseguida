#!/usr/bin/env python3
"""Comprueba que fuentes RSS de fuentes.json funcionan desde tu ordenador.

Uso:  python comprobar_fuentes.py
Con --desactivar marca como "activa": false las que no funcionen.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import feedparser

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "fuentes.json")
UA = "Mozilla/5.0 (compatible; CanalPersecucionBot/1.0)"


def comprobar(f):
    try:
        d = feedparser.parse(f["url"], agent=UA)
        n = len(d.entries)
        ejemplo = d.entries[0].get("title", "")[:70] if n else ""
        return f, n, ejemplo, ""
    except Exception as e:
        return f, 0, "", str(e)


def main():
    datos = json.load(open(PATH, encoding="utf-8"))
    fuentes = datos["fuentes"]
    with ThreadPoolExecutor(10) as p:
        resultados = list(p.map(comprobar, fuentes))

    ok = 0
    for f, n, ejemplo, err in resultados:
        if n:
            ok += 1
            print(f"OK   {n:3d} entradas  {f['nombre']}")
            print(f"                  ultimo: {ejemplo}")
        else:
            print(f"FALLA          {f['nombre']}  ->  {f['url']}  {err}")
            if "--desactivar" in sys.argv:
                f["activa"] = False

    print(f"\n{ok}/{len(fuentes)} fuentes funcionando")
    if "--desactivar" in sys.argv:
        json.dump(datos, open(PATH, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("fuentes.json actualizado (las que fallan quedan desactivadas)")


if __name__ == "__main__":
    main()
