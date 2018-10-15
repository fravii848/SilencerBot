from enum import Enum


class SilenceMode(Enum):
    C_ONLY_CREATOR = '{user_id}'
    C_ONLY_ADMINS = 'admins'
    C_ALL = 'all'


token = '566786956:AAEACP90bJLHhl0jrvTcuONCRWsZ_F16G2s'

availableProxy = {'https': 'socks5://userproxy:password@ams3.proxy.veesecurity.com:443'}
admins = [491444575, 106791929]

menuHelp = 'Инструкция'
menuChatList = 'Мои чаты'

start_message = 'Добрый день. Для работы со мной:\n1) Добавьте меня в супергруппу\n2) Дайте мне права администратора в этой группе\n3) Выберите режим чата'
bot_instruction = 'Как только вы добавите меня в чат, я вас оповещу о том, что чат добавлен в список. И вы сможете выбрать режим работы.\n\nВАЖНО!\n\nУбедитесь, что чат в котором я нахожусь является супергруппой, а так же убедитесь в том, что у меня есть права на удаление сообщений.\nВ ином случае я не смогу вам помочь =/'

all_message_types = ['text', 'sticker', 'document', 'audio', 'animation', 'game', 'video', 'voice', 'video_note', 'contact', 'location', 'venue', 'photo']
