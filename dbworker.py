import config
import os
import psycopg2


# Database setup
DATABASE_URL = os.environ['DATABASE_URL']
connection = psycopg2.connect(DATABASE_URL, sslmode='require')
#connection = psycopg2.connect('postgres://xgvcdhwkcoxhsx:21c47b32b63bb684b2788b41e0004a046d78da2ab93a4c354704f8896486aaef@ec2-54-217-235-159.eu-west-1.compute.amazonaws.com:5432/dl9bl5vqdmkuu', sslmode='require')
cursor = connection.cursor()


def create_chats_table(user_id):
    cursor.execute("CREATE TABLE IF NOT EXISTS admin_chats (user_id integer, chat_id bigint);")
    cursor.execute("CREATE TABLE IF NOT EXISTS chats_mode (chat_id bigint, chat_mode text);")
    connection.commit()


# Пытаемся достать режим работы чата
def get_chat_silence_mode(chat_id):
    try:
        cursor.execute("SELECT chat_mode FROM chats_mode WHERE chat_id='{}'".format(chat_id))
        result = cursor.fetchone()
        return result[0]
    except:
        return None


# Сохраняем текущий режим чата
def set_chat_silence_mode(chat_id, mode):
    cursor.execute("UPDATE chats_mode SET chat_mode = '{0}' WHERE chat_id = '{1}'".format(mode, chat_id))
    connection.commit()


# Добавим чат в список администрируемых
def add_chat_for_admin(user_id, chat_id):
    try:
        cursor.execute("INSERT INTO admin_chats (user_id, chat_id) VALUES ('{0}', '{1}')".format(str(user_id), chat_id))
        cursor.execute("INSERT INTO chats_mode (chat_id, chat_mode) VALUES ('{0}', '{1}')".format(chat_id, config.SilenceMode.C_ONLY_ADMINS.value))
        connection.commit()
        return True
    except:
        connection.rollback()
        return False


# Получим список администрируемых чатов
def get_chat_set_for_admin(user_id):
    try:
        cursor.execute("SELECT chat_id FROM admin_chats WHERE user_id='{}'".format(user_id))
        results = cursor.fetchall()
        return results
    except:
        connection.rollback()
        return None


# Удалим чат из списка
def delete_chat_from_list(chat_id):
    try:
        cursor.execute("DELETE FROM admin_chats WHERE chat_id='{}'".format(chat_id))
        cursor.execute("DELETE FROM chats_mode WHERE chat_id='{}'".format(chat_id))
        connection.commit()
        return True
    except:
        connection.rollback()
        return False
