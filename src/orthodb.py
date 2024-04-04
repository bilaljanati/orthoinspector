import psycopg2
import psycopg2.extras
import random
from functools import cache


class OrthoDb():
    def __init__(self, dbname, conninfo):
        self.dbname = dbname
        self.conn = self._connect(conninfo)

        self.has_models = False
        self.has_profiles = False
        self.has_distances = False
        self._analyze_db()

    def _connect(self, ci):
        return psycopg2.connect(
            dbname=self.dbname,
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
        with self.conn:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql, parameters)
                res = cursor.fetchall()
        return res

    # Determine what the db can do
    def _analyze_db(self):
        self.has_names = self._check_for_names()
        self.has_models = self._check_for_models()
        self.has_profiles = self._check_for_profiles()
        self.has_distances = self._check_for_distances()
        self.has_fulltextsearch = self._check_for_fulltextsearch()

    def _check_for_names(self):
        sql = """SELECT name
                 FROM protein
                 LIMIT 1"""
        try:
            res = self._query(sql)
            has_names = True
        except Exception:
            has_names = False
        return has_names

    def _check_for_models(self):
        sql = """SELECT model
                 FROM species
                 LIMIT 1"""
        try:
            res = self._query(sql)
            has_models = True
        except Exception:
            has_models = False
        return has_models

    def _check_for_profiles(self):
        sql = """SELECT profile
                 FROM protein
                 LIMIT 1"""
        try:
            res = self._query(sql)
            has_prof = True
        except Exception:
            has_prof = False
        return has_prof

    def _check_for_distances(self):
        sql = """SELECT pk_distance
                 FROM distance"""
        try:
            res = self._query(sql)
            has_dist = True
        except Exception:
            has_dist = False
        return has_dist

    # TODO
    def _check_for_fulltextsearch(self):
        return False

    def get_status(self):
        return {
            'names': self.has_names,
            'fulltext': self.has_fulltextsearch
        }

    @cache
    def get_stats(self):
        nb_species = len(self.get_species_list())
        nb_proteins = self.get_nb_proteins()
        return {
            'species': nb_species,
            'proteins': nb_proteins
        }

    # DB queries

    def get_random_access(self):
        stats = self.get_stats()
        protid = random.randrange(0, stats['species'])
        sql = """SELECT access
                 FROM protein
                 WHERE pk_protein = %(protid)s;"""
        res = self._query(sql, {'protid': protid})
        return res[0]['access']

    def get_species_list(self):
        sql = """SELECT *
                 FROM species
                 ORDER BY name ASC"""
        return self._query(sql)

    def get_nb_proteins(self):
        sql = """SELECT COUNT(pk_protein) AS count
                 FROM protein"""
        res = self._query(sql)
        return res[0]['count']

    def get_protein(self, access):
        sql = self._get_sql("protein")
        sql = '\n'.join(line for line in sql.splitlines() if 'model' not in line)
        res = self._query(sql, {'access': access})
        return res[0] if res else res

    def get_orthologs(self, access):
        sql = self._get_sql("orthologs")
        res = self._query(sql, {'access': access})
        return self._format_orthologs(res)

    def _format_orthologs(self, data):
        return [self._format_ortholog_row(row) for row in data]

    def _format_ortholog_row(self, row):
        res = {}
        res['type'] = row['type']
        res['inparalogs'] = self._format_seq_array(row['inparalogs'])
        res['orthologs'] = self._format_seq_array(row['orthologs'])
        res['species'] = {'taxid': row['taxid'], 'name': row['species']}
        res['size'] = row['length']
        lineage = self._format_lineage(row['lineage'])
        res['fullTaxonomy'] = lineage
        res['reducedTaxonomy'] = self._reduce_lineage(lineage)
        res['taxoDist'] = 1
        return res

    def _format_seq_array(self, group):
        return [{"access": pair.split(',')[0], "name": pair.split(',')[1]} for pair in group.split()]

    def _format_lineage(self, lineage):
        l = lineage.split(';')
        if len(l) > 6:
            l = l[6:]
        names = [l[i] for i in range(len(l)) if i%2]
        return names

    # TODO
    def _reduce_lineage(self, lineage):
        return lineage[-6:]

    def search_protein(self, txt):
        pass

    def get_sequences(self, access_list):
        sql = """SELECT description, sequence
                FROM protein
                WHERE access IN %s
              """
        return self._query(sql, [tuple(access_list)])

    def get_fasta(self, access_list):
        fasta = []
        width = 60
        for row in self.get_sequences(access_list):
            seq = self._format_fasta_seq(row['sequence'])
            fasta.append(f">{row['description']}\n{seq}")
        return '\n'.join(fasta)

    def _format_fasta_seq(self, seq, width=60):
        return '\n'.join([seq[i:i+width] for i in range(0, len(seq), width)])
