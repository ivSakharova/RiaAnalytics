import pymysql
import json
from pymysql.cursors import DictCursor
#import Ria_Parser
import matplotlib
from matplotlib import pyplot as plt
import pandas as pd
import matplotlib.ticker as mtick
#file='parse_data.json'
connection=''


class Data_processing:

    def connect_database(self):#подключение к бд
        global connection
        try:
            connection = pymysql.connect(
                host='localhost',
                user='root',
                db='rianews',
                charset='utf8mb4',
                cursorclass=DictCursor
            )
            print('Подключение успешно')
        except:
            print('Ошибка подключения к базе данных')
        return self


    @connect_database
    def __init__(self):
        self.name = "1"

    
    def insert(self, file:str): #добавление данных, полученных ранее парсером
        global connection

        check_id = """
        SELECT max(ID) from news 
        """
        with connection.cursor() as cursor:
            cursor.execute(check_id)
            max_id = cursor.fetchall()
    
        i = max_id
        i = i[0]['max(ID)']
        if i == None:
            i = 0
        
        with open(file) as f:
            arr_data = json.load(f)
            d_news = []
            d_tags = []
            d_news_tags = []
            arr_tags = []
            arr_data_news = arr_data['politics'] #другие категории будут дорабатываться позже
            j = 0
            for new in arr_data_news: #получение данных из json файла о каждой новости
                arr_t = []
                d_news_tags.append([])
                i = i + 1
                d_news_tags[j].append(i)
                d_news.append((i, new['url'], new['title'], '1', new['views'], new['rating'][0], new['rating'][1], new['rating'][2], new['rating'][3], new['rating'][4], new['rating'][5], new['date']))
                for tag in new['tags']:
                    arr_tags.append(tag)
                    if d_tags.count(tag) == 0:
                        d_tags.append(tag)
                for t in arr_tags: #создание связи между новостями и тегами для бд
                    arr_t.append(t)
                d_news_tags[j].append(arr_t)
                j = j + 1
        insert_tags = """
        INSERT IGNORE INTO tags (name)
        VALUES
        (%s)
        """

        insert_news = """
        INSERT INTO news (ID, url, title, topic_ID, views, rating_5, rating_4, rating_3, rating_2, rating_1, rating_0, date)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    
        with connection.cursor() as cursor:
            cursor.executemany(insert_tags, d_tags)
            cursor.executemany(insert_news, d_news)
            connection.commit()


        check_tags_id = """
        SELECT ID from tags
        WHERE name = %s
        """

        insert_news_tags = """
        INSERT INTO newsandtags (News_ID, Tags_ID)
        VALUES
        (%s, %s)
        """
        arr_ins_tag_name = []
        for d_n_t in d_news_tags: #проверка для избежания копий данных
            check_double = ''
            for tag_name in d_n_t[1]:
                with connection.cursor() as cursor:
                    cursor.execute(check_tags_id, tag_name)
                    t_id = cursor.fetchone()['ID']
                    if (d_n_t[0], t_id) != check_double:
                        arr_ins_tag_name.append((d_n_t[0], t_id))
                    else:
                        continue
                    check_double = (d_n_t[0], t_id)
        with connection.cursor() as cursor:
            cursor.executemany(insert_news_tags, arr_ins_tag_name)
            connection.commit()
            print("Данные обновлены")


    def visualize(self): #построение графиков для визуализации полученных данных
            select_views = """ SELECT  sum(views) as views, date FROM news GROUP BY date(date) """
            #select_date = """ SELECT date FROM news"""
            with connection.cursor() as cursor:
                cursor.execute(select_views)
                data_views = cursor.fetchall()
                connection.commit()

            fig = plt.figure(figsize=(15,15))
            plt.subplots_adjust(wspace = 0.4, hspace = 0.4)
            
            ax1 = fig.add_subplot(224)
            ax2 = fig.add_subplot(223)
            ax3 = fig.add_subplot(211)


            df_views = pd.DataFrame(data_views) #график зависимости просмотров от времени
            df_views['views'] = df_views['views'].astype(int)
            df_views.plot(x = 'date', y = 'views', ax = ax1)
            plt.gcf().canvas.set_window_title('Визуализация данных')
            ax1.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            ax1.legend().set_visible(False)
            ax1.set_xlabel('')
            ax1.set_title('Зависимость просмотров от времени', size = 16)
            
            #круговая диаграмма наиболее часто использующихся тегов
            select_tags = """ 
            SELECT count(Tags_ID) AS count, tags.name AS tag
            FROM newsandtags
            JOIN tags ON newsandtags.Tags_ID = tags.ID
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 15 """
            with connection.cursor() as cursor:
                cursor.execute(select_tags)
                data_tags = cursor.fetchall()
                connection.commit()
            df_tags = pd.DataFrame(data_tags)
            df_tags.columns = ['Count', 'Tag']
            df_tags.plot(y = 'Count', labels = df_tags['Tag'], kind = 'pie', ax = ax2, textprops = {'fontsize': 8})
            ax2.legend().set_visible(False)
            ax2.yaxis.set_visible(False)
            ax2.set_title('Частота использований различных тегов к новости', size = 16)
            #гистограмма, отображающая реакции пользователей на новоcти (по номеру недели)
            select_reactions = """ 
            SELECT SUM(rating_0) as r_5 , SUM(rating_1) as r_0, SUM(rating_2) as r_4 , SUM(rating_3) as r_3, SUM(rating_4) as r_2, SUM(rating_5) as r_1, WEEK(DATE) AS date
            FROM `news`
            GROUP BY WEEK(date)""" 
            with connection.cursor() as cursor:
                cursor.execute(select_reactions)
                data_reactions = cursor.fetchall()
                connection.commit()
            df_reactions = pd.DataFrame(data_reactions)
            df_reactions['sum'] = df_reactions['r_5']+df_reactions['r_4']+df_reactions['r_3']+df_reactions['r_2']+df_reactions['r_1']+df_reactions['r_0']
            for i in range(6): # перевод числовых данных в процентное соотношение
                str_i_percent = f'r_{i}_percent'
                str_i = f'r_{i}'
                df_reactions[str_i_percent] = df_reactions[str_i]/df_reactions['sum']*100
                df_reactions[str_i_percent] = df_reactions[str_i_percent].astype(float)
            df_reactions.rename(columns = {'r_0_percent':'dislike', 'r_1_percent':'awful', 'r_2_percent':'bad','r_3_percent':'neutral','r_4_percent':'good', 'r_5_percent':'like'}, inplace = True )
            df_reactions.plot(x = 'date', y = ['dislike', 'awful', 'bad', 'neutral', 'good','like'], kind = 'bar', ax = ax3)
            #ax3.yaxis.set_visible(False)
            ax3.set_title('Реакция пользователей на новости', size = 16)
            ax3.yaxis.set_major_formatter(mtick.PercentFormatter())
            ax3.set_xlabel('')
            plt.show()
            

data_object = Data_processing()
#data_object.insert(file)
data_object.visualize()

