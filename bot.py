from bs4 import BeautifulSoup
import json
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sql_exec


# trunk-ignore(trufflehog/TelegramBotToken)
bot = telebot.TeleBot(API_TOKEN,'html', protect_content=True, allow_sending_without_reply=False)


def removeprefix(s, prefix):
    if s.startswith(prefix):
        return s[len(prefix):]
    else:
        return s


def deny(id: int):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👨‍💻 Владелец 👨‍💻",
                 url='tg://resolve?domain=sergej_nekrasov'))
    bot.send_message(id, '<b>У вас нет доступа! ⛔</b>\nОбратитесь к владельцу!',
                     message_effect_id='5104858069142078462', reply_markup=keyboard, protect_content=True)
    return


def generate_document(number: int):
    number, short_name, items = sql_exec.check(
        'data', 'number', str(number))[0]
    items = json.loads(items)
    partitions = items['partition']
    with open('template.html', 'r', encoding="UTF-8") as f:
        html_doc = f.read()
    soup = BeautifulSoup(html_doc, 'html.parser')
    z = soup.find('title')
    z.string = f'[Отчёт] {short_name}'
    images = soup.find_all("img", {"class": "image-profile-img"})
    images[0].attrs['src'] = items['photo']
    images[1].attrs['src'] = items['photo']
    name = soup.find_all("div", {"class": "name-surname"})
    name[0].contents[0].string = short_name
    name = soup.find_all("div", {"class": "mobile-name-surname"})
    name[0].contents[0].string = short_name
    notes = soup.find_all("div", {"class": "notes"})
    notes[0].contents[0].string = items['notes']
    notes = soup.find_all("div", {"class": "mobile-notes"})
    notes[0].contents[0].string = items['notes']
    telephone = soup.find_all("a", {"class": "link-phone"})
    telephone[0].attrs['href'] = f"tel:{items['phone']}"
    telephone[1].attrs['href'] = f"tel:{items['phone']}"
    target_element = soup.find_all("div", {"class": "report"})[0]
    for element in list(partitions.keys()):
        new_html = f'<div class="prod_search_ui_title"><div class="grid_title">{element}</div></div>'
        for keys in list(partitions[element].keys()):
            new_html += f'<div class="prod_search_ui"><div class="grid_column_title">{keys}</div><div class="grid_column_result">{partitions[element][keys]}</div></div>'
        target_element.insert(0, BeautifulSoup(new_html, 'html.parser'))
    script = f"""
    document.getElementsByClassName("telephone")[0]
    .addEventListener("click", function(event) {{
        open('tel:{items['phone']}', '_self');
        event.preventDefault();
    }});
    """
    new_html = f'<script>{script}</script>'
    target_element.insert(0, BeautifulSoup(new_html, 'html.parser'))
    with open(f'{short_name}.html', 'w', encoding="UTF-8") as f:
        f.write(soup.prettify())
    return f'{short_name}.html'


def gen_keyboard(arg=1):
    markup = InlineKeyboardMarkup()
    arg -= 1
    if arg < 0:
        arg = 0
    for x in range(arg * 6, arg * 6 + 6):
        try:
            if sql_exec.get_pos_line("data", x) != 0:
                line = sql_exec.get_pos_line_result("data", x)
                name = line[0][1]
                markup.row(InlineKeyboardButton(
                    f"{x + 1}. {name}", callback_data=f"{line[0][0]}"))
            else:
                break
        except Exception as e:
            print(e)
    if sql_exec.count_row("data") > 6:
        markup.row(InlineKeyboardButton("<<", callback_data=f"prev_page_{arg}"), InlineKeyboardButton(
            ">>", callback_data=f"next_page_{arg}"),)
    else:
        pass
    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(call.data)
    count_chats = sql_exec.count_row("data")
    count_page_chats = count_chats // 7
    if len(call.data) == 7:
        access = sql_exec.check(
            'users', 'user_id', str(call.from_user.id))[0][1]
        if access == '0':
            deny(call.from_user.id)
        else:
            name_html = generate_document(call.data)
            time.sleep(1)
            bot.send_document(call.message.chat.id, open(
                name_html, 'rb'), protect_content=True)
            bot.answer_callback_query(call.id)
            return
    elif call.data == "show_menu":
        access = sql_exec.check(
            'users', 'user_id', str(call.from_user.id))[0][1]
        if access == '0':
            deny(call.from_user.id)
        else:
            bot.send_message(call.message.chat.id, "<b>Выберите нужный отчёт</b>",
                             reply_markup=gen_keyboard())
    elif "next_page_" in call.data:
        page = int(removeprefix(str(call.data), "next_page_"))
        if page == count_page_chats + 2 or (count_page_chats == 1 and count_chats % 7 == 0):
            bot.answer_callback_query(
                call.id, text="Дальше листать некуда... Больше чатов у нас нет :(", show_alert=True)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="<b>Выберите нужный отчёт</b>", parse_mode="HTML", reply_markup=gen_keyboard(page + 2))
        return
    elif "prev_page_" in call.data:
        page = int(removeprefix(str(call.data), "prev_page_"))
        if page == 0:
            bot.answer_callback_query(
                call.id, text="Дальше листать некуда... Отрицательных страниц не существует :(", show_alert=True)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="<b>Выберите нужный отчёт</b>", parse_mode="HTML", reply_markup=gen_keyboard(page))
        return
    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['start'])
def start_message(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⚙ Меню ⚙", callback_data="show_menu"))
    if not sql_exec.check('users', 'user_id', str(message.chat.id)):
        sql_exec.insert('users', 'user_id,access', f'{message.chat.id},0')
    bot.send_message(message.chat.id, '<b>Добро пожаловать! 👋</b>\n\nДанный бот работает для личного использования. <b>Если вы хотите получить доступ - свяжитесь с владельцем</b>\n\n<b>Для того чтобы отобразить меню - нажмите кнопку ниже</b>',
                     reply_markup=keyboard, message_effect_id='5046509860389126442', protect_content=True)


bot.infinity_polling()
