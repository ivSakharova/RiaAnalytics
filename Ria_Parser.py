from datetime import datetime, date, timedelta
import time
import html5lib
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import json
MONTH_DICT = {"января":1, "февраля":2, "марта":3, "апреля":4, "мая":5, "июня":6, "июля":7, "августа":8, "сентября":9, "октября":10, "ноября":11, "декабря":12}
class RiaParser:
    main_url = 'https://ria.ru/politics'
    d_news = {}
    d_news['politics'] = []

    def __init__(self, start_date, end_date = datetime.today):
        self.start_date = start_date
        self.end_date = end_date


    def text_to_date(self, text_date:str): #перевод даты новостей в списке в формат datetime
        if text_date.find(","):
            date_and_time = text_date.split(",")
            if date_and_time[0] == "Вчера":
                news_date = date.today() - timedelta(days=1)
            else:
                arr_date = date_and_time[0].split()
                news_date = date(2023, MONTH_DICT[arr_date[1]], int(arr_date[0]))
            arr_time=date_and_time[1].split(":")
        else:
            news_date = date.today()
            arr_time = text_date.split(":")
        return datetime(news_date.year, news_date.month, news_date.day, int(arr_time[0]), int(arr_time[1]))

    def text_to_date_for_item (self, text_date:str): #перевод даты каждой новости в формат datetime
        arr_date_time = text_date.split()
        arr_time = arr_date_time[0].split(":")
        arr_date = arr_date_time[1].split(".")
        return datetime(int(arr_date[2]), int(arr_date[1]), int(arr_date[0]), int(arr_time[0]), int(arr_time[1]))


    def find_news(self): # обработка списка новостей
        href = RiaParser.main_url
        chrome_options = Options()#Скроллинг новостей в первый раз
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('window-size=750,500')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(href)
        driver.find_element_by_class_name('list-more').click()
        date_last_element = driver.find_elements_by_class_name('list-item__date')[-1].text
        date_last_element = RiaParser.text_to_date(self, date_last_element)
        
        while (date_last_element > self.start_date): # скролинг новостей до нужной даты
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight-1000);") 
            date_last_element = driver.find_elements_by_class_name('list-item__date')[-1].text
            date_last_element = RiaParser.text_to_date(self, date_last_element)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html5lib')  
        news = soup.find_all('div', class_='list-item')
        for new in news: #парсинг каждой новости в списке
            item_url = new.find('a')
            item_url = item_url['href']
            arr_news_info = (self.news_info(item_url))

            if (arr_news_info == -1):
                break
            else:
                if arr_news_info != None:
                    self.d_news['politics'].append(arr_news_info)
        driver.quit()
        return (self.d_news)

    def news_info(self, href: str):#загрузка js-скриптов для получения данных о реакции пользователей
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(href)
        time.sleep(1)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html5lib')

        d_item={}#получение данных о конкретной новости
        item_date = soup.find('div', class_='article__info-date')
        item_date = item_date.find('a').text
        item_date_time = self.text_to_date_for_item(item_date)
        if (item_date_time <= self.end_date):
            if (item_date_time >= self.start_date):
                item_title = soup.find(class_='article__title').text
                d_item['title'] = item_title
                d_item['url'] = href
                d_item['date'] = str(item_date_time)
                item_views=soup.find('span', class_='article__views').text
                item_views = item_views.split("\n")
                d_item['views'] = item_views[0]
                item_ratings = soup.find('div', class_='emoji')
                item_rating = item_ratings.find_all('a', class_ = re.compile("emoji-item*"))
                arr_rating = []
                for rating in item_rating: #  данные о реакции пользователей на новость
                    arr_rating.append(rating.find('span').text)
                d_item['rating'] = arr_rating
                arr_tags = []
                item_tags = soup.find_all('a', class_='article__tags-item')
                for item_tag in item_tags: #теги, присущие каждой новости
                    arr_tags.append(item_tag.text)
                d_item['tags'] = arr_tags
                driver.quit()
                return (d_item)
            else:
                return (-1)


parser = RiaParser(datetime(2023, 7, 25), datetime(2023, 7, 26))
parser.find_news()
with open('parse_data.json', 'w') as fw:
    json.dump(parser.d_news, fw)
print ("Парсинг данных завершен")





