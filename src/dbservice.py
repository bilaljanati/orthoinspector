from functools import cache
import psycopg2
import psycopg2.extras


class DbService():
    
    def __init__(self, dbname, conninfo):
        conninfo['dbname'] = dbname
        self.conn = self._connect(conninfo)
        self.conn.autocommit = True

    def _connect(self, ci):
        return psycopg2.connect(
            dbname=ci['dbname'],
            host=ci['host'],
            port=ci['port'],
            user=ci['user'],
            password=ci['password']
        )

    @cache
    def _get_sql(self, _query):
        with open(f"sql/{_query}.sql") as f:
            sql = f.read()
        return sql

    def _query(self, sql, parameters=None):
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(sql, parameters)
            res = cursor.fetchall()
        return res

