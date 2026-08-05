#!/usr/bin/env python3
"""Redaccion de posts sin ninguna API de pago.

Detecta el pais y su bandera, calcula la gravedad, resume la noticia, genera
hashtags y (opcionalmente) traduce al espanol con MyMemory, que es gratuito y
no necesita clave ni tarjeta.
"""
import html
import json
import os
import re
import time

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE_TRAD = os.path.join(BASE, "traducciones.json")

# --------------------------------------------------------------------------
# paises: (nombre_es, bandera, region, alias separados por |)
# --------------------------------------------------------------------------

PAISES = [
    ("Nigeria", "🇳🇬", "África", "nigeria|nigerian|plateau state|benue|kaduna|borno"),
    ("India", "🇮🇳", "Asia", "india|indian|uttar pradesh|chhattisgarh|odisha|manipur"),
    ("Pakistán", "🇵🇰", "Asia", "pakistan|pakistani|punjab province|lahore|karachi"),
    ("China", "🇨🇳", "Asia", "china|chinese|xinjiang|henan|zhejiang|uighur|uyghur"),
    ("Corea del Norte", "🇰🇵", "Asia", "north korea|north korean|corea del norte|dprk"),
    ("Irán", "🇮🇷", "OrienteMedio", "iran|iranian|teheran|tehran"),
    ("Irak", "🇮🇶", "OrienteMedio", "iraq|iraqi|mosul|nineveh|bagdad|baghdad"),
    ("Siria", "🇸🇾", "OrienteMedio", "syria|syrian|siria|damascus|damasco|aleppo"),
    ("Egipto", "🇪🇬", "OrienteMedio", "egypt|egyptian|egipto|coptic|copto|minya"),
    ("Turquía", "🇹🇷", "OrienteMedio", "turkey|turkish|turquia|istanbul|estambul"),
    ("Arabia Saudí", "🇸🇦", "OrienteMedio", "saudi arabia|saudi|arabia saudi|riyadh"),
    ("Yemen", "🇾🇪", "OrienteMedio", "yemen|yemeni"),
    ("Jordania", "🇯🇴", "OrienteMedio", "jordan|jordanian|jordania"),
    ("Líbano", "🇱🇧", "OrienteMedio", "lebanon|lebanese|libano|beirut"),
    ("Israel", "🇮🇱", "OrienteMedio", "israel|israeli|jerusalem|jerusalen"),
    ("Palestina", "🇵🇸", "OrienteMedio", "palestine|palestinian|palestina|gaza|west bank|cisjordania"),
    ("Qatar", "🇶🇦", "OrienteMedio", "qatar|qatari"),
    ("Kuwait", "🇰🇼", "OrienteMedio", "kuwait|kuwaiti"),
    ("Emiratos Árabes", "🇦🇪", "OrienteMedio", "united arab emirates|emiratos|dubai|abu dhabi"),
    ("Omán", "🇴🇲", "OrienteMedio", "oman|omani"),
    ("Afganistán", "🇦🇫", "Asia", "afghanistan|afghan|afganistan|kabul|taliban|talibán"),
    ("Bangladés", "🇧🇩", "Asia", "bangladesh|bangladeshi|dhaka"),
    ("Sri Lanka", "🇱🇰", "Asia", "sri lanka|sri lankan|colombo"),
    ("Nepal", "🇳🇵", "Asia", "nepal|nepali|katmandu|kathmandu"),
    ("Bután", "🇧🇹", "Asia", "bhutan|butan"),
    ("Birmania", "🇲🇲", "Asia", "myanmar|burma|birmania|chin state|kachin|rangoon"),
    ("Laos", "🇱🇦", "Asia", "laos|laotian|vientiane"),
    ("Vietnam", "🇻🇳", "Asia", "vietnam|vietnamese|hanoi|montagnard"),
    ("Camboya", "🇰🇭", "Asia", "cambodia|camboya|phnom penh"),
    ("Indonesia", "🇮🇩", "Asia", "indonesia|indonesian|papua|aceh|java|yakarta|jakarta"),
    ("Malasia", "🇲🇾", "Asia", "malaysia|malasia|kuala lumpur"),
    ("Brunéi", "🇧🇳", "Asia", "brunei"),
    ("Filipinas", "🇵🇭", "Asia", "philippines|filipino|filipinas|mindanao|manila"),
    ("Maldivas", "🇲🇻", "Asia", "maldives|maldivas"),
    ("Uzbekistán", "🇺🇿", "Asia", "uzbekistan|uzbek|tashkent"),
    ("Turkmenistán", "🇹🇲", "Asia", "turkmenistan|turkmen|ashgabat"),
    ("Tayikistán", "🇹🇯", "Asia", "tajikistan|tajik|dushanbe"),
    ("Kirguistán", "🇰🇬", "Asia", "kyrgyzstan|kyrgyz|bishkek"),
    ("Kazajistán", "🇰🇿", "Asia", "kazakhstan|kazakh|astana|almaty"),
    ("Azerbaiyán", "🇦🇿", "Asia", "azerbaijan|azeri|baku"),
    ("Armenia", "🇦🇲", "Europa", "armenia|armenian|nagorno|artsakh|ereván|yerevan"),
    ("Georgia", "🇬🇪", "Europa", "georgia|georgian|tbilisi"),
    ("Rusia", "🇷🇺", "Europa", "russia|russian|rusia|moscow|moscu|kremlin"),
    ("Bielorrusia", "🇧🇾", "Europa", "belarus|belarusian|bielorrusia|minsk"),
    ("Ucrania", "🇺🇦", "Europa", "ukraine|ukrainian|ucrania|kyiv|kiev"),
    ("Sudán", "🇸🇩", "África", "sudan|sudanese|jartum|khartoum|darfur"),
    ("Sudán del Sur", "🇸🇸", "África", "south sudan|sudan del sur|juba"),
    ("Somalia", "🇸🇴", "África", "somalia|somali|mogadishu|al-shabaab|al shabaab"),
    ("Eritrea", "🇪🇷", "África", "eritrea|eritrean|asmara"),
    ("Etiopía", "🇪🇹", "África", "ethiopia|ethiopian|etiopia|addis|tigray|oromia"),
    ("Yibuti", "🇩🇯", "África", "djibouti|yibuti"),
    ("Libia", "🇱🇾", "África", "libya|libyan|libia|tripoli"),
    ("Argelia", "🇩🇿", "África", "algeria|algerian|argelia|kabylie|kabilia"),
    ("Marruecos", "🇲🇦", "África", "morocco|moroccan|marruecos|rabat"),
    ("Túnez", "🇹🇳", "África", "tunisia|tunez|tunis"),
    ("Mauritania", "🇲🇷", "África", "mauritania|nouakchott"),
    ("Malí", "🇲🇱", "África", "mali|malian|bamako|tombuctu|timbuktu"),
    ("Burkina Faso", "🇧🇫", "África", "burkina|ouagadougou"),
    ("Níger", "🇳🇪", "África", "niger|nigerien|niamey"),
    ("Chad", "🇹🇩", "África", "chad|chadian|yamena|djamena"),
    ("Camerún", "🇨🇲", "África", "cameroon|camerun|yaounde"),
    ("Rep. Centroafricana", "🇨🇫", "África", "central african republic|centroafricana|bangui"),
    ("R.D. Congo", "🇨🇩", "África", "democratic republic of congo|dr congo|drc|congo|kinshasa|adf"),
    ("Mozambique", "🇲🇿", "África", "mozambique|cabo delgado|maputo"),
    ("Kenia", "🇰🇪", "África", "kenya|kenyan|kenia|nairobi"),
    ("Tanzania", "🇹🇿", "África", "tanzania|dodoma|zanzibar"),
    ("Uganda", "🇺🇬", "África", "uganda|ugandan|kampala"),
    ("Ruanda", "🇷🇼", "África", "rwanda|ruanda|kigali"),
    ("Burundi", "🇧🇮", "África", "burundi|bujumbura"),
    ("Angola", "🇦🇴", "África", "angola|luanda"),
    ("Zimbabue", "🇿🇼", "África", "zimbabwe|zimbabue|harare"),
    ("Sudáfrica", "🇿🇦", "África", "south africa|sudafrica|johannesburg|pretoria"),
    ("Senegal", "🇸🇳", "África", "senegal|dakar"),
    ("Costa de Marfil", "🇨🇮", "África", "ivory coast|cote d'ivoire|costa de marfil|abidjan"),
    ("Ghana", "🇬🇭", "África", "ghana|accra"),
    ("Togo", "🇹🇬", "África", "togo|lome"),
    ("Benín", "🇧🇯", "África", "benin|cotonou"),
    ("Comoras", "🇰🇲", "África", "comoros|comoras"),
    ("Cuba", "🇨🇺", "América", "cuba|cuban|habana|havana"),
    ("Nicaragua", "🇳🇮", "América", "nicaragua|managua|ortega"),
    ("Venezuela", "🇻🇪", "América", "venezuela|caracas|maduro"),
    ("México", "🇲🇽", "América", "mexico|mexican|michoacan|guerrero|chiapas"),
    ("Colombia", "🇨🇴", "América", "colombia|bogota|cauca|arauca"),
    ("Perú", "🇵🇪", "América", "peru|lima"),
    ("Bolivia", "🇧🇴", "América", "bolivia|la paz"),
    ("Brasil", "🇧🇷", "América", "brazil|brasil|brasilia"),
    ("Argentina", "🇦🇷", "América", "argentina|buenos aires"),
    ("Chile", "🇨🇱", "América", "chile|santiago de chile"),
    ("Estados Unidos", "🇺🇸", "América", "united states|u.s.|usa|estados unidos|washington"),
    ("Canadá", "🇨🇦", "América", "canada|canadian|ottawa"),
    ("España", "🇪🇸", "Europa", "spain|spanish|espana|españa|madrid|barcelona"),
    ("Francia", "🇫🇷", "Europa", "france|french|francia|paris"),
    ("Alemania", "🇩🇪", "Europa", "germany|german|alemania|berlin"),
    ("Reino Unido", "🇬🇧", "Europa", "united kingdom|britain|british|reino unido|london|londres"),
    ("Italia", "🇮🇹", "Europa", "italy|italian|italia|roma|rome"),
    ("Austria", "🇦🇹", "Europa", "austria|austrian|vienna|viena"),
    ("Bosnia", "🇧🇦", "Europa", "bosnia|sarajevo|medjugorje"),
    ("Kosovo", "🇽🇰", "Europa", "kosovo|pristina"),
    ("Grecia", "🇬🇷", "Europa", "greece|greek|grecia|atenas|athens"),
    ("Chipre", "🇨🇾", "Europa", "cyprus|chipre|nicosia"),
    ("Australia", "🇦🇺", "Oceanía", "australia|australian|canberra|sydney"),
]

