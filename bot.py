import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, FloodWait
import os
import time

# Get environment variables
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Initialize the bot client
app = Client(
    "ZeroBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize the user client (for kicking members)
user_app = Client(
    "UserSession",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# Temporary storage for channel IDs and user states
user_states = {} # To store user's current action, e.g., waiting for channel ID
user_channels = {} # To store the channel ID for each user

async def get_channel_id(chat_id_or_link):
    try:
        if chat_id_or_link.startswith("-100"):
            return int(chat_id_or_link)
        elif chat_id_or_link.startswith("@"):
            chat = await user_app.get_chat(chat_id_or_link)
            return chat.id
        elif chat_id_or_link.startswith("https://t.me/"):
            parts = chat_id_or_link.split('/')
            if len(parts) > 3:
                chat_id_or_link = parts[3]
            chat = await user_app.get_chat(chat_id_or_link)
            return chat.id
        else:
            return None
    except Exception as e:
        print(f"Error getting channel ID: {e}")
        return None

async def check_admin_rights(chat_id, user_id):
    try:
        member = await user_app.get_chat_member(chat_id, user_id)
        if member.status in ["creator", "administrator"]:
            return True
        return False
    except Exception as e:
        print(f"Error checking admin rights: {e}")
        return False

async def zero_channel_members(chat_id, message):
    kicked_count = 0
    try:
        await message.edit_text("بدء تصفير القناة...")
        async for member in user_app.get_chat_members(chat_id):
            if member.user.id == user_app.me.id: # Don't kick self
                continue
            try:
                await user_app.kick_chat_member(chat_id, member.user.id)
                kicked_count += 1
                await message.edit_text(f"جارٍ تصفير القناة... تم طرد {kicked_count} عضو.")
                await asyncio.sleep(0.1) # To avoid flood waits
            except FloodWait as e:
                await message.edit_text(f"تم الوصول إلى حد الطرد، الانتظار لـ {e.value} ثوانٍ.")
                await asyncio.sleep(e.value)
            except Exception as e:
                print(f"Error kicking member {member.user.id}: {e}")
                # await message.reply_text(f"خطأ أثناء طرد العضو {member.user.id}: {e}")
        await message.edit_text(f"اكتمل تصفير القناة. تم طرد إجمالي {kicked_count} عضو.")
    except ChatAdminRequired:
        await message.edit_text("البوت ليس لديه صلاحيات المسؤول لطرد الأعضاء في هذه القناة.")
    except Exception as e:
        await message.edit_text(f"حدث خطأ أثناء تصفير القناة: {e}")

async def clean_deleted_accounts(chat_id, message):
    kicked_count = 0
    try:
        await message.edit_text("بدء تنظيف الحسابات المحذوفة...")
        async for member in user_app.get_chat_members(chat_id):
            if member.user.is_deleted:
                try:
                    await user_app.kick_chat_member(chat_id, member.user.id)
                    kicked_count += 1
                    await message.edit_text(f"جارٍ تنظيف الحسابات المحذوفة... تم طرد {kicked_count} حساب.")
                    await asyncio.sleep(0.1)
                except FloodWait as e:
                    await message.edit_text(f"تم الوصول إلى حد الطرد، الانتظار لـ {e.value} ثوانٍ.")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    print(f"Error kicking deleted account {member.user.id}: {e}")
        await message.edit_text(f"اكتمل تنظيف الحسابات المحذوفة. تم طرد إجمالي {kicked_count} حساب.")
    except ChatAdminRequired:
        await message.edit_text("البوت ليس لديه صلاحيات المسؤول لطرد الأعضاء في هذه القناة.")
    except Exception as e:
        await message.edit_text(f"حدث خطأ أثناء تنظيف الحسابات المحذوفة: {e}")

async def clean_fake_accounts(chat_id, message):
    kicked_count = 0
    try:
        await message.edit_text("بدء تنظيف الحسابات الوهمية (بدون صورة أو اسم مستخدم)...")
        async for member in user_app.get_chat_members(chat_id):
            if not member.user.photo and not member.user.username:
                try:
                    await user_app.kick_chat_member(chat_id, member.user.id)
                    kicked_count += 1
                    await message.edit_text(f"جارٍ تنظيف الحسابات الوهمية... تم طرد {kicked_count} حساب.")
                    await asyncio.sleep(0.1)
                except FloodWait as e:
                    await message.edit_text(f"تم الوصول إلى حد الطرد، الانتظار لـ {e.value} ثوانٍ.")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    print(f"Error kicking fake account {member.user.id}: {e}")
        await message.edit_text(f"اكتمل تنظيف الحسابات الوهمية. تم طرد إجمالي {kicked_count} حساب.")
    except ChatAdminRequired:
        await message.edit_text("البوت ليس لديه صلاحيات المسؤول لطرد الأعضاء في هذه القناة.")
    except Exception as e:
        await message.edit_text(f"حدث خطأ أثناء تنظيف الحسابات الوهمية: {e}")

@app.on_message(filters.command("start"))
async def start_command(client, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("إضافة قناة", callback_data="add_channel")],
            [InlineKeyboardButton("تصفير القناة", callback_data="zero_channel")],
            [InlineKeyboardButton("تنظيف الحسابات المحذوفة", callback_data="clean_deleted")],
            [InlineKeyboardButton("تنظيف الحسابات الوهمية", callback_data="clean_fake")],
            [InlineKeyboardButton("المطور", callback_data="developer")]
        ]
    )
    await message.reply_text("مرحباً بك في بوت تصفير القنوات! اختر من الخيارات أدناه:", reply_markup=keyboard)

