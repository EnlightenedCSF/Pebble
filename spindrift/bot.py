from .logger import SQLiteLogger
from .settings import ConfigLogger

from PIL import Image
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          CallbackQueryHandler, Filters)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from functools import partial
from urllib.request import urlopen

import io
import sys
import traceback


CONFIG = ConfigLogger()


def make_text_handler(s):
    def f(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text=s)
    return f

def make_photo_handler(func):
    def f(bot, update):
        user_id = update.effective_message['from_user']['id']
        config = CONFIG.get_config(user_id)

        url = bot.getFile(update.message.photo[-1].file_id).file_path
        image_file = io.BytesIO(urlopen(url).read())
        im = Image.open(image_file)
        func(im, config)
    return f

def make_handler(func, buttons_intro):
    def f(bot, update):
        user_id = update.effective_message['from_user']['id']
        config = CONFIG.get_config(user_id)

        msg = func(config)

        has_buttons = (msg.buttons is not None) and len(msg.buttons) > 0
        has_media = (msg.image is not None) or (msg.image_url is not None)
        has_text = msg.message is not None

        if has_media:
            photo = msg.image_url \
                    if msg.image_url is not None \
                    else open(msg.image, 'rb')
            if has_text:
                if msg.message_media_relation == 0:   #  CAPTION_ABOVE
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=msg.message)
                    bot.send_photo(chat_id=update.message.chat_id,
                                   photo=photo)
                else:                                 #  CAPTION_BELOW
                    bot.send_photo(chat_id=update.message.chat_id,
                                   photo=photo)
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=msg.message)
            else:
                bot.send_photo(chat_id=update.message.chat_id, photo=photo)
        else:
            bot.send_message(chat_id=update.message.chat_id, text=msg.message)

        if has_buttons:
            msg_id = str(update.message.message_id)
            keyboard = [[InlineKeyboardButton(x, callback_data='{0}_{1}'\
                                             .format(x, msg_id))
                        for x in msg.buttons]]
            keyboard = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(buttons_intro,
                                      reply_markup=keyboard)
    return f

def make_buttons_processor(choice_confirmation_label):
    def f(bot, update):
        query = update.callback_query
        text = choice_confirmation_label.format(query.data.split('_')[0])
        bot.edit_message_text(text=text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
    return f

def make_set_command(confirmation_label):
    def f(bot, update):
        user_id = update.effective_message['from_user']['id']
        key, value = update.message.text.split(' ')[1:]
        CONFIG.record(user_id, key, value)
        bot.send_message(chat_id=update.message.chat_id,
                         text=confirmation_label.format(key, value))
    return f

def make_params_command(no_params_label, params_title):
    def f(bot, update):
        user_id = update.effective_message['from_user']['id']
        vocab = CONFIG.get_config(user_id=user_id)
        if len(vocab) == 0:
            total = no_params_label
        else:
            title = params_title
            underscore = '========'
            s = '\n'.join(['{0} = {1}'.format(k,v) for k, v in vocab.items()])
            total = '\n'.join([title, underscore, s])
        bot.send_message(chat_id=update.message.chat_id, text=total)
    return f


class TelegramBot():

    def __init__(self, token, config_path, db_path=None):
        global CONFIG
        CONFIG.init(config_path)

        self.token = token

        self.logging = False
        if not (db_path is None):
            self.logger = TelegramLogger(db_path)
            self.logging = True

        self.updater = Updater(token=self.token)
        self.dispatcher = self.updater.dispatcher

        self._start_text = ('Hello and welcome! Start using me right away or '
                            'ask for /help :)')
        self._help_text = ('The available commands are:\n'
                           '→ /start: Shows the starting dialog\n'
                           '→ /help: Shows this message\n'
                           '→ /set <param> <x>: Sets parameter <param> to '
                                                'value <x>. Like `/set a 4`\n'
                           '→ /params: Shows list of all specified parameters')

        # todo: rebuild callback when strings change
        self._parameters_title = 'Parameters are:'
        self._no_parameters_label = 'No parameters specified'
        self._param_changed_confirmation_label = ('The parameter "{0}" '
                                                  'successfully set to "{1}"')
        self._button_press_invitation_label = 'Rate:'
        self._button_press_confirmation_label = 'You chose "{0}"'

        self._set_text_command('start', self._start_text)
        self._set_text_command('help', self._help_text)

        # /set
        confirm_label = self._param_changed_confirmation_label
        self.dispatcher.add_handler(
            CommandHandler('set', make_set_command(confirm_label)))

        # /params
        self.dispatcher.add_handler(
            CommandHandler('params',
                           make_params_command(self._no_parameters_label,
                                               self._parameters_title)
                          ))
        # Buttons
        conf = self._button_press_confirmation_label
        self.dispatcher.add_handler(
            CallbackQueryHandler(make_buttons_processor(conf)
                                ))
        self.resume()

    #  =-=-=-=-=-  COMMAND HANDLING  -=-=-=-=-=

    def register_command(self, name, f):
        label = self._button_press_invitation_label
        if self.command_with_name(name) is None:
            self.dispatcher.add_handler(
                CommandHandler(name,
                               make_handler(f, buttons_intro=label)))
        else:
            command = self.command_with_name(name)
            command.callback = make_handler(f, buttons_intro=label)

    def register_photo_handler(self, f):
        self.dispatcher.add_handler(MessageHandler(Filters.photo,
                                                   make_photo_handler(f)))

    def command_with_name(self, name):
        for command in self.dispatcher.handlers[0]:
            if type(command) == CommandHandler and command.command[0] == name:
                return command
        return None

    def has_command_with_name(self, name):
        return self.command_with_name(name) is None

    def commands(self):
        return [x.command[0] for x in self.dispatcher.handlers[0]]

    #  =-=-=-=-=-  PAUSING  -=-=-=-=-=

    def stop(self):
        self.updater.stop_polling()
        self.started = False

    def resume(self):
        self.updater.start_polling()
        self.started = True

    #  =-=-=-=-=-  START AND HELP TEXTS  -=-=-=-=-=

    @property
    def starting_message():
        return self._help_text

    @starting_message.setter
    def starting_message(self, value):
        self._start_text = value
        self._set_text_command('start', self._start_text)

    @property
    def help_message(self):
        return self._start_text

    @help_message.setter
    def help_message(self, value):
        self._help_text = value
        self._set_text_command('help', self._help_text)

    #  =-=-=-=-=-  UTILITIES  -=-=-=-=-=

    def _set_text_command(self, name, return_text):
        if len(self.dispatcher.handlers) == 0:
            self.dispatcher.add_handler(
                CommandHandler(name, make_text_handler(return_text))
            )
            return
        was_found = False
        for command in self.dispatcher.handlers[0]:
            if type(command) == CommandHandler and command.command[0] == name:
                was_found = True
                command.callback = make_text_handler(return_text)
        if not was_found:
            self.dispatcher.add_handler(
                CommandHandler(name, make_text_handler(return_text))
            )