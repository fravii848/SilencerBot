# coding=utf-8
import config
import telebot
import flask
from flask import Flask

app = Flask(__name__)

WEBHOOK_HOST = 'silencer-219514.appspot.com'
WEBHOOK_PORT = 80 # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % config.token


# Taking our bot with TOKEN
bot = telebot.TeleBot(config.token)


@bot.message_handler(func=lambda m: True, content_types=['new_chat_members'])
def add_on_invite(message):
    bot_user = bot.get_me()
    if message.new_chat_member.id == bot_user.id:
        if message.chat.type == 'supergroup' and message.from_user.id in config.admins:
            bot.send_message(message.from_user.id, 'Чат {0} добавлен'.format(message.chat.title))
        else:
            bot.send_message(message.from_user.id, 'Чат {0} не является супергруппой'.format(message.chat.title))
    else:
        bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(func=lambda m: m.chat.type == 'supergroup' and m.from_user.id in config.admins,
                     content_types=['migrate_from_chat_id'])
def add_on_supergroup_migration(message):
    bot.send_message(message.from_user.id, 'Чат {0} добавлен'.format(message.chat.title))


@bot.message_handler(func=lambda m: True, content_types=['left_chat_member'])
def show_new_members(message):
    bot_user = bot.get_me()
    if message.left_chat_member.id == bot_user.id:
        bot.send_message(message.from_user.id, 'Чат {0} удалён.'.format(message.chat.title))
    else:
        bot.delete_message(message.chat.id, message.message_id)


# Bot start answer
@bot.message_handler(func=lambda m: m.chat.type == 'private', commands=['start'])
def handle_start(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True)
    user_markup.row(config.menuHelp)
    bot.send_message(message.from_user.id,
                     config.start_message,
                     reply_markup=user_markup)


# Get any message from admin
@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id in config.admins)
def user_chat_settings(message):
    if message.text == config.menuHelp:
        answer = config.bot_instruction
        bot.send_message(message.chat.id, answer)


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


# Handle chat messages
@bot.message_handler(func=lambda message: message.chat.type == 'supergroup', content_types=config.all_message_types)
def filter_supergroup_messages(message):
    bot_user = bot.get_me()
    chat_member = bot.get_chat_member(message.chat.id, bot_user.id)
    if chat_member.can_delete_messages and chat_member.can_restrict_members:
        members = bot.get_chat_administrators(message.chat.id)
        users_ids = map(lambda x: x.user.id, members)
        if message.from_user.id not in users_ids:
            bot.delete_message(message.chat.id, message.message_id)


@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook(WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/', methods=['GET', 'HEAD'])
def index():
    return '.'


# Start flask server
app.run(host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT)


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