PAISES_COMPILADO = [(n, b, r, re.compile(r"\b(?:" + a + r")\b", re.I))
                    for n, b, r, a in PAISES]

# --------------------------------------------------------------------------
# gravedad
# --------------------------------------------------------------------------

GRAVE_ALTA = re.compile(
    r"\b(kill|killed|killing|murder|murdered|slain|massacre|dead|death|died|"
    r"execut|behead|abduct|kidnap|hostage|rape|torture|burn(?:ed|t)? alive|"
    r"asesin|matan|muert|masacre|secuestr|degoll|ejecut|tortur|violac)\w*", re.I)

GRAVE_MEDIA = re.compile(
    r"\b(arrest|detain|jail|imprison|sentenc|convict|charged|attack|assault|"
    r"raid|demolish|destroy|burn|vandal|desecrat|expel|evict|ban|fine|blasphemy|"
    r"deten|arrest|encarcel|conden|cárcel|carcel|ataque|atacad|asalt|redada|"
    r"derrib|destruy|incend|vandal|profan|expuls|desahuci|prohib|multa|blasfemia)\w*",
    re.I)

EMOJI_GRAVEDAD = {"alta": "🚨", "media": "⚠️", "baja": "📄"}

# --------------------------------------------------------------------------
# relevancia (sin IA hace falta ser mas estricto)
# --------------------------------------------------------------------------

