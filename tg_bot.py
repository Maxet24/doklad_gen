import doklad_generator
import prompts
import secret_vars
import telebot
import tempfile
import os
import json
from db_manager import get_db, set_db
from datetime import datetime

DEBUG = False
TOKEN = secret_vars.TG_KEY
whitelist = ['maxet24']
DOKLAD_TYPES = ['1', '2']

FOLDER_PATH = os.getcwd()
if os.getcwd() == "/":
    FOLDER_PATH = "/home/maxet24/doklad_gen"

bot = telebot.TeleBot(TOKEN)

user_states = {}
# awaiting_for_doklad_type
user_requests = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, prompts.start_text, parse_mode="Markdown")

@bot.message_handler(commands=['show_logs'])
def handle_show_logs(message):
    if message.chat.username in whitelist:
        curr_db = get_db()
        pretty_output = ""
        for person in curr_db.values():
            # pretty_output += f"{person['username']} : {person['doklad_gens']}, themes: {person['themes']}, cost: {round(person['money_spent'] * 1000) / 1000} $\n"
            pretty_output += f"{person['username']} : {person['doklad_gens']}, cost: {round(person['money_spent'] * 1000) / 1000} $, "
        bot.send_message(message.chat.id, pretty_output)

@bot.message_handler(commands=['show_logs_short'])
def handle_show_logs_short(message):
    if message.chat.username in whitelist:
        curr_db = get_db()

        total_value = 0
        cnt_users = 0
        cnt_uses = 0
        for person in curr_db.values():
            cnt_users += 1
            cnt_uses += person['doklad_gens']
            total_value += person['money_spent']

        pretty_output = f"Total users: {cnt_users}, uses: {cnt_uses}, cost: {total_value}"

        bot.send_message(message.chat.id, pretty_output)

@bot.message_handler(commands=['send_file'])
def handle_send_file(message):
    if message.chat.username in whitelist:
        print('UPLOADING...')
        send_doklad(message.chat.id, FOLDER_PATH + "/doklads/maxet24_6.pptx")
        print('done')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # If doklad type sent
    if message.chat.id in user_states and user_states[message.chat.id] == 'awaiting_for_doklad_type':

        doklad_type = message.text
        if doklad_type not in DOKLAD_TYPES:
            user_states[message.chat.id] = 'none'
            bot.send_message(message.chat.id, "Чел ты...")
            return

        #######
        # if doklad_type == '2':
        #     bot.send_message(message.chat.id, "Функция в стадии разработки...")
        #     user_states[message.chat.id] = 'none'
        #     return
        #####

        # Get from cache
        user_states[message.chat.id] = 'none'
        user_request_text = user_requests[message.chat.id]

        bot.send_message(message.chat.id, "Ждите, генерация может занять около 1.5 минуты...")

        theme = user_request_text.split("\n")[0]
        fio = "Глебов Максим Александрович РСБО-01-23"
        if len(user_request_text.split("\n")) > 1:
            fio = user_request_text.split("\n")[1]

        # Legal check
        curr_db = get_db()
        if message.chat.username in curr_db:

            if str(datetime.now().date()) not in curr_db[message.chat.username]['uses_by_days']:
                curr_db[message.chat.username]['uses_by_days'][str(datetime.now().date())] = 0

            # OUT OF USAGE
            if curr_db[message.chat.username]['uses_by_days'][str(datetime.now().date())] >= 5 and message.chat.username not in whitelist:
                bot.send_message(message.chat.id, "Воу, воу, бро, полегче!\n\nНа сегодня твой лимит (5 генераций) исчерпан)")
                return

            curr_db[message.chat.username]['doklad_gens'] += 1
            curr_db[message.chat.username]['themes'].append(theme)
            curr_db[message.chat.username]['fios'].append(fio)
            curr_db[message.chat.username]['uses_by_days'][str(datetime.now().date())] += 1
        else:
            curr_db[message.chat.username] = {
                'id': message.chat.id,
                'username': message.chat.username,
                'doklad_gens': 1,
                'themes': [theme],
                'fios': [fio],
                'uses_by_days': {str(datetime.now().date()): 1},
                'money_spent': 0
            }

        money_spent = 0
        if doklad_type == '1':
            filename = FOLDER_PATH + f'/doklads/{message.chat.username}_{curr_db[message.chat.username]["doklad_gens"]}.pptx'
            meta = doklad_generator.gen_doklad_pptx(user_request_text, fio, filename)
            money_spent = meta['money_spent']
            send_doklad(message.chat.id, filename)

        elif doklad_type == '2':
            pptx_filename = FOLDER_PATH + f'/doklads/{message.chat.username}_{curr_db[message.chat.username]["doklad_gens"]}.pptx'
            docs_filename = FOLDER_PATH + f'/doklads/{message.chat.username}_{curr_db[message.chat.username]["doklad_gens"]}.docx'
            meta = doklad_generator.gen_doklad_pptx_docx(user_request_text, fio, pptx_filename, docs_filename)
            money_spent = meta['money_spent']
            send_doklad(message.chat.id, pptx_filename)
            send_doklad(message.chat.id, docs_filename)

        curr_db[message.chat.username]['money_spent'] += money_spent
        set_db(curr_db)

        if DEBUG:
            print('DONE')

    # If nothing earlier
    else:
        user_requests[message.chat.id] = message.text
        user_states[message.chat.id] = 'awaiting_for_doklad_type'
        bot.send_message(message.chat.id, "Какой тип доклада нужен?\n\n"
                                          "1 - Только презентация с текстом на слайдах (старая версия)\n"
                                          "2 - Презентация с картинками + Word документ с текстом\n\n"
                                          "Напиши цифру ;)")


def send_doklad(chat_id, filename):
    with open(filename, 'rb') as file:
        bot.send_document(chat_id, file)


if __name__ == "__main__":
    bot.polling(none_stop=True)
