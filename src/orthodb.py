import psycopg2
import psycopg2.extras
from functools import cache


class OrthoDb():
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

    @cache
    def get_sql(self, query):
        with open(f"sql/{query}.sql") as f:
            sql = f.read()
        return sql

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

    def check_for_models(self):
        sql = """SELECT COUNT(pk_species) AS count
                 FROM species
                 WHERE model IS NULL"""
        res = self.query(sql)
        return res[0]['count'] == 0

    def check_for_profiles(self):
        sql = """SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'protein' 
                    AND column_name = 'profile'"""
        res = self.query(sql)
        return len(res) > 0

    def check_for_distances(self):
        sql = """SELECT 1
                 FROM information_schema.tables
                 WHERE table_name = 'distance'"""
        res = self.query(sql)
        return len(res) > 0

    # TODO
    def check_for_fulltextsearch(self):
        pass

    @cache
    def get_stats():
        nb_species = len(self.get_species_list())
        nb_sequences = self.get_nb_proteins()
        return {
            'species': nb_species,
            'sequences': nb_sequences,
        }

    # DB queries

    def get_species_list(self):
        sql = """SELECT *
                 FROM species"""
        return self.query(sql)

    def get_nb_proteins(self):
        sql = """SELECT COUNT(pk_protein) AS count
                 FROM protein"""
        res = self.query(sql)
        return res[0]['count']

    def get_protein(self, access):
        sql = self.get_sql("protein")
        res = self.query(sql, {'access': access})
        return res[0] if res else res

    def get_orthologs(self, access):
        sql = self.get_sql("orthologs")
        res = self.query(sql, {'access': access})
        return self.__format_orthologs(res)

    def __format_orthologs(self, data):
        return [self.__format_ortholog_row(row) for row in data]

    def __format_ortholog_row(self, row):
        res = {}
        res['type'] = row['type']
        res['inparalogs'] = self.__format_seq_array(row['inparalogs'])
        res['orthologs'] = self.__format_seq_array(row['orthologs'])
        res['species'] = {'taxid': row['taxid'], 'name': row['species']}
        res['size'] = row['length']
        res['fullTaxonomy'] = []
        res['reducedTaxonomy'] = []
        res['taxoDist'] = 1
        return res

    def __format_seq_array(self, group):
        return [{"access": pair.split(',')[0], "name": pair.split(',')[1]} for pair in group.split()]

    def search_protein(self, txt):
        pass

    def get_sequences(self, access_list):
        sql = """SELECT description, sequence
                FROM protein
                WHERE access IN %s
              """
        return self.query(sql, [tuple(access_list)])

    def get_fasta(self, access_list):
        fasta = []
        width = 60
        for row in self.get_sequences(access_list):
            seq = self._format_fasta_seq(row['sequence'])
            fasta.append(f">{row['description']}\n{seq}")
        return '\n'.join(fasta)

    def _format_fasta_seq(self, seq, width=60):
        return '\n'.join([seq[i:i+width] for i in range(0, len(seq), width)])
