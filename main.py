import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram import html
from aiogram import Router
from dotenv import load_dotenv
import requests
import time

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CREATOR_ID = int(os.getenv("CREATOR_ID"))
LOG_FILE = "bot.log"
ALLOWED_USERS_FILE = "allowed_users.txt"
HYDRAX_API_ID = os.getenv("HYDRAX_API_ID")

# Diccionario de idiomas (solo español e inglés)
LANGS = {
    "es": {
        "welcome": "¡Bienvenido! Usa /ayuda para ver cómo funciona el bot.",
        "help": "Este bot te permite subir videos a Telegram o Hydrax. Usa /server para elegir el servidor y envía tu archivo de video.",
        "setlang": "Selecciona el idioma:",
        "lang_es": "Español 🇪🇸",
        "lang_en": "English 🇺🇸",
        "lang_changed": "Idioma cambiado exitosamente.",
        "not_allowed": "No tienes permiso para usar el bot.",
        "add_success": "Usuario añadido correctamente.",
        "remove_success": "Usuario eliminado correctamente.",
        "already_allowed": "El usuario ya está autorizado.",
        "not_in_list": "El usuario no está en la lista.",
        "log_send": "Aquí tienes el archivo de registro.",
        "ads_intro": "¿Cuál será el anuncio? Envía el mensaje.",
        "ads_add_more": "¿Deseas añadir más información?",
        "ads_preview": "Previsualización del anuncio:",
        "ads_send_confirm": "¿Deseas enviar el anuncio?",
        "ads_sent": "Anuncio enviado a todos los usuarios.",
        "ads_summary": "Resumen: Enviados: {sent}, Bloqueados: {blocked}, Fallidos: {failed}",
        "ping": "⏱️ Latencia: {ms} ms.",
        "server_select": "¿Qué servidor deseas usar?",
        "server_tg": "🚀Telegram",
        "server_hydrax": "🦎Hydrax",
        "server_selected": "Servidor seleccionado: {server}",
        "hapi_ask": "Envía tu nueva API de Hydrax.",
        "hapi_confirm": "¿Es correcta esta API?",
        "hapi_ok": "API de Hydrax actualizada.",
        "hapi_cancel": "Operación cancelada.",
        "cancelled": "Operación cancelada.",
        "uploading": "Subiendo archivo...",
        "upload_complete": "Subida completada.",
        "upload_error": "Error al subir el archivo.",
    },
    "en": {
        "welcome": "Welcome! Use /ayuda to see how the bot works.",
        "help": "This bot lets you upload videos to Telegram or Hydrax. Use /server to select the server and send your video file.",
        "setlang": "Select language:",
        "lang_es": "Español 🇪🇸",
        "lang_en": "English 🇺🇸",
        "lang_changed": "Language changed successfully.",
        "not_allowed": "You are not allowed to use this bot.",
        "add_success": "User added successfully.",
        "remove_success": "User removed successfully.",
        "already_allowed": "User is already authorized.",
        "not_in_list": "User not found in allowed list.",
        "log_send": "Here is the log file.",
        "ads_intro": "What will be the announcement? Send the message.",
        "ads_add_more": "Do you want to add more info?",
        "ads_preview": "Announcement preview:",
        "ads_send_confirm": "Send the announcement?",
        "ads_sent": "Announcement sent to all users.",
        "ads_summary": "Summary: Sent: {sent}, Blocked: {blocked}, Failed: {failed}",
        "ping": "⏱️ Latency: {ms} ms.",
        "server_select": "Which server do you want?",
        "server_tg": "🚀Telegram",
        "server_hydrax": "🦎Hydrax",
        "server_selected": "Selected server: {server}",
        "hapi_ask": "Send your new Hydrax API.",
        "hapi_confirm": "Is this API correct?",
        "hapi_ok": "Hydrax API updated.",
        "hapi_cancel": "Operation cancelled.",
        "cancelled": "Operation cancelled.",
        "uploading": "Uploading file...",
        "upload_complete": "Upload completed.",
        "upload_error": "Error uploading file.",
    }
}

