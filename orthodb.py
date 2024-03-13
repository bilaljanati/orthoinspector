import psycopg2
import psycopg2.extras
from abc import ABCMeta, abstractmethod


class OrthoDb(metaclass=ABCMeta):
    def __init__(self, dbname, conninfo, has_transverse):
        self.dbname = dbname
        self.conn = self.connect(conninfo)

        self.has_transverse = has_transverse
        self.has_models = False
        self.has_profiles = False
        self.has_distances = False
        self.analyze_db()

    def connect(self, ci):
        return psycopg2.connect(
            dbname=self.dbname,
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

    # Determine what the db can do
    def analyze_db(self):
        self.has_models = self.check_for_models()
        self.has_profiles = self.check_for_profiles()
        self.has_distances = self.check_for_distances()
        self.has_fulltextsearch = self.check_for_fulltextsearch()

    @abstractmethod
    def check_for_models(self):
        pass

    @abstractmethod
    def check_for_profiles(self):
        pass

    @abstractmethod
    def check_for_distances(self):
        pass

    @abstractmethod
    def check_for_fulltextsearch(self):
        pass
