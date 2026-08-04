# Que funcione sin tu ordenador, gratis

Dos opciones que no cuestan nada. La primera no pide ni tarjeta.

---

## Opción A · GitHub Actions (recomendada)

GitHub ejecuta tu bot cada 30 minutos en sus servidores. No hay servidor que mantener, no piden tarjeta, y no hay nada que se te pueda quedar encendido.

**Cómo funciona:** cada media hora GitHub arranca una máquina, el bot atiende los botones que hayas pulsado, revisa las webs, te manda los borradores nuevos, guarda el estado y se apaga.

**La única diferencia con tenerlo en tu ordenador:** cuando pulsas ✅ Publicar, el post sale en la siguiente pasada, es decir hasta 30 minutos después. Telegram guarda tu pulsación 24 horas, así que no se pierde nada. Para un canal que miras una o dos veces al día, es irrelevante.

### Pasos

**1. Crea una cuenta en [github.com](https://github.com)** si no la tienes.

**2. Crea un repositorio.** Botón **+** → *New repository*.

- Nombre: `canal-persecucion`
- **Privado** si no quieres que se vea el código (tienes 2.000 minutos gratis al mes; a 30 min de intervalo gastarás unos 1.400)
- **Público** si te da igual: minutos ilimitados. Tu token **no** va en el código, así que es seguro.

**3. Sube los ficheros.** En el repo vacío → *uploading an existing file* → arrastra todo lo de esta carpeta **menos `config.json`** (el `.gitignore` ya lo excluye, pero al arrastrar a mano tienes que fijarte tú). Sube también la carpeta `.github`.

Ficheros que deben ir: `bot.py`, `redaccion.py`, `fuentes.json`, `requirements.txt`, `.github/workflows/bot.yml`, `.gitignore`.
Fichero que **NO** debe ir: `config.json` (tiene tu token).

**4. Mete los secretos.** En el repo → *Settings* → *Secrets and variables* → *Actions* → **New repository secret**. Crea tres:

| Nombre | Valor |
|---|---|
| `TELEGRAM_BOT_TOKEN` | tu token de BotFather |
| `CHANNEL_ID` | `@the_persecuted_church` |
| `ADMIN_CHAT_ID` | `7633188915` |

Opcional: `EMAIL_TRADUCTOR` con tu email, para ampliar la cuota del traductor a 50.000 caracteres/día.

**5. Enciéndelo.** Pestaña **Actions** → si te pide confirmación, *I understand my workflows, go ahead and enable them* → elige *Canal de la Iglesia perseguida* → **Run workflow**.

Esa primera ejecución marca el histórico como visto y no publica nada. A partir de ahí va sola cada 30 minutos.

**6. Apaga el bot de tu ordenador.** Importante: no pueden funcionar los dos a la vez, porque se roban los mensajes entre ellos. Cierra la ventana de `ARRANCAR.bat` y usa solo uno de los dos.

### Cosas a vigilar con el tiempo

- **GitHub apaga los cron tras ~60 días sin actividad en el repo.** Te avisa por correo. Para reactivarlo: entra en *Actions* y pulsa *Enable workflow*, o haz cualquier commit.
- **Minutos gratis (solo si el repo es privado):** 2.000 al mes. A 30 minutos de intervalo son unas 1.400-1.700, así que entra justo. Míralo de vez en cuando en *Settings → Billing → Plans and usage*. Si se acerca al límite: pon el cron cada 45 minutos (`*/45`) o haz el repositorio público (minutos ilimitados, y tu token seguiría a salvo en Secrets).
- **GitHub retrasa o se salta ejecuciones** cuando su cola va cargada, sobre todo en punto en hora. No es un fallo: la siguiente pasada recoge lo pendiente.
- **Nunca subas `config.json`.** Está en `.gitignore`, pero si algún día lo fuerzas, tu token quedaría publicado. Si pasara: @BotFather → `/revoke`.

### Detalles útiles

- **Ver qué ha hecho**: pestaña *Actions* → cada ejecución tiene su registro.
- **Forzar una pasada ya**: *Actions* → *Run workflow*.
- **Cambiar la frecuencia**: edita `.github/workflows/bot.yml`, línea del `cron`. `*/30` = cada 30 min, `0 */2` = cada 2 horas.
- **Ojo con los repos privados recién creados**: a veces GitHub no registra el cron hasta que haces algún commit. Si a las dos horas no se ha ejecutado sola, edita cualquier fichero (por ejemplo añade una línea a este documento), guarda, y ya arranca.
- **Consumo**: unas 24 horas de máquina al mes, dentro de los 2.000 minutos gratuitos.

---

## Opción B · Oracle Cloud Always Free

Una máquina virtual gratis para siempre (2 OCPU ARM y 12 GB de RAM desde junio de 2026, antes eran 4 y 24). Ahí el bot corre igual que en tu ordenador, con las pulsaciones instantáneas.

**A favor:** es un servidor de verdad, sin retrasos, y sobra potencia.
**En contra:** piden tarjeta para verificar identidad (no cobran), el registro a veces rechaza cuentas, y muchas regiones están sin capacidad ARM disponible. Además hay que saber manejarse mínimamente con Linux y `systemd`.

Si te apetece esta vía, dímelo y te preparo los comandos exactos y el servicio de arranque automático.

---

## Comparativa rápida

| | Tu ordenador | GitHub Actions | Oracle Cloud |
|---|---|---|---|
| Coste | 0 € | 0 € | 0 € |
| Tarjeta | no | **no** | sí (verificación) |
| Funciona apagado el portátil | no | **sí** | **sí** |
| Retraso al pulsar ✅ | ninguno | hasta 30 min | ninguno |
| Dificultad | ya está hecho | media (subir ficheros y 3 secretos) | alta |

Para tu uso —mirarlo una o dos veces al día— **la opción A es la más sensata**.
