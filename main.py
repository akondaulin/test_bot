import telebot
from telebot import types
from datetime import datetime
import psycopg2
from config import TOKEN, dbname, user, password, port, host
import dashboard
import matplotlib
matplotlib.use('Agg')
from tabulate import tabulate
from prettytable import PrettyTable


bot = telebot.TeleBot(TOKEN)

def main_menu(message):
    markup = types.ReplyKeyboardMarkup()
    btn_start = types.KeyboardButton('/start')
    btn_stats = types.KeyboardButton('/stats')
    btn_info = types.KeyboardButton('/info')
    markup.row(btn_start, btn_stats, btn_info)
    bot.send_message(message.chat.id, 'Главное меню:', reply_markup=markup)

#### Начало с кнопки Старт
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_1 = types.KeyboardButton('💰 Приход')
    btn_2 = types.KeyboardButton('😫 Расход')
    markup.row(btn_1, btn_2)
    bot.send_message(message.chat.id, 'Выбери категорию', reply_markup=markup)

#### Начало с кнопки stats
@bot.message_handler(commands=['stats'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    btn_1 = types.KeyboardButton('Сводка расходов за сегодня')
    btn_2 = types.KeyboardButton('Сводка расходов за вчера')
    markup.row(btn_1, btn_2)
    btn_3 = types.KeyboardButton('Сводка расходов за неделю')
    btn_4 = types.KeyboardButton('Сводка расходов с начала месяца')
    markup.row(btn_3,btn_4)
    bot.send_message(message.chat.id, 'Выбери период', reply_markup=markup)

#### Начало с кнопки Info
@bot.message_handler(commands=['info'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    btn_1 = types.KeyboardButton('Сколько отложено с начала месяца')
    btn_2 = types.KeyboardButton('Детализация по источникам за неделю')
    markup.row(btn_1, btn_2)
    btn_3 = types.KeyboardButton('Детализация по источникам за текущий месяц')
    markup.row(btn_3)
    bot.send_message(message.chat.id, 'Выбери что узнать подробнее', reply_markup=markup)

# Обработчик выбора периода для кнопки Info
@bot.message_handler(func=lambda message: message.text in ['Сколько отложено с начала месяца','Детализация по источникам за неделю','Детализация по источникам за текущий месяц'])
def show_info(message):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    cur = conn.cursor()

    if message.text == 'Сколько отложено с начала месяца':
        sql = "SELECT SUM(amount) as total_cost FROM finance.costs WHERE source = 'Отложить 20%'"
        cur.execute(sql)
        total_cost = cur.fetchone()[0]
        if total_cost is None:
            total_cost = 0
        bot.send_message(message.chat.id, f'Сумма отложенной суммы: {total_cost}')
    elif message.text == 'Детализация по источникам за неделю':
        sql = "SELECT source, SUM(amount) FROM finance.costs WHERE date >=  CURRENT_DATE - INTERVAL '7 days' group by source"
        cur.execute(sql)
        rows = cur.fetchall()
        if rows:
            table = "Детализация по источникам за неделю:\n"
            for row in rows:
                source = row[0]
                amount = row[1]
                if amount < 5000:
                    bgcolor = '#00FF00'  # Green background
                elif amount < 10000:
                    bgcolor = '#FFFF00'  # Yellow background
                else:
                    bgcolor = '#FF0000'  # Red background
                table += f"<pre>{source}\t{amount}</pre>\n<code style='background-color:{bgcolor}'>{' '*len(str(amount))}{'.'}</code>\n"  
            bot.send_message(message.chat.id, f'{table}', parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, 'Нет данных о расходах за последнюю неделю.')
    elif message.text == 'Детализация по источникам за текущий месяц':
        sql = "SELECT source, SUM(amount) FROM finance.costs WHERE date >= DATE_TRUNC('month', CURRENT_DATE) group by source"
        cur.execute(sql)
        rows = cur.fetchall()
        if rows:
            table = "Детализация по источникам за текущий месяц:\n"
            for row in rows:
                source = row[0]
                amount = row[1]
                if amount < 5000:
                    bgcolor = '#00FF00'  # Green background
                elif amount < 10000:
                    bgcolor = '#FFFF00'  # Yellow background
                else:
                    bgcolor = '#FF0000'  # Red background
                table += f"<pre>{source}\t{amount}</pre>\n<code style='background-color:{bgcolor}'>{' '*len(str(amount))}{'.'}</code>\n"  
            bot.send_message(message.chat.id, f'{table}', parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, 'Нет данных о расходах за текущий месяц.')



    
    cur.close()
    conn.close()
    main_menu(message)

# Обработчик выбора периода для сводки расходов
@bot.message_handler(func=lambda message: message.text in ['Сводка расходов за сегодня', 'Сводка расходов за вчера','Сводка расходов за неделю', 'Сводка расходов с начала месяца'])
def show_stats(message):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    cur = conn.cursor()
    
    if message.text == 'Сводка расходов за сегодня':
        sql = "SELECT SUM(amount) AS total_cost FROM finance.costs WHERE date = CURRENT_DATE"
    elif message.text == 'Сводка расходов за вчера':
        sql = "SELECT SUM(amount) AS total_cost FROM finance.costs WHERE date = CURRENT_DATE - INTERVAL '1 day'"
    elif message.text == 'Сводка расходов за неделю':
        sql = "SELECT SUM(amount) AS total_cost FROM finance.costs WHERE date >= CURRENT_DATE - INTERVAL '7 days'"
        ############################
        cur.execute(sql)
        total_cost = cur.fetchone()[0]
        if total_cost is None:
            total_cost = 0
        bot.send_message(message.chat.id, f'Сумма расходов за неделю: {total_cost}')
        dashboard.show_weekly_stats(bot, message)
        return
        ##########
    elif message.text == 'Сводка расходов с начала месяца':
        sql = "SELECT SUM(amount) AS total_cost FROM finance.costs WHERE date >= DATE_TRUNC('month', CURRENT_DATE)"
        ############################
        cur.execute(sql)
        total_cost = cur.fetchone()[0]
        if total_cost is None:
            total_cost = 0
        bot.send_message(message.chat.id, f'Сумма расходов за месяц: {total_cost}')
        dashboard.show_monthly_stats(bot, message)
        return
        ##########
    cur.execute(sql)
    total_cost = cur.fetchone()[0]
    if total_cost is None:
        total_cost = 0
    bot.send_message(message.chat.id, f'Сумма расходов: {total_cost}')
    
    cur.close()
    conn.close()
    main_menu(message)

#### Выбор источника прихода
@bot.message_handler(func=lambda message: message.text == '💰 Приход')
def income_source(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_1 = types.KeyboardButton('Соколов')
    btn_2 = types.KeyboardButton('Академ')
    markup.row(btn_1, btn_2)
    btn_3 = types.KeyboardButton('Дикси')
    btn_4 = types.KeyboardButton('Другое')
    markup.row(btn_3, btn_4)
    bot.send_message(message.chat.id, 'Выбери источник', reply_markup=markup)

#### Выбор аван изи зп в случае прихода
@bot.message_handler(func=lambda message: message.text in ['Соколов', 'Академ', 'Дикси'])
def income_source(message):
    markup = types.ReplyKeyboardMarkup()
    btn_1 = types.KeyboardButton('Аванс')
    markup.row(btn_1)
    btn_2 = types.KeyboardButton('ЗП')
    markup.row(btn_2)
    bot.send_message(message.chat.id, 'Выбери что именно пришло', reply_markup=markup)

#### Выбор источника расходов
@bot.message_handler(func=lambda message: message.text == '😫 Расход')
def costs_source(message):
    markup = types.ReplyKeyboardMarkup()
    btn_1 = types.KeyboardButton('Квартира')
    btn_2 = types.KeyboardButton('Кредит')
    markup.row(btn_1, btn_2)
    btn_3 = types.KeyboardButton('Аптека')
    btn_4 = types.KeyboardButton('ВкусМил')
    markup.row(btn_3, btn_4)
    btn_5 = types.KeyboardButton('Продукты')
    btn_6 = types.KeyboardButton('Быт')
    markup.row(btn_5, btn_6)
    btn_7 = types.KeyboardButton('Кафе и фастфуд')
    btn_8 = types.KeyboardButton('Коммуналка и интернет')
    markup.row(btn_7, btn_8)
    btn_9 = types.KeyboardButton('Такси и самокаты')
    btn_10 = types.KeyboardButton('Транспорт')
    markup.row(btn_9, btn_10)
    btn_11 = types.KeyboardButton('Стоматолог')
    btn_12 = types.KeyboardButton('Красота')
    markup.row(btn_11, btn_12)
    btn_13 = types.KeyboardButton('Прочее')
    btn_14 = types.KeyboardButton('Доставка')
    markup.row(btn_13,  btn_14)
    btn_15 = types.KeyboardButton('Отложить 20%')
    btn_16 = types.KeyboardButton('Психолог')
    markup.row(btn_15, btn_16)
    btn_17 = types.KeyboardButton('WildBerries')
    btn_18 = types.KeyboardButton('Самокат')
    markup.row(btn_17, btn_18)
    bot.send_message(message.chat.id, 'Выбери источник расходов', reply_markup=markup)

#### Введдение суммы расхода или прихода
@bot.message_handler(func=lambda message: message.text in ['ЗП', 'Аванс', 'Другое'])
def sum_income(message):
    global type,source
    type = 'income'
    source = message.text
    bot.send_message(message.chat.id, 'Введи сумму прихода', reply_markup=None)


#### Введдение суммы расхода или прихода
@bot.message_handler(func=lambda message: message.text in ['Квартира', 'Кредит','Аптека','ВкусМил','Продукты','Быт','Кафе и фастфуд','Коммуналка и интернет',
                                                            'Такси и самокаты', 'Транспорт', 'Стоматолог', 'Красота', 'Прочее', 'Доставка', 'Отложить 20%', 'Психолог','WildBerries','Самокат'])
def sum_costs(message):
    global type, source
    type = 'costs'
    source = message.text
    bot.send_message(message.chat.id, 'Введи сумму расходов', reply_markup=None)


@bot.message_handler(func=lambda message: not message.text.isdigit())
def handle_invalid_input(message):
    bot.send_message(message.chat.id, 'Введите только числовое значение. Повторите ввод.')


def save_to_database(date, type, source, amount):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    cur = conn.cursor()

    sql = "INSERT INTO finance.costs (date, type, source, amount) VALUES (%s, %s, %s, %s)"
    values = (date, type, source, amount)
    cur.execute(sql, values)
    conn.commit()
    cur.close()
    conn.close()


@bot.message_handler(func=lambda message: message.text.isdigit())
def save_amount(message):
    amount = message.text
    current_date = datetime.now()
    save_to_database(current_date, type, source, amount)
    bot.send_message(message.chat.id, 'Сумма успешно сохранена!')
    
    main_menu(message)



bot.infinity_polling(none_stop=True)