TERMINO_PERSECUCION = re.compile(
    r"\b(persecut|persegu|persecu|martyr|martir|mártir|kill|murder|assassin|"
    r"slain|behead|abduct|kidnap|hostage|arrest|detain|jail|imprison|sentenc|"
    r"convict|blasphemy|apostasy|attack|assault|raid|torture|threat|mob|"
    r"violence|violent|impunity|harass|discriminat|expel|evict|burn|burnt|"
    r"beaten|desecrat|vandal|demolish|destroy|banned|restrict|"
    r"religious freedom|libertad religiosa|cristianofobia|asesin|muert|"
    r"secuestr|deten|detien|detuv|apres|encarcel|conden|blasfemia|apostas|"
    r"ataque|atac|amenaz|discrimin|profan|destruy|derrib|incend|quem|demoli|"
    r"violenc|agred|golpe|paliza|impunidad|expuls|prohib|restring|persig|"
    r"mat[oó]|matan|matar|mataron|matando|asalt|redada|allanamiento)\w*", re.I)

CONTEXTO_CRISTIANO = re.compile(
    r"\b(christian|church|churches|pastor|priest|bishop|nun|monk|missionar|"
    r"believer|convert|congregation|parish|chapel|cathedral|catholic|"
    r"evangelical|protestant|bible|gospel|worship|cristian|iglesia|iglesias|"
    r"sacerdote|obispo|monja|religiosa|misioner|creyent|converso|feligres|"
    r"parroquia|capilla|catedral|catolic|católic|evangelic|evangélic|"
    r"protestant|biblia|culto|fiel|fieles)\w*", re.I)


