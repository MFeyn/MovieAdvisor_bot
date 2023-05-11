import datetime

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import telebot

from config import TOKEN

plt.style.use('ggplot')

bot = telebot.TeleBot(TOKEN)
df = pd.read_excel('TestBD_xlsx.xlsx', engine='openpyxl')


def send_ranked_list(message, dataframe):
    ranked_list_str = '*Твои фильмы*\n'
    ranked_list_str += dataframe.sort_values('score', ignore_index=True).head().to_string(columns=['name', 'score'],
                                                                                          header=False,
                                                                                          index=True,
                                                                                          ).replace('  ', ' ')
    bot.send_message(message.chat.id, ranked_list_str)


def send_ranked_list_more(message, dataframe):
    ranked_df = dataframe.sort_values('score', ignore_index=True)
    bot.send_message(message.chat.id, '<b>Твой ТОП 5 фильмов</b>\n', parse_mode='HTML')
    nums = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
    for i in range(0, 5):
        strg = ranked_df.iloc[i]
        bot.send_message(message.chat.id,
                         '{:<} <b>{:<}</b>, {:<}\n'.format(nums[i], strg[0], strg[1]) +
                         '\U0001F30F {:<}\n\U00002B50 {:<}\n'.format(strg[2], strg[3]) +
                         '<i>{:<}</i>\n\U000023F3 Продолжительность: {:4<}мин\n'.format(
                             strg[4].replace(']', ' ').replace('[', ' '), strg[9]) +
                         '\U00002B55 {:4<}+\nОписание: {:<}'.format(strg[11], strg[7]), parse_mode='HTML')


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет! Я твой друг-киносоветчик 💫')
    bot.send_message(message.chat.id, 'У тебя бывало такое, когда просишь друзей ' +
                     'посоветовать фильм, а никто ничего не может вспомнить:(' +
                     '\nЯ могу помочь с этим!')
    bot.send_message(message.chat.id, 'Бот позволяет сохранять информацию о фильмах, которые ты или твои друзья ' +
                     'посмотрели. В тот момент, когда ты захочешь посмотреть фильм, ' +
                     'можешь просто ответить на ряд вопросов и получить рекомендацию (и не нужно никого ' +
                     'мучить вопросами)')
    bot.send_message(message.chat.id, 'Так ты точно сможешь найти фильм по душе:)')
    bot.send_message(message.chat.id,
                     '/choose – для подбора фильма 🤪')


@bot.message_handler(commands=['choose'])
def start_choose(message):
    df['score'] = 0
    df.index = np.arange(1, len(df) + 1)
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard.row('Готов!', 'Нет')
    bot.send_message(message.chat.id,
                     'Начнём подбор фильма! Сейчас в нашей базе ' + str(len(df.index)) + ' крутых фильмов. ' +
                     'Я задам тебе ряд вопросов, и мы найдём лучший.')
    bot.send_message(message.chat.id, 'Ты готов(а) начать?', reply_markup=keyboard)
    bot.register_next_step_handler(message, send_first_q)


def send_first_q(message):
    if message.text.lower() == 'нет':
        bot.send_message(message.chat.id, 'Ну, на нет и суда нет')
        bot.register_next_step_handler(message, start_message)
    else:
        bot.send_message(message.chat.id, '1️⃣ Оцени по шкале от -5 до 5, насколько фильм должен быть динамичным')
        bot.send_message(message.chat.id, 'Спокойный 😌 -5  –––  5 😈 Динамичный')
        bot.register_next_step_handler(message, get_x_coor)


def get_x_coor(message):
    user_x_coor = message.text
    if user_x_coor.lstrip('-').isdigit():
        user_x_coor = int(user_x_coor)
        if (-5 <= user_x_coor) and (user_x_coor <= 5):
            bot.send_message(message.chat.id, '2️⃣ А по такой шкале?')
            bot.send_message(message.chat.id, 'На подумать 🤔 -5  –––  5 Почиллить 😎')
            bot.register_next_step_handler(message, get_y_coor, user_x_coor)
        else:
            bot.send_message(message.chat.id,
                             'Упс, кажется, ты ввёл число, которое нельзя использовать в этой шкале:(' +
                             ' Попробуй снова. Например, введи 1.')
            bot.register_next_step_handler(message, get_x_coor)
    else:
        bot.send_message(message.chat.id, 'Упс, кажется, ты ввёл не число. Попробуй снова. Например, введи 1.')
        bot.register_next_step_handler(message, get_x_coor)


