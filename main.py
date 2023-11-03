import requests
from bs4 import BeautifulSoup as bs
import lxml
import datetime
import csv
import telebot
from telebot import types
import time


bot = telebot.TeleBot("PUT YOUR TOKEN HERE!)))")  

start_button = types.KeyboardButton("/start")
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(start_button)
article_data_file = "article_data.csv"
article_data = None

def read_article_data():
    try:
        with open(article_data_file, "r") as file:
            reader = csv.DictReader(file)
            article_data = {}
            for row in reader:
                i = int(row["counter"])
                title = row["title"]
                photo = row["photo"]
                description = row["description"]
                article_data[i] = {
                    "title": title,
                    "photo": photo,
                    "description": description
                }
            return article_data
    except FileNotFoundError:
        return None

@bot.message_handler(func=lambda message: message.text == "/start")
def handle_start(message):
    start(message)


def start(message):
    global article_data
    if article_data is None:
        bot.send_message(message.chat.id, "Подождите, идет загрузка данных...")

        time.sleep(1)

        article_data = get_title_photo(html)
        write_article_data(article_data)
        bot.send_message(message.chat.id, "Данные загружены!")

        time.sleep(1)

    for i in range(1, 21):
        article = article_data.get(i)
        if article:
            bot.send_message(message.chat.id, f"{i}. {article['title']}")
            
            markup = telebot.types.InlineKeyboardMarkup()
            description_button = telebot.types.InlineKeyboardButton("Описание", callback_data=f"description_{i}")
            photo_button = telebot.types.InlineKeyboardButton("Фото", callback_data=f"photo_{i}")
            markup.add(description_button, photo_button)

            bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("description_") or call.data.startswith("photo_"))
def handle_callback_query(call):
    option, number = call.data.split("_")
    article = article_data.get(int(number))
    if article:
        if option == "description":
            bot.send_message(call.message.chat.id, f"Описание: {article['description']}")
        elif option == "photo":
            bot.send_message(call.message.chat.id, f"Ссылка на фото: {article['photo']}")



def get_html(url):
    response = requests.get(url)
    return response.text

def get_title_photo(html):
    soup = bs(html, "lxml")
    catalog = soup.find('div', class_ = "Tag--articles").find_all("div", class_ = "Tag--article")
    counter = 1
    
    article_data_with_counter = {}
    
    for i in catalog:
        if counter <= 20:
            article = i.find("div", class_ = "ArticleItem")
            article_title = article.find('a', class_ = "ArticleItem--name").text.strip()
            article_photo = article.find('a', class_ = "ArticleItem--image").find("img").get("src")
            article_description_link = article.find('a', class_ = "ArticleItem--name").get('href')
            description_html = get_html(article_description_link)
            article_description = get_description_data(description_html)
            data = {}
            data.update({'title': article_title})
            data.update({'photo': article_photo})
            data.update({'description': article_description})

            article_data_with_counter.update({counter:data})
            counter += 1

    write_article_data(article_data_with_counter)
    return article_data_with_counter

  
def get_article_description_html(desc_url):
    desc_response = requests.get(desc_url)
    return desc_response.text
def get_description_data(desc_html):
    soup = bs(desc_html, "lxml")
    article_descriprition = soup.find('p').text
    return article_descriprition

def news_today():
    date_time = datetime.datetime.now()
    date = str(date_time)[:10]
    url = f'https://kaktus.media/?lable=8&date={date}&order=time'
    return url

def write_article_data(data):
    with open(article_data_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["counter", "title", "photo", "description"])
        for i in range(1, 21):
            article = data.get(i)
            if article:
                writer.writerow([i, article['title'], article['photo'], article['description']])



html = get_html(news_today())
get_title_photo(html)

bot.polling()