@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message

    if data == "add_channel":
        await message.edit_text("الرجاء إرسال معرف القناة (Channel ID) أو رابطها.")
        user_states[user_id] = "waiting_for_channel_id"
    elif data == "zero_channel":
        if user_id not in user_channels:
            await message.edit_text("الرجاء إضافة قناة أولاً باستخدام زر 'إضافة قناة'.")
            return
        channel_id = user_channels[user_id]
        if not await check_admin_rights(channel_id, user_app.me.id):
            await message.edit_text("الحساب المساعد (User Session) ليس مسؤولاً في هذه القناة أو لا يملك صلاحية طرد الأعضاء.")
            return
        await zero_channel_members(channel_id, message)
    elif data == "clean_deleted":
        if user_id not in user_channels:
            await message.edit_text("الرجاء إضافة قناة أولاً باستخدام زر 'إضافة قناة'.")
            return
        channel_id = user_channels[user_id]
        if not await check_admin_rights(channel_id, user_app.me.id):
            await message.edit_text("الحساب المساعد (User Session) ليس مسؤولاً في هذه القناة أو لا يملك صلاحية طرد الأعضاء.")
            return
        await clean_deleted_accounts(channel_id, message)
    elif data == "clean_fake":
        if user_id not in user_channels:
            await message.edit_text("الرجاء إضافة قناة أولاً باستخدام زر 'إضافة قناة'.")
            return
        channel_id = user_channels[user_id]
        if not await check_admin_rights(channel_id, user_app.me.id):
            await message.edit_text("الحساب المساعد (User Session) ليس مسؤولاً في هذه القناة أو لا يملك صلاحية طرد الأعضاء.")
            return
        await clean_fake_accounts(channel_id, message)
    elif data == "developer":
        await message.edit_text("المطور: [اسم المطور الخاص بك] (@اسم_المطور)")

@app.on_message(filters.text & filters.private)
async def handle_text_input(client, message):
    user_id = message.from_user.id
    if user_states.get(user_id) == "waiting_for_channel_id":
        channel_input = message.text.strip()
        channel_id = await get_channel_id(channel_input)
        if channel_id:
            user_channels[user_id] = channel_id
            user_states[user_id] = "idle"
            await message.reply_text(f"تم حفظ القناة: `{channel_input}` (ID: `{channel_id}`). يمكنك الآن استخدام خيارات التصفير.")
        else:
            await message.reply_text("صيغة معرف القناة أو الرابط غير صحيحة. الرجاء إرسال معرف القناة (يبدأ بـ -100) أو رابطها (مثل @username أو https://t.me/username).")

async def main():
    await app.start()
    await user_app.start()
    print("Both clients started.")
    await idle()

if __name__ == "__main__":
    from pyrogram import idle
    asyncio.run(main())
