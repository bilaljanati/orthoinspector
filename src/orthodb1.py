from orthodb import OrthoDb
import psycopg2


class OrthoDb1(OrthoDb):

    def check_for_models(self):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'species' 
                            AND column_name = 'model';""")
        result = cursor.fetchone()
        cursor.close()
        return bool(result)