def get_y_coor(message, user_x_coor):
    user_y_coor = message.text
    if user_y_coor.lstrip('-').isdigit():
        user_y_coor = int(user_y_coor)
        if (-5 <= user_y_coor) and (user_y_coor <= 5):
            df.score = np.power(df.coord_x - user_x_coor, 2) + np.power(df.coord_y - user_y_coor, 2)
            df.score = df.score.rank()
            df.loc[df['score'] > 5, 'score'] = 5
            send_ranked_list(message, df)

            keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            keyboard.row('Один', 'С друзьями')

            bot.send_message(message.chat.id, '3️⃣ С кем хочешь посмотреть фильм?', reply_markup=keyboard)
            bot.register_next_step_handler(message, get_need_company)
        else:
            bot.send_message(message.chat.id,
                             'Упс, кажется, ты ввёл число, которое нельзя использовать в этой шкале:(' +
                             ' Попробуй снова. Например, введи 1.')
            bot.register_next_step_handler(message, get_y_coor)
    else:
        bot.send_message(message.chat.id, 'Упс, кажется, ты ввёл не число. Попробуй снова. Например, введи 1.')
        bot.register_next_step_handler(message, get_y_coor)


def get_need_company(message):
    if message.text.lower() == 'один':
        df.loc[df['need_company'] == 0, 'score'] += 1
        df.loc[df['need_company'] != 0, 'score'] += 5
        send_ranked_list(message, df)
        bot.send_message(message.chat.id, '4️⃣ А теперь укажи желаемый год выхода фильма')
        bot.register_next_step_handler(message, get_year)

    elif message.text.lower() == 'с друзьями':
        df.loc[df['need_company'] == 0, 'score'] += 5
        df.loc[df['need_company'] != 0, 'score'] += 1
        send_ranked_list(message, df)
        bot.send_message(message.chat.id, '4️⃣ А теперь укажи желаемый год выхода фильма')
        bot.register_next_step_handler(message, get_year)

    else:
        bot.send_message(message.chat.id, 'Нажми на кнопку ниже или напиши "один" и "с друзьями")')
        bot.register_next_step_handler(message, get_need_company)


def get_year(message):
    user_year = message.text
    if user_year.isdigit():
        user_year = int(user_year)
        now = datetime.datetime.now()
        if (1895 <= user_year) and (user_year <= int(now.year)):
            df.loc[np.absolute(df['year'] - user_year) < 5, 'score'] += np.absolute(df['year'] - user_year) + 1
            df.loc[np.absolute(df['year'] - user_year) >= 5, 'score'] += 5
            send_ranked_list(message, df)
            bot.send_message(message.chat.id, '5️⃣ Каким должен быть минимальный рейтинг фильма на Кинопоиске?\n' +
                             'Введи число от 0 до 10')
            bot.register_next_step_handler(message, get_rating_company)
        else:
            bot.send_message(message.chat.id, 'Ты выбрал очень странный год выхода для фильма... ' +
                             'Попробуй снова. Например, введи 2014.')
            bot.register_next_step_handler(message, get_year)
    else:
        bot.send_message(message.chat.id, 'Упс, кажется, ты ввёл не число. Попробуй снова. Например, введи 2014.')
        bot.register_next_step_handler(message, get_year)


def get_rating_company(message):
    user_rating = message.text
    if user_rating.isdigit():
        user_rating = int(user_rating)
        if (0 <= user_rating) and (user_rating <= 10):
            df.loc[df['rating'] >= user_rating, 'score'] += 1
            df.loc[df['rating'] < user_rating, 'score'] += 5
            send_ranked_list(message, df)

            keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            keyboard.row('Люблю наше',
                         'Люблю зарубеж', )

            bot.send_message(message.chat.id, '6️⃣ Отечественный или зарубежный фильм?', reply_markup=keyboard)
            bot.register_next_step_handler(message, get_origin)
        else:
            bot.send_message(message.chat.id, 'Оценка на Кинопоиске выставляется по шкале от 0 до 10\n' +
                             'Попробуй снова. Например, введи 8.')
            bot.register_next_step_handler(message, get_rating_company)

    else:
        bot.send_message(message.chat.id, 'Упс, кажется, ты ввёл не число. Попробуй снова. Например, введи 7.')
        bot.register_next_step_handler(message, get_rating_company)