# hechos concretos: si aparece uno de estos, la noticia entra aunque el resto
# del texto parezca institucional
TERMINO_FUERTE = re.compile(
    r"\b(killed|killing|murder|assassinat|massacre|slain|behead|shot dead|"
    r"burnt alive|burned alive|abduct|kidnap|hostage|arrest|detain|jailed|"
    r"imprison|sentenc|convict|blasphemy|apostasy|death row|执行|"
    r"demolish|bulldoz|torched|desecrat|martyr|"
    r"asesin|matar|mataron|masacre|degoll|secuestr|deten|encarcel|conden|"
    r"blasfemia|apostas|derrib|demol|profan|martir|mártir|incendi)\w*", re.I)

# temas que NO son noticia de persecucion: si aparecen y no hay ningun hecho
# concreto, se descarta (campanas, actos, nombramientos, liturgia, agenda)
VETO = re.compile(
    r"\b(donat|donate|fundrais|fundraising|appeal for funds|legacy|bequest|"
    r"gift aid|webinar|podcast|newsletter|subscribe|magazine|"
    r"prayer request|please pray|prayer diary|devotional|reflection|"
    r"appoint|appointed|nominat|ordain|consecrat|installed as|enthron|"
    r"liturg|homily|sermon|retreat|pilgrimage|novena|festival|"
    r"conference|congress|synod|assembly|webcast|anniversary of the founding|"
    r"obituary|funeral of|dies at|passed away|"
    # ensayos, series de opinion y entrevistas: no son noticia
    r"part \d+ of|of the series|this series|fellow|essay|op-ed|opinion|"
    r"commentary|column|interview with|book review|explainer|"
    r"parte \d+ de|de la serie|esta serie|ensayo|opini[oó]n|columna|"
    r"entrevista con|rese[nñ]a|"
    r"donativ|donaci[oó]n|colecta|campa[nñ]a de|legado|"
    r"b[oó]letin|bolet[ií]n|podcast|seminario web|revista|"
    r"petici[oó]n de oraci[oó]n|oremos|oraci[oó]n del d[ií]a|reflexi[oó]n|"
    r"nombra|nombrado|design|ordena|ordenaci[oó]n|consagra|toma de posesi[oó]n|"
    r"liturgia|homil[ií]a|serm[oó]n|retiro|peregrinaci[oó]n|novena|"
    r"congreso|s[ií]nodo|asamblea|aniversario de la fundaci[oó]n|"
    r"obituario|funeral de|fallece|falleci[oó])\w*", re.I)


def es_relevante(texto, fuente_especializada=False, titulo=""):
    """Sin IA hay que ser exigente. Reglas:

    1. Tiene que haber contexto cristiano (iglesia, pastor, converso...).
    2. Tiene que haber un termino de persecucion.
    3. Si el texto es de agenda institucional (campanas, nombramientos,
       liturgia, podcasts) se descarta salvo que haya un hecho concreto
       (muertos, detenidos, condenas, demoliciones...).
    4. En fuentes generalistas, ademas, el titular tiene que hablar de ello:
       no vale que la palabra 'iglesia' aparezca de refilon en el cuerpo.
    """
    titulo = titulo or texto[:160]
    hay_contexto = bool(CONTEXTO_CRISTIANO.search(texto))
    hay_termino = bool(TERMINO_PERSECUCION.search(texto))
    hay_fuerte = bool(TERMINO_FUERTE.search(texto))

    if not (hay_contexto and hay_termino):
        return False
    if VETO.search(texto) and not hay_fuerte:
        return False
    if not fuente_especializada:
        # el titular debe llevar el contexto cristiano y algun termino
        if not (CONTEXTO_CRISTIANO.search(titulo) and TERMINO_PERSECUCION.search(titulo)):
            return False
    else:
        # en especializadas basta con que el titular mencione una de las dos
        if not (CONTEXTO_CRISTIANO.search(titulo) or TERMINO_PERSECUCION.search(titulo)):
            return False
    return True


