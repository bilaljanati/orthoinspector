from functools import cache
import psycopg2


class DbService():
    def connect(self, ci):
        return psycopg2.connect(
            dbname=ci['dbname'],
            host=ci['host'],
            port=ci['port'],
            user=ci['user'],
            password=ci['password']
        )

    def query(self, sql, parameters=None):
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(sql, parameters)
        res = cursor.fetchall()
        cursor.close()
        return res

    @cache
    def get_sql(self, query):
        with open(f"sql/{query}.sql") as f:
            sql = f.read()
        return sql