def get_origin(message):
    if message.text == 'Люблю наше':
        df.loc[df['origin'] == 'отечественный', 'score'] += 1
        df.loc[df['origin'] == 'зарубежный', 'score'] += 5
        go_to_genres(message)

    elif message.text == 'Люблю зарубеж':
        df.loc[df['origin'] == 'отечественный', 'score'] += 5
        df.loc[df['origin'] == 'зарубежный', 'score'] += 1
        go_to_genres(message)

    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю(\nНажми на кнопку ниже.')
        bot.register_next_step_handler(message, get_origin)


def go_to_genres(message):
    send_ranked_list(message, df)
    bot.send_message(message.chat.id, 'Здорово!\n7️⃣ Самый сложный выбор: фильм какого жанра ты бы хотел посмотреть?')
    genres_set = set(df['genre'].sum().replace(']', ' ').replace('[', ' ').replace(',', ' ').split())
    s = '- '
    for x in genres_set:
        s += '{} - '.format(x)
    bot.send_message(message.chat.id, 'Выбери столько, сколько захочешь и напиши их через пробел:')
    bot.send_message(message.chat.id, s)
    bot.register_next_step_handler(message, get_genre, genres_set)


def get_genre(message, genres_set):
    user_genres_str = message.text.lower()
    user_genres = set(user_genres_str.split())
    if user_genres <= genres_set:
        rank_step = 5 / len(user_genres)
        df.score += 6
        for i in user_genres:
            df.loc[df['genre'].str.contains(i), 'score'] -= rank_step
        send_ranked_list(message, df)
        platforms_set = set(df['platform'].sum().replace(']', ' ').replace('[', ' ').replace(',', ' ').split())
        s = '- '
        for x in platforms_set:
            s += '{} - '.format(x)
        bot.send_message(message.chat.id,
                         '8️⃣ А какую платфрому предпочитаешь для просмотра? Укажи в порядке приоритета ' +
                         'перечисленные ниже платформы через пробел.')
        bot.send_message(message.chat.id, s)
        bot.register_next_step_handler(message, get_platform, platforms_set)
    else:
        bot.send_message(message.chat.id, 'К сожалению, пока никто не смотрел фильмы такого жанра. ' +
                         'Попробуй другие жанры')
        bot.register_next_step_handler(message, get_genre, genres_set)


def get_platform(message, platforms_set):
    user_platforms_str = message.text.lower()
    user_platforms = user_platforms_str.split()
    user_platforms = list(dict.fromkeys(user_platforms))
    if set(user_platforms) <= platforms_set:
        rank_step = 5 / len(user_platforms)
        df.score += 6
        step = rank_step / (len(user_platforms))
        for i in user_platforms:
            df.loc[df['platform'].str.contains(i), 'score'] -= rank_step
            rank_step -= step
        send_ranked_list(message, df)
        keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        keyboard.row('Покороче',
                     'Подлиннее')
        bot.send_message(message.chat.id, '9️⃣ Любишь фильмы подлиннее или покороче?', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_time)
    else:
        bot.send_message(message.chat.id, 'К сожалению, не могу найти фильмы на твоей платформе. ' +
                         'Попробуй другие платформы')
        bot.register_next_step_handler(message, get_platform, platforms_set)


def get_time(message):
    movie_length = message.text.lower()
    print(movie_length)
    avg_length = df['duration'].mean()
    if movie_length == 'покороче':
        df.loc[df['duration'] < avg_length, 'score'] += 1
        df.loc[df['duration'] >= avg_length, 'score'] += 5
        go_to_budget(message)
    elif movie_length == 'подлиннее':
        df.loc[df['duration'] < avg_length, 'score'] += 5
        df.loc[df['duration'] >= avg_length, 'score'] += 1
        go_to_budget(message)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю :(\nНажми на кнопку ниже.')
        bot.register_next_step_handler(message, get_time)


def go_to_budget(message):
    send_ranked_list(message, df)
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard.row('Бюджет выше среднего',
                 'Бюджет ниже среднего',
                 'Средний бюджет')
    bot.send_message(message.chat.id, '🔟 Какой бюджет должен быть у твоего фильма?', reply_markup=keyboard)
    bot.register_next_step_handler(message, get_budget)


def get_budget(message):
    movie_budget = message.text.lower()
    avg_budget = df['budget'].mean()
    print(avg_budget)
    if movie_budget == 'бюджет выше среднего':
        df.loc[df['budget'] > avg_budget, 'score'] += 1
        df.loc[df['budget'] <= avg_budget, 'score'] += 5
        go_to_pg(message)
    elif movie_budget == 'бюджет ниже среднего':
        df.loc[df['budget'] >= avg_budget, 'score'] += 5
        df.loc[df['budget'] < avg_budget, 'score'] += 1
        go_to_pg(message)
    elif movie_budget == 'средний бюджет':
        df.loc[(df['budget'] >= avg_budget - (0.1 * avg_budget)) & (df['budget'] < avg_budget + (0.1 * avg_budget)),
        'score'] += 1
        df.loc[(df['budget'] < avg_budget - (0.1 * avg_budget)) | (df['budget'] > avg_budget + (0.1 * avg_budget)),
        'score'] += 5
        go_to_pg(message)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю :(\nНажми на кнопку ниже.')
        bot.register_next_step_handler(message, get_budget)


def go_to_pg(message):
    send_ranked_list(message, df)
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard.row('0+',
                 '6+',
                 '12+',
                 '16+',
                 '18+')
    bot.send_message(message.chat.id, '1️⃣1️⃣ Фильмы с каким рейтингом предпочитаешь в это время суток?',
                     reply_markup=keyboard)
    bot.register_next_step_handler(message, get_pg)


def get_pg(message):
    user_pg = message.text.lower()
    pg = user_pg.replace('+', '')
    pg = int(pg)
    if user_pg in ['0+', '6+', '12+', '16+', '18+']:
        df.loc[df['pg'] == pg, 'score'] += 1
        df.loc[df['pg'] != pg, 'score'] += 5
        send_ranked_list(message, df)
        keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        keyboard.row('Конечно, на проекторе 📽')
        keyboard.row('На компьютере 💻', 'На телефоне 📱')

        bot.send_message(message.chat.id, '1️⃣2️⃣ На каком экране хочешь посмотреть фильм?', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_screen)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю :(\nНажми на кнопку ниже.')
        bot.register_next_step_handler(message, get_pg)


def get_screen(message):
    if message.text == 'Конечно, на проекторе 📽':
        screen_code = 1
    elif message.text == 'На компьютере 💻':
        screen_code = 2
    elif message.text == 'На телефоне 📱':
        screen_code = 3
    else:
        screen_code = 0
    if screen_code > 0:
        df.loc[df['screen'] - screen_code == 0, 'score'] += 1
        df.loc[df['screen'] - screen_code != 0, 'score'] += 2.5 * np.absolute(df.screen - screen_code)
        send_ranked_list(message, df)

        keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        keyboard.row('Да ✅', 'Нет ❌')

        bot.send_message(message.chat.id, '1️⃣3️⃣ "Этот фильм я бы точно хотел пересмотреть". ' +
                         'Хотел бы сказать так о фильме, который ищешь?', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_rewatch)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю(\nНажми на кнопку ниже.')
        bot.register_next_step_handler(message, get_screen)


def get_rewatch(message):
    if message.text in ['Да ✅', 'Нет ❌']:
        if message.text == 'Да ✅':
            df.loc[df['rewatch'] == 1, 'score'] += 1
            df.loc[df['rewatch'] == 0, 'score'] += 5
        elif message.text == 'Нет ❌':
            df.loc[df['rewatch'] == 1, 'score'] += 5
            df.loc[df['rewatch'] == 0, 'score'] += 1
        send_ranked_list(message, df)

        keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        keyboard.row('Да ✅', 'Нет ❌')

        bot.send_message(message.chat.id, '1️⃣4️⃣ А покушать во время просмотра хочешь?', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_food)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю(\nНажми на кнопку ниже.')
        bot.register_next_step_handler(message, get_rewatch)


def get_food(message):
    if message.text in ['Да ✅', 'Нет ❌']:
        if message.text == 'Да ✅':
            df.loc[df['food'] == 1, 'score'] += 1
            df.loc[df['food'] == 0, 'score'] += 5
        elif message.text == 'Нет ❌':
            df.loc[df['food'] == 1, 'score'] += 5
            df.loc[df['food'] == 0, 'score'] += 1
        send_ranked_list(message, df)

        keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        keyboard.row('Да ✅', 'Нет ❌')

        bot.send_message(message.chat.id, '1️⃣5️⃣ Под Новый год выбираешь фильм?)', reply_markup=keyboard)
        bot.register_next_step_handler(message, get_new_year)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю(\nНажми на кнопку ниже.')
        bot.register_next_step_handler(message, get_rewatch)


def get_new_year(message):
    if message.text in ['Да ✅', 'Нет ❌']:
        if message.text == 'Да ✅':
            df.loc[df['new_year'] == 1, 'score'] += 1
            df.loc[df['new_year'] == 0, 'score'] += 5
        elif message.text == 'Нет ❌':
            df.loc[df['new_year'] == 1, 'score'] += 5
            df.loc[df['new_year'] == 0, 'score'] += 1

        bot.send_message(message.chat.id, 'Фуууух. Ты подошёл к концу! Лови свой персональный топ фильмов')
        send_ranked_list_more(message, df)
        bot.register_next_step_handler(message, get_new_year)
    else:
        bot.send_message(message.chat.id, 'Я тебя не понимаю(\nНажми на кнопку ниже.')
        bot.register_next_step_handler(message, get_rewatch)


if __name__ == '__main__':
    bot.enable_save_next_step_handlers(delay=4)
    bot.polling()