# --------------------------------------------------------------------------
# analisis
# --------------------------------------------------------------------------

def detectar_pais(titulo, cuerpo=""):
    """Devuelve (nombre_es, bandera, region). El titulo pesa el triple."""
    mejor, puntos_mejor = None, 0
    for nombre, bandera, region, patron in PAISES_COMPILADO:
        p = len(patron.findall(titulo)) * 3 + len(patron.findall(cuerpo))
        if p > puntos_mejor:
            mejor, puntos_mejor = (nombre, bandera, region), p
    return mejor or ("Internacional", "🌍", "Mundo")


def detectar_gravedad(texto):
    if GRAVE_ALTA.search(texto):
        return "alta"
    if GRAVE_MEDIA.search(texto):
        return "media"
    return "baja"


def limpiar(texto):
    texto = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", texto or "", flags=re.S | re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = html.unescape(texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    # colas tipicas de los RSS
    texto = re.sub(r"(?:The post .*? appeared first on .*?\.?$"
                   r"|Read more.*$|Continue reading.*$|Leer m[aá]s.*$)", "",
                   texto, flags=re.I).strip()
    return texto


def resumir(texto, max_frases=3, max_chars=480):
    """Primeras frases completas del resumen del RSS."""
    texto = limpiar(texto)
    if not texto:
        return ""
    frases = re.split(r"(?<=[.!?])\s+", texto)
    salida = ""
    for f in frases[:max_frases]:
        if len(salida) + len(f) + 1 > max_chars:
            break
        salida = (salida + " " + f).strip()
    if not salida:
        salida = texto[:max_chars].rsplit(" ", 1)[0] + "..."
    return salida


def titular_limpio(titulo):
    t = limpiar(titulo)
    t = re.sub(r"\s*[|–-]\s*(Morning Star News|International Christian Concern|"
               r"Open Doors.*|Release International|Barnabas Aid|ACI Prensa)\s*$", "", t, flags=re.I)
    return t.rstrip(".")


