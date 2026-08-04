# Canal de Telegram sobre la persecución del cristiano

Bot que vigila las agencias más fiables sobre cristianos perseguidos **cada 3 minutos**, coge **solo noticias recién publicadas**, recupera **la foto o el vídeo que ha subido el propio medio**, redacta el post en **español con la traducción al inglés debajo**, te lo manda a ti en privado como borrador con botones, y lo publica en el canal **solo cuando tú le das a Publicar**.

---

# PROCEDIMIENTO

Son 4 pasos. Solo el paso 2 se hace a mano; el resto lo lleva un asistente.

## Paso 1 · Ten a mano el token

El que te dio @BotFather (el nuevo, después de revocar el anterior). Es la cadena larga `8123456789:AAF...`.

Si lo has perdido: @BotFather → `/mybots` → tu bot → **API Token**.

## Paso 2 · Hacer al bot administrador del canal

⚠️ **Desde el móvil o desde Telegram Desktop. En Telegram Web NO funciona** — su buscador de administradores no encuentra bots, por eso te salía "No Results". Tampoco sirve añadirlo como suscriptor: en un canal los bots solo pueden entrar como administradores.

**Móvil:**

1. Abre el canal.
2. Toca el **nombre del canal** en la barra de arriba.
3. **✏️ Editar** (arriba a la derecha).
4. **Administradores** → **Añadir administrador**.
5. Escribe `actualizador` en el buscador. No hace falta el nombre entero ni la @.
6. Toca el bot → deja **Publicar mensajes** activado → **✓**.

