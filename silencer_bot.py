import config
import dbworker
import telebot
import os
from flask import Flask, request

# Need this to connect to api.telegram.org
from telebot import apihelper
from telebot import types

# Set proxy to work
apihelper.proxy = config.availableProxy
# Taking our bot with TOKEN
bot = telebot.TeleBot(config.token)


def build_chats_list_keyboard(chats):
    print(chats)
    keyboard = types.InlineKeyboardMarkup()
    for chat_id in chats:
        chat = bot.get_chat(chat_id)
        chat_button = types.InlineKeyboardButton(text=chat.title, callback_data='set_mode,{0}'.format(chat.id))
        delete_button = types.InlineKeyboardButton(text="Удалить чат", callback_data='delete_chat,{0}'.format(chat.id))
        keyboard.add(chat_button, delete_button)
    return keyboard


def build_chat_keyboard(mode, user_id, chat_id):
    keyboard = types.InlineKeyboardMarkup()
    only_me = 'Только я'
    only_admins = 'Только администраторы'
    all_members = 'Все'
    if mode == config.SilenceMode.C_ONLY_CREATOR.value.format(user_id=user_id):
        only_me += ' ✅'
    elif mode == config.SilenceMode.C_ONLY_ADMINS.value:
        only_admins += ' ✅'
    elif mode == config.SilenceMode.C_ALL.value:
        all_members += ' ✅'
    keyboard.add(types.InlineKeyboardButton(text=only_me,
                                            callback_data='{0},{1}'.format(config.SilenceMode.C_ONLY_CREATOR.value.format(user_id=user_id), chat_id)))
    keyboard.add(types.InlineKeyboardButton(text=only_admins,
                                            callback_data='{0},{1}'.format(config.SilenceMode.C_ONLY_ADMINS.value, chat_id)))
    keyboard.add(types.InlineKeyboardButton(text=all_members,
                                            callback_data='{0},{1}'.format(config.SilenceMode.C_ALL.value, chat_id)))

    return keyboard


@bot.message_handler(func=lambda m: True, content_types=['new_chat_members'])
def add_on_invite(message):
    bot_user = bot.get_me()
    if message.new_chat_member.id == bot_user.id:
        if message.chat.type == 'supergroup' and message.from_user.id in config.admins:

            s = dbworker.add_chat_for_admin(message.from_user.id, message.chat.id)
            if s:
                dbworker.set_chat_silence_mode(message.chat.id, config.SilenceMode.C_ONLY_ADMINS.value)
                bot.send_message(message.from_user.id, 'Чат {0} добавлен'.format(message.chat.title))
            else:
                bot.send_message(message.from_user.id, 'Чат {0} не добавлен. Обратитесь к создателю'.format(message.chat.title))
        else:
            bot.send_message(message.from_user.id, 'Чат {0} не является супергруппой'.format(message.chat.title))
    else:
        bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(func=lambda m: m.chat.type == 'supergroup' and m.from_user.id in config.admins, content_types=['migrate_from_chat_id'])
def add_on_supergroup_migration(message):
    s = dbworker.add_chat_for_admin(message.from_user.id, message.chat.id)
    if s:
        dbworker.set_chat_silence_mode(message.chat.id, config.SilenceMode.C_ONLY_ADMINS.value)
        bot.send_message(message.from_user.id, 'Чат {0} добавлен'.format(message.chat.title))
    else:
        bot.send_message(message.from_user.id, 'Чат {0} не добавлен. Обратитесь к создателю'.format(message.chat.title))


@bot.message_handler(func=lambda m: True, content_types=['left_chat_member'])
def show_new_members(message):
    bot_user = bot.get_me()
    if message.left_chat_member.id == bot_user.id:
        mode = dbworker.get_chat_silence_mode(message.chat.id)
        if mode is None:
            return
        s = dbworker.delete_chat_from_list(message.chat.id)
        if s:
            bot.send_message(message.from_user.id, 'Чат {0} удалён.'.format(message.chat.title))
    else:
        bot.delete_message(message.chat.id, message.message_id)


# Bot start answer
@bot.message_handler(func=lambda m: m.chat.type == 'private', commands=['start'])
def handle_start(message):
    dbworker.create_chats_table(message.from_user.id)
    user_markup = telebot.types.ReplyKeyboardMarkup(True)
    user_markup.row(config.menuHelp)
    user_markup.row(config.menuChatList)
    bot.send_message(message.from_user.id,
                     config.start_message,
                     reply_markup=user_markup)


