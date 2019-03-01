# Nautical

Утилита для создания легковесных Telegram-ботов из Python-функций.

## Содержание

* [Установка](#Установка)
* [Руководство](#Руководство)
    * [0. Start, help и другие команды по умолчанию](#Start-help-и-другие-команды-по-умолчанию)
    * [1. Регистрация комманд](#1-Регистрация-комманд)
    * [2. Отправка изображений пользователю](#2-Отправка-изображений-пользователю)
    * [3. Загрузка изображений пользователем](#3-Загрузка-изображений-пользователем)
    * [4. Контроль выполнения функций с помощью параметров](#4-Контроль-выполнения-функций-с-помощью-параметров)
    * [5. Реагирование на нажатия кнопок](#5-Реагирование-на-нажатия-кнопок)
    * [6. Логирование событий в SQLite](#6-Логирование-событий-в-SQLite)
* [Авторы](#Авторы)


## Установка
[К содержанию](#Содержание)

```bash
git clone https://github.com/olferuk/Nautical.git
cd <cloned_repo>
pip install .
```

## Руководство
[К содержанию](#Содержание)

Подготовка:
```python
from nautical.bot import TelegramBot
from nautical.message import Message

bot = TelegramBot(token='<YOUR_TOKEN>', config_path='./config.db')
```

### 0. Start, help и другие команды по умолчанию
[К содержанию](#Содержание)

Создайте бота, как показано в сниппете выше. Ваш токен можно получить, обратившись к боту @bot_father в Телеграме.

Бот уже запущен и готов к работе! Давайте проверим:

```bash
> /start

Hello and welcome! Start using me right away or ask for /help :)

> /help

The available commands are:
→ /start: Shows the starting dialog
→ /help: Shows this message
→ /set <param> <x>: Sets parameter <param> to value <x>. Like `/set a 4`
→ /params: Shows list of all specified parameters
```

Цель команд `/set` и `/params` - дать пользователю бота возможность управлять функциями "под капотом" бота.

Сообщения после команд `/start` и `/help`, конечно, тоже можно менять:

```python
bot.starting_message = 'Другое приветственное сообщение'

bot.help_message = 'Другое сообщение о коммандах'
```

### 1. Регистрация комманд
[К содержанию](#Содержание)

```python
def hello_world():
    return Message(text='Hello world!')

bot.register_command('hello', hello_world)
```

Вы можете сразу проверить работу новой команды:

```bash
> /hello

Hello, world!
```

### 2. Отправка изображений пользователю
[К содержанию](#Содержание)

У класса `Message` есть два поля для поддержки отправки изображений: `image` и `image_url`.
Используйте `image`, чтобы поделиться файлом с устройства (в `image` нужно передать абсолютный путь к картинке),
а для ссылок из Интернета предусмотрено поле `image_url`.

Пример:

```python
def local_funny_meme():
    return Message(image='/Users/yourName/path/to/a/meme')

bot.register_command('local_meme', local_funny_meme)


def funny_online_meme():
    return Message(image_url='https://sun1-16.userapi.com/c849332/v849332281/1207ee/tI9a_zqqY0U.jpg')

bot.register_command('online_meme', funny_online_meme)
```

### 3. Загрузка изображений пользователем
[К содержанию](#Содержание)

Реагировать на загруженные изображения просто:

```python
def process_photo(img):
  print('Получил изображение разрешением {}'.format(img))

bot.register_photo_handler(process_photo)
```

Изображение, которое функция `process_photo` получит на вход, имеет тип `PIL.JpegImagePlugin.JpegImageFile`.

### 4. Контроль выполнения функций с помощью параметров
[К содержанию](#Содержание)

Для того, чтобы пользователи могли контролировать бота, Nautical предоставляет механизм параметров:

```python
def function_to_control(config):
  x = int(config['x'])
  print('Значение x равно {}'.format(x))
  if x > 5:
    return Message(text='x больше 5')
  return Message(text='x меньше или равен 5')

bot.register_command('test', function_to_control)
```

Обратите внимание, что `function_to_control` может и не принимать `config`: тогда настройки пользователя ей
просто не будут переданы. Если же первый параметр в функции задан, туда автоматически настройки будут отправлены,
как первому позиционному аргументу.

В работоспособности можно убедиться следующим образом:

```bash
> /set x 2

Successfully set parameter "x" to "2"

> /test

x меньше или равен 5

> /set x 10

Successfully set parameter "x" to "10"

> /test

x больше 5
```

__NB__: набор параметров у каждого пользователя индивидуальный, и присвоение разными пользователями
одной переменной никак не влияет на работоспособность бота у другого пользователя с его настройками.

Параметры хранятся в SQLite-файле, имя которого вы задаете в конструкторе с помощью параметра `config_path`.

### 5. Реагирование на нажатия кнопок
[К содержанию](#Содержание)

Добавить кнопки к сообщению очень просто:

```python
def joke():
    return Message(message='A bear once met a burning car in the forest. He sat in it and burned alive.',
                   buttons=['😀 Ahahah', '😒 Meh'])

bot.register_command('joke', joke)
```

Они нужны для того, чтобы трекать действия пользователя, как будет описано в следующем разделе.
Полноценно реагировать на нажатия кнопок пока нельзя. Stay tuned!

### 6. Логирование событий в SQLite
[К содержанию](#Содержание)

Чтобы разработчику знать, что делают пользователи бота, можно включить логирование их действий.

#### 6.1. Простое логирование

Рассмотрим подробнее:

```python
bot = TelegramBot(token='<YOUR_TOKEN>', config_path='config.db', db_path='logs.db')

def hello():
  return Message('Hello world!')

def greet(config):
  return Message('Hello, {}!'.format(config['name']))


bot.register_command('hello', hello)
bot.register_command('greet', greet)

# Later in the Telegram:

> /hello

Hello, world!

> /set name Alex

Parameter "name" successfully set to "Alex"

> /greet

Hello, Alex!
```

Открыв файл `logs.db`, можно обнаружить 2 таблицы: `user` и `record`. В `user` будет добавлен каждый пользователь,
который написал боту:

| __user_id__  | __user_name__ | __first_name__ | __last_name__ |
|--------------|---------------|----------------|---------------|
| 81910644     |               | Alexander      | Olferuk       |

А в `record` - вся история:

| __user_id__ | __chat_id__ | __message_id__ | __dt__              | __message__    | __is_image__ | __meta__ | __button__ |
|-------------|-------------|----------------|---------------------|----------------|--------------|----------|------------|
| 81910644    | 81910628    | 598            | 2019-02-06 15:49:06 | /hello         | 0            |          |            |
| 81910644    | 81910628    | 600            | 2019-02-06 15:49:15 | /set name Alex | 0            |          |            |
| 81910644    | 81910628    | 602            | 2019-02-06 15:49:22 | /greet         | 0            |          |            |

#### 6.2. Использование поля meta

Представьте, что бот по команде `/joke` должен выдавать одну из миллиона смешных шуток, а вам интересно,
какие шутки какому пользователю мы уже показали. Саму шутку, конечно, мы запоминать не будем, а, например, её индекс
в коллекции вполне можем. Для этого можно воспользоваться полем `meta`:

```python
JOKES = [...]

def show_random_joke():
  index = np.random.randint(len(JOKES))
  return Message(JOKES[index], meta=index)

bot.register_command('joke', show_random_joke)
```

Смотрим табличку `record`:

| __user_id__ | __chat_id__ | __message_id__ | __dt__              | __message__    | __is_image__ | __meta__ | __button__ |
|-------------|-------------|----------------|---------------------|----------------|--------------|----------|------------|
| 81910644    | 81910628    | 604            | 2019-02-06 16:18:08 | /joke          | 0            | 5        |            |
| 81910644    | 81910628    | 606            | 2019-02-06 16:18:11 | /joke          | 0            | 7        |            |
| 81910644    | 81910628    | 608            | 2019-02-06 16:18:15 | /joke          | 0            | 0        |            |

#### 6.3. Регистрация нажатий на кнопки

Вернемся к примеру с шуткой про медведя:

```python
def joke():
    return Message(message='A bear once met a burning car in the forest. He sat in it and burned alive.',
                   buttons=['😀 Ahahah', '😒 Meh'])

bot.register_command('bear', joke)
```

Кнопки появляются, на них нажать можно, и это будет зарегистрировано:

| __user_id__ | __chat_id__ | __message_id__ | __dt__              | __message__    | __is_image__ | __meta__ | __button__ |
|-------------|-------------|----------------|---------------------|----------------|--------------|----------|------------|
| 81910644    | 81910628    | 610            | 2019-02-06 16:22:10 | /bear          |  0           |          |           |
| 81910644    | 81910628    | 610            | 2019-02-06 16:22:10 |                |  0           |          | 😒 Meh     |
| 81910644    | 81910628    | 613            | 2019-02-06 16:22:16 | /bear          |  0           |          |           |
| 81910644    | 81910628    | 613            | 2019-02-06 16:22:16 |                |  0           |          | 😀 Ahahah  |

А по тому, что у пар "сообщение бота" - "реакция пользователя" одинаковый `message_id`, легко разобраться, какая реакция к какому
сообщению относится.

## Авторы
[К содержанию](#Содержание)

* Ольферук Александр ( [vk](https://vk.com/a_olferuk) | [github](https://github.com/EnlightenedCSF) )
* Палухин Данила ( [vk](https://vk.com/dpaluhin) | [github](https://github.com/Palushok) )
