import telebot
import sql_exec
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# trunk-ignore(trufflehog/TelegramBotToken)
bot = telebot.TeleBot('7100797155:AAHRVltuJt51w5_lbfd4UF_GR2JiH2JTikQ', 'html')


# def gen_markup():
#     markup = InlineKeyboardMarkup()
#     markup.row_width = 2
#     markup.add(InlineKeyboardButton("Yes", callback_data="cb_yes"),
#                InlineKeyboardButton("No", callback_data="cb_no"))
#     return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "show_menu":
        bot.answer_callback_query(call.id, call.text)
    bot.answer_callback_query(call.id)


# @bot.message_handler(func=lambda message: True)
# def message_handler(message):
#     bot.send_message(message.chat.id, "Yes/no?", reply_markup=gen_markup())


@bot.message_handler(commands=['start'])
def start_message(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⚙ Меню ⚙", callback_data="show_menu"))
    if not sql_exec.check('users', 'user_id', str(message.chat.id)):
        sql_exec.insert('users', 'user_id,access', f'{message.chat.id},0')
    bot.send_message(message.chat.id, '<b>Добро пожаловать! 👋</b>\n\nДанный бот работает для личного использования. <b>Если вы хотите получить доступ - свяжитесь с владельцем</b>\n\n<b>Для того чтобы отобразить меню - нажмите кнопку ниже</b>', reply_markup=keyboard, message_effect_id='5046509860389126442')

bot.infinity_polling()