**Telegram Desktop** ([desktop.telegram.org](https://desktop.telegram.org), es la app de escritorio, no la web):
canal → ⋮ → **Gestionar canal** → **Administradores** → **Añadir administrador** → mismo buscador.

> **Por qué esto no se puede automatizar:** la Bot API tiene un método `promoteChatMember`, pero solo funciona si el bot **ya** es administrador. Un bot no puede promocionarse a sí mismo. Es el único paso manual de todo el sistema.

## Paso 3 · Lanzar el asistente

Doble clic en **`CONFIGURAR.bat`** (o en una terminal: `python configurar.py`).

El asistente hace todo lo demás y te va diciendo qué falta en cada momento:

- instala las dependencias
- valida el token contra Telegram
- comprueba que encuentra el canal
- **verifica que el bot es administrador y puede publicar**; si no lo es, te dice cómo y espera a que lo hagas
- **detecta tu chat id solo**: te pide que le mandes `/start` al bot y lo captura
- configura la traducción gratuita al español
- escribe `config.json`
- publica un mensaje de prueba en el canal

**Todo esto es gratis. No hay ninguna API de pago, ni clave, ni tarjeta.**

Si algo falla, el asistente te dice exactamente qué y puedes repetirlo las veces que haga falta.

## Paso 4 · Arrancar

Doble clic en **`ARRANCAR.bat`** (o `python bot.py`).

Deja esa ventana abierta: mientras esté abierta, el bot funciona.

**En el primer arranque no publica nada del histórico.** Marca lo que ya existe y, a partir de ahí, te llega cada noticia nueva pocos minutos después de que la fuente la publique.

---

# CÓMO ES EL DÍA A DÍA

Te llega un borrador a tu chat privado con el bot:

```
📝 BORRADOR · Morning Star News · hace 4 min · 🖼
➖➖➖

🚨 NIGERIA 🇳🇬

Al menos 30 muertos en un ataque contra dos aldeas cristianas

Hombres armados asaltaron el domingo dos aldeas del estado de Plateau
durante los cultos matinales. Las autoridades confirman 30 fallecidos
y una veintena de casas incendiadas. Es el tercer ataque en un mes.

➖➖➖
🇬🇧 At least 30 killed in attack on two Christian villages

Gunmen raided two villages in Plateau State on Sunday during morning
services. Local authorities confirm 30 dead...

📎 Fuente: International Christian Concern
#Nigeria #Africa #Ataque #IglesiaPerseguida
```

Con la foto del artículo encima y tres botones: **✅ Publicar** · **✏️ Editar** · **🗑 Descartar**.

La cabecera te dice la fuente, **hace cuánto se publicó** y si trae 🖼 foto, 🎬 vídeo, 🎥 YouTube o 📄 nada.

## Uso realista: una o dos veces al día

No hace falta estar pendiente del móvil. El ritmo normal es:

1. Enciendes el ordenador y abres `ARRANCAR.bat` (o lo dejas en el arranque automático de Windows).
2. El bot recupera **todo lo publicado en las últimas 48 h** que no hayas visto ya y te lo deja en el chat privado como borradores.
3. Cuando te venga bien —desayuno, noche, lo que sea— abres ese chat y vas dando ✅ o 🗑 a lo que haya. Cinco minutos.
4. Cierras la ventana cuando quieras. **Lo que dejes sin decidir sigue ahí**: sus botones funcionan la próxima vez que arranques, hasta 14 días después.

O sea: el bot trabaja cuando el ordenador está encendido, y tú decides cuando te apetece. Lo único que no ocurre con el ordenador apagado es la *recogida* de noticias, y para eso está la ventana de 48 h: aunque solo lo enciendas por la noche, no se te escapa casi nada.

**Comandos** (escríbeselos al bot por privado):

| Comando | Qué hace |
|---|---|
| `/chequear` | busca noticias ahora mismo |
| `/pendientes` | lista los borradores que tienes sin decidir |
| `/estado` | fuentes activas, borradores pendientes, configuración |
| `/pausa` · `/reanudar` | parar y reanudar la búsqueda |
| `/cancelar` | cancelar una edición a medias |

---

# QUÉ HAY EN LA CARPETA

| Fichero | Para qué |
|---|---|
| `CONFIGURAR.bat` | asistente de configuración (doble clic) |
| `ARRANCAR.bat` | pone el bot en marcha (doble clic) |
| `DIAGNOSTICO.bat` | genera `diagnostico.txt` si algo no arranca |
| `bot.py` | el bot |
| `redaccion.py` | redacta los posts: país, bandera, gravedad, resumen, hashtags, traducción |
| `configurar.py` | el asistente |
| `traducciones.json` | caché de traducciones, para no repetir peticiones |
| `probar_conexion.py` | diagnóstico: token, permisos, publicación de prueba |
| `comprobar_fuentes.py` | comprueba qué webs responden |
| `fuentes.json` | la lista de webs |
| `config.json` | tus datos (lo crea el asistente) |
| `estado.json` | qué noticias ya ha visto |
| `bot.log` | registro de lo que va haciendo |

---

# CÓMO REDACTA SIN PAGAR NADA

No hay ninguna IA de pago. `redaccion.py` hace el trabajo con reglas:

- **País y bandera** — reconoce más de 100 países y también regiones y ciudades (Plateau, Kaduna, Henan, Minya, Cabo Delgado...). El título pesa el triple que el cuerpo.
- **Gravedad** — 🚨 si hay muertos, secuestros o ejecuciones; ⚠️ si hay detenciones, condenas, ataques o demoliciones; 📄 si es un informe.
- **Resumen** — las primeras frases completas del resumen del RSS, limpias de HTML y de coletillas tipo *"The post ... appeared first on ..."*.
- **Hashtags** — país, región y hasta dos temas detectados (#Asesinato, #Secuestro, #Detenciones, #Juicio, #Templos, #Blasfemia, #Leyes, #Informe) más el fijo.
- **Traducción al español** — vía MyMemory: gratis, sin clave y sin tarjeta. 5.000 caracteres al día, o 50.000 si diste un email. Con caché para no traducir dos veces lo mismo. **Si la cuota se agota el bot no se para**: publica en el idioma original.
- **Filtro de relevancia** — exige a la vez un término de persecución (asesinato, detención, blasfemia, ataque, demolición...) **y** un contexto cristiano (iglesia, pastor, sacerdote, converso...). En las fuentes 100 % especializadas basta con uno de los dos. Así una campaña de donativos o un nombramiento episcopal no llegan al canal.

Y como cada post pasa por tu botón de ✅ antes de publicarse, cualquier cosa que la regla no acierte la corriges con ✏️ o la tiras con 🗑.

---

# INMEDIATEZ Y MULTIMEDIA

**Cuándo llega.** Sondeo cada 3 minutos con ETag / If-Modified-Since: solo descarga si hay algo nuevo. Desde que la fuente publica hasta que tienes el borrador pasan minutos. Ese es el límite real, y no es el bot: es que Morning Star o ICC publican cuando publican.

**Nada viejo.** Todo lo de más de 12 horas (`max_antiguedad_horas`) se descarta sin mirarlo.

**Fotos y vídeos.** Para cada noticia busca, en este orden:

1. `media:content`, `media:thumbnail` o `enclosure` del RSS
2. la imagen incrustada en el cuerpo del artículo
3. si no hay nada, abre el artículo y lee `og:video`, `og:image` y los YouTube incrustados

Y publica así:

- **Foto** → vista previa grande encima del texto. Este truco esquiva el límite de 1024 caracteres de los pies de foto, así que cabe el post entero en español e inglés.
- **Vídeo mp4** → `sendVideo` con el texto de pie.
- **YouTube** → enlace 🎥 que Telegram reproduce dentro de la app.
- **Sin media** → texto con vista previa del enlace.

Siempre es la imagen que ha publicado la propia fuente, no una de archivo.

---

# FUENTES

| Fuente | Por qué está |
|---|---|
| Morning Star News | Agencia especializada con periodistas locales. La más rápida y precisa en hechos concretos. |
| International Christian Concern | Cobertura diaria y amplia, red de contactos en Asia y África. |
| Open Doors UK | Investigación propia. Autores de la Lista Mundial de la Persecución. |
| Release International | Socios locales en más de 25 países. |
| Christian Solidarity Worldwide | Documentación jurídica y de DDHH, citada por la ONU. |
| Barnabas Aid | Oriente Medio, África y Asia. |
| Voice of the Martyrs | Testimonios directos de presos y sus familias. |
| Aid to the Church in Need | Fundación pontificia, informe bienal de libertad religiosa. |
| ACI Prensa | Única en español; generalista, se filtra fuerte. |

Fuera agregadores y medios generalistas: son los que meten ruido y noticias de segunda mano.

Para comprobar cuáles responden: `python comprobar_fuentes.py`. Para desactivar las que fallen: `python comprobar_fuentes.py --desactivar`. Para añadir una nueva, edita `fuentes.json` copiando el formato de las que hay.

---

# SI ALGO FALLA

| Síntoma | Solución |
|---|---|
| `python no se reconoce` | Instala Python desde python.org marcando **Add python.exe to PATH** |
| "No he podido publicar" al pulsar ✅ | El bot no es administrador o le falta *Publicar mensajes*. Paso 2 |
| El buscador de administradores no encuentra el bot | Estás en Telegram Web. Móvil o Telegram Desktop |
| No llegan borradores | `/estado` para ver si está pausado; `/chequear` para forzar; mira `bot.log` |
| Llegan noticias que no vienen a cuento | Pon `"filtrar": true` a esa fuente en `fuentes.json`, o desactívala |
| Los posts salen en inglés | Se agotó la cuota diaria del traductor (vuelve al día siguiente) o `"traducir": false` en `config.json` |
| Se repiten noticias | Borra `estado.json` solo si quieres reiniciar el historial (volverá a proponerte cosas ya vistas) |
| Cualquier otra cosa | Mira las últimas líneas de `bot.log`: ahí está el error real |

**Los borradores pendientes sobreviven a los reinicios.** Puedes cerrar la ventana con veinte borradores sin decidir: siguen guardados y sus botones funcionan igual cuando vuelvas a arrancar. Se guardan 14 días (`dias_guardar_borradores`).

---

# QUE FUNCIONE SIN TU ORDENADOR ENCENDIDO

Mientras `ARRANCAR.bat` esté abierto, el bot funciona. Para que corra siempre **sin pagar nada**, mira **`HOSTING-GRATIS.md`**: GitHub Actions lo ejecuta cada 30 minutos en sus servidores, sin tarjeta y sin servidor que mantener. Ya están preparados el modo `--una-vez` y el workflow en `.github/workflows/bot.yml`.

Importante: **no tengas el bot corriendo en dos sitios a la vez** (tu ordenador y GitHub), porque se roban los mensajes entre ellos. Uno u otro.

---

# AVISOS

- **El token es la contraseña del bot.** Vive solo en `config.json`. Si se filtra, @BotFather → `/revoke`.
- **Derechos**: titular + resumen breve + enlace a la fuente es la práctica estándar. No copies artículos enteros y cita siempre a la organización.
- **Verificación**: en este tema circulan muchas cifras infladas. Las fuentes son serias, pero el botón de aprobar existe justo para eso: si algo suena raro, contrástalo antes.
- **Sensibilidad**: los nombres de conversos en países cerrados a veces son seudónimos. No añadas datos que la fuente ha ocultado a propósito.
