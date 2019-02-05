from sqlite3 import Error

import pandas as pd
import sqlite3
import sys


class ConfigLogger:

    def __init__(self):
        self.initialized = False
        self.create_table = '''CREATE TABLE IF NOT EXISTS config (
            user_id integer,
            parameter text,
            value text,
            CONSTRAINT user_param PRIMARY KEY (user_id, parameter)
        )'''
        self.create_index = '''CREATE UNIQUE INDEX IF NOT EXISTS params
            ON config(user_id,parameter)
        '''

    def init(self, config_filename):
        self.config_filename = config_filename
        try:
            self.conn = sqlite3.connect(self.config_filename,
                                        check_same_thread=False)
            c = self.conn.cursor()
            c.execute(self.create_table)
            c.execute(self.create_index)
        except Error as e:
            print(e, file=sys.stderr)

    def record(self, user_id, parameter, value):
        sql = '''REPLACE INTO config(user_id, parameter, value)
                 VALUES (?,?,?)'''
        cur = self.conn.cursor()
        batch = (user_id, parameter, value)
        cur.execute(sql, batch)

    def get_config(self, user_id):
        sql = '''SELECT * FROM config WHERE user_id = {}'''.format(user_id)
        df = pd.read_sql_query(sql, self.conn)
        return dict(zip(df.parameter, df.value))

    def to_pandas(self):
        return pd.read_sql_query("SELECT * FROM config", self.conn)
