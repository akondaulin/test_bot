import psycopg2
from config import dbname, user, password, port, host
import io
import matplotlib.pyplot as plt

def get_weekly_costs():
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cur = conn.cursor()
        sql = "SELECT date, SUM(amount) FROM finance.costs WHERE date >= CURRENT_DATE - INTERVAL '7 days' GROUP BY date ORDER BY date"
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except psycopg2.Error as e:
        print("Error fetching data from database:", e)
        return []


def show_weekly_stats():
    rows = get_weekly_costs()
    if rows:
        dates = [row[0] for row in rows]
        amounts = [row[1] for row in rows]

        plt.figure(figsize=(10, 6))
        plt.plot(dates, amounts, marker='o')
        plt.title('График расходов за неделю')
        plt.xlabel('Дата')
        plt.ylabel('Сумма расходов')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()

        bot.send_photo(message.chat.id, buffer, caption='График расходов за неделю')
    else:
        bot.send_message(message.chat.id, 'Нет данных о расходах за последнюю неделю.')

show_weekly_stats()