# Get any message from admin
@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id in config.admins)
def user_chat_settings(message):
    if message.text == config.menuHelp:
        answer = config.bot_instruction
        bot.send_message(message.chat.id, answer)
    elif message.text == config.menuChatList:
        answer = "Cписок чатов:"
        chats = dbworker.get_chat_set_for_admin(message.from_user.id)
        keyboard = types.InlineKeyboardMarkup()
        if chats is not None:
            keyboard = build_chats_list_keyboard(chats)
        else:
            answer = 'У тебя пока нет чатов.'
        keyboard.add(types.InlineKeyboardButton(text='Как добавить чат?', callback_data='add_chat'))
        bot.send_message(message.chat.id, answer, reply_markup=keyboard)


# Get any message from unknown
@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id not in config.admins)
def user_chat_settings(message):
    bot.send_message(message.chat.id, 'Вам нельзя со мной разговаривать. Обратитесь к тому, кто вам дал мою ссылку.')


# Handle Callback queries
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    if call.data == 'add_chat':
        answer = 'Добавь меня в супергруппу и дай права администратора'
        bot.answer_callback_query(callback_query_id=call.id, show_alert=False)
        bot.send_message(call.message.chat.id, answer)
        return

    call_chat, chat_id = call.data.split(',')
    mode = ''

    if call_chat == 'delete_chat':
        s = dbworker.delete_chat_from_list(chat_id)
        if s:
            bot.leave_chat(chat_id)
            bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text='Чат удалён')
            chats = dbworker.get_chat_set_for_admin(call.from_user.id)
            answer = 'Cписок чатов:'
            keyboard = types.InlineKeyboardMarkup()
            if chats is not None:
                keyboard = build_chats_list_keyboard(chats)
            else:
                answer = 'У тебя пока нет чатов.'
            keyboard.add(types.InlineKeyboardButton(text='Как добавить чат?', callback_data='add_chat'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=answer, reply_markup=keyboard)
        else:
            bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text='Ошибка удаления')
        return

    if call_chat == 'set_mode':
        mode = dbworker.get_chat_silence_mode(chat_id)
        bot.answer_callback_query(callback_query_id=call.id, show_alert=False)
        keyboard = build_chat_keyboard(mode, call.from_user.id, chat_id)
        chat = bot.get_chat(chat_id)
        bot.send_message(call.message.chat.id, "Кто может писать в чате {0}?".format(chat.title), reply_markup=keyboard)
        return

    answer = ''
    old_mode = dbworker.get_chat_silence_mode(chat_id)
    if call_chat == config.SilenceMode.C_ONLY_CREATOR.value.format(user_id=call.from_user.id):
        mode = config.SilenceMode.C_ONLY_CREATOR.value.format(user_id=call.from_user.id)
        answer = "Режим Только я - включен"
    elif call_chat == config.SilenceMode.C_ONLY_ADMINS.value:
        mode = config.SilenceMode.C_ONLY_ADMINS.value
        answer = "Режим Только администраторы - включен"
    elif call_chat == config.SilenceMode.C_ALL.value:
        mode = config.SilenceMode.C_ALL.value
        answer = "Режим Все - включен"
    bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text=answer)
    if mode == old_mode:
        return
    dbworker.set_chat_silence_mode(chat_id, mode)
    keyboard = build_chat_keyboard(mode, call.from_user.id, chat_id)
    chat = bot.get_chat(chat_id)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Кто может писать в чате {0}?".format(chat.title), reply_markup=keyboard)


# Handle chat messages
@bot.message_handler(func=lambda message: message.chat.type == 'supergroup', content_types=config.all_message_types)
def filter_supergroup_messages(message):
    bot_user = bot.get_me()
    chat_member = bot.get_chat_member(message.chat.id, bot_user.id)
    if chat_member.can_delete_messages and chat_member.can_restrict_members:
        mode = dbworker.get_chat_silence_mode(message.chat.id)
        if mode == config.SilenceMode.C_ONLY_ADMINS.value:
            members = bot.get_chat_administrators(message.chat.id)
            users_ids = map(lambda x: x.user.id, members)
            if message.from_user.id not in users_ids:
                bot.delete_message(message.chat.id, message.message_id)
        elif mode == config.SilenceMode.C_ALL.value:
            return
        elif message.from_user.id != mode:
            if message.from_user.id != mode:
                bot.delete_message(message.chat.id, message.message_id)


def listener(messages):
    for message in messages:
        print(message)


bot.set_update_listener(listener)
bot.polling(none_stop=True)

"""
@server.route('/' + config.token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "POST", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://countsilencebot.herokuapp.com/' + config.token)
    return "CONNECTED", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', '5000')))
"""