def hashtags(pais, region, gravedad, texto, fijo="#IglesiaPerseguida"):
    def limpio(s):
        s = (s.replace("á", "a").replace("é", "e").replace("í", "i")
              .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
              .replace("Á", "A").replace("É", "E").replace("Í", "I")
              .replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N"))
        return "#" + re.sub(r"[^\w]", "", s)

    tags = []
    if pais != "Internacional":
        tags.append(limpio(pais))
    tags.append(limpio(region))

    temas = [
        (r"\b(kill|murder|asesin|matan|muert)\w*", "#Asesinato"),
        (r"\b(abduct|kidnap|secuestr)\w*", "#Secuestro"),
        (r"\b(arrest|detain|jail|imprison|deten|encarcel)\w*", "#Detenciones"),
        (r"\b(sentenc|convict|court|trial|conden|juici|tribunal)\w*", "#Juicio"),
        (r"\b(church|chapel|cathedral|iglesia|capilla|templo)\w*", "#Templos"),
        (r"\b(blasphemy|apostasy|blasfemia|apostas)\w*", "#Blasfemia"),
        (r"\b(law|bill|legislat|ley|legislac)\w*", "#Leyes"),
        (r"\b(report|informe|survey|estudio)\w*", "#Informe"),
    ]
    for patron, tag in temas:
        if re.search(patron, texto, re.I) and tag not in tags:
            tags.append(tag)
        if len(tags) >= 4:
            break
    if fijo and fijo not in tags:
        tags.append(fijo)
    return tags


# --------------------------------------------------------------------------
# traduccion gratuita (MyMemory: sin clave, sin tarjeta)
# --------------------------------------------------------------------------

_cache = None


def _cargar_cache():
    global _cache
    if _cache is None:
        try:
            _cache = json.load(open(CACHE_TRAD, encoding="utf-8"))
        except Exception:
            _cache = {}
    return _cache


def _guardar_cache():
    try:
        c = _cargar_cache()
        if len(c) > 2000:
            c = dict(list(c.items())[-2000:])
            globals()["_cache"] = c
        json.dump(c, open(CACHE_TRAD, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass


def _trocear(texto, limite=450):
    """MyMemory acepta ~500 caracteres por peticion."""
    frases = re.split(r"(?<=[.!?])\s+", texto)
    trozos, actual = [], ""
    for f in frases:
        if len(f) > limite:
            if actual:
                trozos.append(actual)
                actual = ""
            for i in range(0, len(f), limite):
                trozos.append(f[i:i + limite])
            continue
        if len(actual) + len(f) + 1 > limite:
            trozos.append(actual)
            actual = f
        else:
            actual = (actual + " " + f).strip()
    if actual:
        trozos.append(actual)
    return trozos


def traducir(texto, origen="en", destino="es", email=""):
    """Traduce con MyMemory. Gratis y sin clave (5.000 caracteres al dia, o
    50.000 si pasas un email). Si falla, devuelve el texto original."""
    texto = (texto or "").strip()
    if not texto or origen == destino:
        return texto
    cache = _cargar_cache()
    clave = f"{origen}|{destino}|{texto}"
    if clave in cache:
        return cache[clave]

    partes = []
    for trozo in _trocear(texto):
        try:
            params = {"q": trozo, "langpair": f"{origen}|{destino}"}
            if email:
                params["de"] = email
            r = requests.get("https://api.mymemory.translated.net/get",
                             params=params, timeout=25).json()
            t = (r.get("responseData") or {}).get("translatedText", "")
            estado = r.get("responseStatus")
            if not t or estado not in (200, "200"):
                return texto           # cuota agotada u otro problema
            if "MYMEMORY WARNING" in t.upper() or "QUOTA" in t.upper():
                return texto
            partes.append(html.unescape(t))
            time.sleep(0.4)            # no saturar el servicio gratuito
        except Exception:
            return texto
    resultado = " ".join(partes).strip()
    if resultado:
        cache[clave] = resultado
        _guardar_cache()
    return resultado or texto


# --------------------------------------------------------------------------
# construccion del post
# --------------------------------------------------------------------------

def esc(t):
    return html.escape(t or "", quote=False)


def construir_post(titulo, resumen_bruto, enlace, fuente, cfg,
                   idioma_fuente="en", media=None):
    """Devuelve el texto HTML listo para Telegram, sin usar ninguna IA de pago."""
    titulo = titular_limpio(titulo)
    resumen = resumir(resumen_bruto)
    texto_analisis = f"{titulo} {resumen}"

    pais, bandera, region = detectar_pais(titulo, resumen)
    gravedad = detectar_gravedad(texto_analisis)
    emoji = EMOJI_GRAVEDAD[gravedad]

    traducir_on = cfg.get("traducir", True) and idioma_fuente != "es"
    email = cfg.get("email_traductor", "")
    if traducir_on:
        titulo_es = traducir(titulo, idioma_fuente, "es", email)
        resumen_es = traducir(resumen, idioma_fuente, "es", email)
    else:
        titulo_es, resumen_es = titulo, resumen

    lineas = [f"{emoji} <b>{esc(pais).upper()}</b> {bandera}",
              "",
              f"<b>{esc(titulo_es)}</b>",
              "",
              esc(resumen_es)]

    # original debajo, solo si de verdad hemos traducido
    if cfg.get("publicar_ingles", True) and traducir_on and titulo_es != titulo:
        etiqueta = "🇬🇧" if idioma_fuente == "en" else "🌐"
        lineas += ["", "➖➖➖",
                   f"{etiqueta} <b>{esc(titulo)}</b>", "",
                   f"<i>{esc(resumen)}</i>"]

    lineas += [""]
    if media and media.get("tipo") == "youtube":
        lineas.append(f'🎥 <a href="{esc(media["url"])}">Vídeo</a>')
    lineas += [f'📎 <a href="{esc(enlace)}">Fuente: {esc(fuente)}</a>',
               " ".join(hashtags(pais, region, gravedad, texto_analisis,
                                 cfg.get("hashtag_fijo", "#IglesiaPerseguida")))]

    firma = cfg.get("firma", "").strip()
    if firma:
        lineas += ["", esc(firma)]
    return "\n".join(lineas)


if __name__ == "__main__":
    demo = construir_post(
        "Gunmen kill 30 Christians in attack on two villages in Plateau state",
        "<p>Armed men attacked two predominantly Christian villages in Nigeria's "
        "Plateau state on Sunday morning, killing at least 30 people and burning "
        "about 20 homes, local officials said. It was the third such attack in the "
        "area this month. Residents said no security forces arrived.</p>",
        "https://morningstarnews.org/ejemplo", "Morning Star News",
        {"traducir": False, "publicar_ingles": True}, "en")
    print(demo)