def get_user_lang(user_id):
    # Simple local file-based language storage, per user
    lang_file = f"lang_{user_id}.txt"
    if os.path.exists(lang_file):
        with open(lang_file, "r") as f:
            return f.read().strip()
    return "en" if user_id != CREATOR_ID else "es"

def set_user_lang(user_id, lang):
    lang_file = f"lang_{user_id}.txt"
    with open(lang_file, "w") as f:
        f.write(lang)

def get_text(key, user_id):
    lang = get_user_lang(user_id)
    return LANGS[lang][key]

def log_event(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {text}\n")

def is_allowed(user_id):
    with open(ALLOWED_USERS_FILE, "r") as f:
        allowed = [int(line.strip()) for line in f if line.strip()]
    return user_id in allowed

def add_user(user_id):
    if is_allowed(user_id):
        return False
    with open(ALLOWED_USERS_FILE, "a") as f:
        f.write(f"{user_id}\n")
    return True

def remove_user(user_id):
    with open(ALLOWED_USERS_FILE, "r") as f:
        users = [int(line.strip()) for line in f if line.strip()]
    if user_id not in users:
        return False
    users.remove(user_id)
    with open(ALLOWED_USERS_FILE, "w") as f:
        for uid in users:
            f.write(f"{uid}\n")
    return True

# Por usuario, guarda el "server" seleccionado
def get_user_server(user_id):
    server_file = f"server_{user_id}.txt"
    if os.path.exists(server_file):
        with open(server_file, "r") as f:
            return f.read().strip()
    return "telegram"

def set_user_server(user_id, server):
    server_file = f"server_{user_id}.txt"
    with open(server_file, "w") as f:
        f.write(server)

def set_user_hydrax_api(user_id, api):
    api_file = f"hydrax_api_{user_id}.txt"
    with open(api_file, "w") as f:
        f.write(api)

def get_user_hydrax_api(user_id):
    api_file = f"hydrax_api_{user_id}.txt"
    if os.path.exists(api_file):
        with open(api_file, "r") as f:
            return f.read().strip()
    return HYDRAX_API_ID

# Estado de anuncios/cancelación por usuario
user_states = {}

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()
dp.include_router(router)

@router.message(Command("start"))
async def cmd_start(msg: Message):
    user_id = msg.from_user.id
    if not is_allowed(user_id):
        await msg.answer(get_text("not_allowed", user_id))
        log_event(f"Denied access to user {user_id}")
        return
    await msg.answer(get_text("welcome", user_id))
    log_event(f"User {user_id} started bot.")

@router.message(Command("setlang"))
async def cmd_setlang(msg: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🇪🇸 Español", callback_data="lang_es")
    kb.button(text="🇺🇸 English", callback_data="lang_en")
    kb.adjust(2)
    await msg.answer(get_text("setlang", msg.from_user.id), reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("lang_"))
async def cb_setlang(cb: CallbackQuery):
    lang = "es" if cb.data == "lang_es" else "en"
    set_user_lang(cb.from_user.id, lang)
    await cb.message.edit_text(get_text("lang_changed", cb.from_user.id))
    log_event(f"User {cb.from_user.id} changed language to {lang}")

@router.message(Command("ayuda"))
async def cmd_ayuda(msg: Message):
    await msg.answer(get_text("help", msg.from_user.id))

@router.message(Command("add"))
async def cmd_add(msg: Message, command: CommandObject):
    if msg.from_user.id != CREATOR_ID:
        await msg.answer(get_text("not_allowed", msg.from_user.id))
        return
    try:
        uid = int(command.args.strip())
        if add_user(uid):
            await msg.answer(get_text("add_success", msg.from_user.id))
            log_event(f"User {uid} added by creator.")
        else:
            await msg.answer(get_text("already_allowed", msg.from_user.id))
    except Exception:
        await msg.answer("Formato inválido. Usa /add <id_usuario>")

@router.message(Command("remove"))
async def cmd_remove(msg: Message, command: CommandObject):
    if msg.from_user.id != CREATOR_ID:
        await msg.answer(get_text("not_allowed", msg.from_user.id))
        return
    try:
        uid = int(command.args.strip())
        if remove_user(uid):
            await msg.answer(get_text("remove_success", msg.from_user.id))
            log_event(f"User {uid} removed by creator.")
        else:
            await msg.answer(get_text("not_in_list", msg.from_user.id))
    except Exception:
        await msg.answer("Formato inválido. Usa /remove <id_usuario>")

@router.message(Command("log"))
async def cmd_log(msg: Message):
    if msg.from_user.id != CREATOR_ID:
        await msg.answer(get_text("not_allowed", msg.from_user.id))
        return
    if os.path.exists(LOG_FILE):
        await msg.answer_document(FSInputFile(LOG_FILE), caption=get_text("log_send", msg.from_user.id))
    else:
        await msg.answer("No hay registro disponible.")

@router.message(Command("ads"))
async def cmd_ads(msg: Message):
    if msg.from_user.id != CREATOR_ID:
        await msg.answer(get_text("not_allowed", msg.from_user.id))
        return
    user_states[msg.from_user.id] = {"ads": [], "step": 1}
    await msg.answer(get_text("ads_intro", msg.from_user.id))

@router.message(F.text, F.from_user.id == CREATOR_ID)
async def ads_flow(msg: Message):
    state = user_states.get(msg.from_user.id, {})
    if state.get("ads") is not None and state.get("step") == 1:
        state["ads"].append(msg.text)
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Sí", callback_data="ads_yes")
        kb.button(text="🚫 No", callback_data="ads_no")
        kb.adjust(2)
        await msg.answer(get_text("ads_add_more", msg.from_user.id), reply_markup=kb.as_markup())
        state["step"] = 2

@router.callback_query(F.data.in_(["ads_yes", "ads_no"]))
async def ads_add_more(cb: CallbackQuery):
    state = user_states.get(cb.from_user.id, {})
    if not state or "ads" not in state:
        return
    if cb.data == "ads_yes":
        preview = "\n".join(state["ads"])
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Sí", callback_data="ads_send")
        kb.button(text="🚫 No", callback_data="ads_cancel")
        kb.adjust(2)
        await cb.message.edit_text(get_text("ads_preview", cb.from_user.id) + f"\n\n{html.quote(preview)}",
                                  reply_markup=kb.as_markup())
        state["step"] = 3
    else:
        state["step"] = 1
        await cb.message.answer(get_text("ads_intro", cb.from_user.id))

@router.callback_query(F.data == "ads_send")
async def ads_send(cb: CallbackQuery):
    state = user_states.get(cb.from_user.id, {})
    if not state or "ads" not in state:
        return
    preview = "\n".join(state["ads"])
    sent, blocked, failed = 0, 0, 0
    all_users = []
    with open(ALLOWED_USERS_FILE, "r") as f:
        all_users = [int(line.strip()) for line in f if line.strip()]
    msg_status = await cb.message.answer("Enviando anuncio...")

    for idx, uid in enumerate(all_users):
        try:
            await bot.send_message(uid, preview)
            sent += 1
        except Exception as e:
            if "blocked" in str(e):
                blocked += 1
            else:
                failed += 1
        if idx % 5 == 0 or idx == len(all_users) - 1:
            await msg_status.edit_text(
                f"Enviando anuncio...\nEnviados: {sent}\nBloqueados: {blocked}\nFallidos: {failed}\nQuedan: {len(all_users)-idx-1}")
        await asyncio.sleep(0.5)
    await cb.message.answer(get_text("ads_sent", cb.from_user.id))
    await cb.message.answer(get_text("ads_summary", cb.from_user.id).format(sent=sent, blocked=blocked, failed=failed))
    log_event(f"Ads sent by creator ({sent} ok, {blocked} blocked, {failed} failed)")
    user_states.pop(cb.from_user.id, None)

@router.callback_query(F.data == "ads_cancel")
async def ads_cancel(cb: CallbackQuery):
    user_states.pop(cb.from_user.id, None)
    await cb.message.answer(get_text("cancelled", cb.from_user.id))

@router.message(Command("ping"))
async def cmd_ping(msg: Message):
    start = time.time()
    try:
        await bot.get_me()
        delta = int((time.time() - start) * 1000)
        await msg.answer(get_text("ping", msg.from_user.id).format(ms=delta))
    except Exception:
        await msg.answer("Ping failed.")

@router.message(Command("server"))
async def cmd_server(msg: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("server_tg", msg.from_user.id), callback_data="server_tg")
    kb.button(text=get_text("server_hydrax", msg.from_user.id), callback_data="server_hydrax")
    kb.adjust(2)
    await msg.answer(get_text("server_select", msg.from_user.id), reply_markup=kb.as_markup())

@router.callback_query(F.data.in_(["server_tg", "server_hydrax"]))
async def cb_server(cb: CallbackQuery):
    value = "telegram" if cb.data == "server_tg" else "hydrax"
    set_user_server(cb.from_user.id, value)
    await cb.message.edit_text(get_text("server_selected", cb.from_user.id).format(server=value.capitalize()))
    log_event(f"User {cb.from_user.id} set server to {value}")

@router.message(Command("hapi"))
async def cmd_hapi(msg: Message):
    await msg.answer(get_text("hapi_ask", msg.from_user.id))
    user_states[msg.from_user.id] = {"hapi": True, "step": 1}

@router.message(F.text)
async def hapi_flow(msg: Message):
    state = user_states.get(msg.from_user.id, {})
    if state.get("hapi") and state.get("step") == 1:
        api = msg.text.strip()
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Sí", callback_data="hapi_yes")
        kb.button(text="🚫 No", callback_data="hapi_no")
        kb.adjust(2)
        user_states[msg.from_user.id]["api"] = api
        await msg.answer(get_text("hapi_confirm", msg.from_user.id) + f"\n\n{html.quote(api)}", reply_markup=kb.as_markup())
        user_states[msg.from_user.id]["step"] = 2

@router.callback_query(F.data.in_(["hapi_yes", "hapi_no"]))
async def cb_hapi_confirm(cb: CallbackQuery):
    state = user_states.get(cb.from_user.id, {})
    if not state or "api" not in state:
        return
    if cb.data == "hapi_yes":
        set_user_hydrax_api(cb.from_user.id, state["api"])
        await cb.message.edit_text(get_text("hapi_ok", cb.from_user.id))
        log_event(f"User {cb.from_user.id} changed Hydrax API.")
    else:
        await cb.message.edit_text(get_text("hapi_cancel", cb.from_user.id))
    user_states.pop(cb.from_user.id, None)

@router.message(Command("cancel"))
async def cmd_cancel(msg: Message):
    user_states.pop(msg.from_user.id, None)
    await msg.answer(get_text("cancelled", msg.from_user.id))
    log_event(f"User {msg.from_user.id} cancelled operation.")

@router.message(F.video | F.document.mime_type.in_(["video/mp4", "video/mkv", "video/avi"]))
async def handle_video(msg: Message):
    user_id = msg.from_user.id
    if not is_allowed(user_id):
        await msg.answer(get_text("not_allowed", user_id))
        log_event(f"Denied video upload to user {user_id}")
        return

    server = get_user_server(user_id)
    await msg.answer(get_text("uploading", user_id))

    # Guardar archivo temporal
    file = msg.video or msg.document
    file_name = file.file_name or f"{file.file_id}.mp4"
    temp_path = f"./{file_name}"
    await msg.bot.download(file, destination=temp_path)

    log_event(f"User {user_id} uploaded {file_name} (server: {server})")

    try:
        if server == "hydrax":
            hydrax_api = get_user_hydrax_api(user_id)
            url = f"http://up.hydrax.net/{hydrax_api}"
            files = {'file': (file_name, open(temp_path, 'rb'), 'video/mp4')}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                await msg.answer(get_text("upload_complete", user_id) + f"\nHydrax: {response.text}")
            else:
                await msg.answer(get_text("upload_error", user_id))
        else:
            await msg.answer_document(FSInputFile(temp_path), caption=get_text("upload_complete", user_id))
        log_event(f"User {user_id} completed upload: {file_name}")
    except Exception as e:
        await msg.answer(get_text("upload_error", user_id))
        log_event(f"Upload error for user {user_id}: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s | %(message)s')
    import asyncio
    asyncio.run(dp.start_polling(bot))
