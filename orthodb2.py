from orthodb import OrthoDb
import psycopg2
from functools import cache


class OrthoDb2(OrthoDb):

    @cache
    def get_sql(self, query):
        with open(f"sql/{query}.sql") as f:
            sql = f.read()
        return sql

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

    def check_for_fulltextsearch(self):
        return False
    
    def get_species_list(self):
        sql = """SELECT *
                 FROM species"""
        return self.query(sql)

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
        access_list = access_list.split(',')
        fasta = []
        width = 60
        for row in self.get_sequences(access_list):
            #seq = '\n'.join([row['sequence'][i:i+width] for i in range(0, len(row['sequence']), width)])
            seq = self._format_fasta_seq(row['sequence'])
            fasta.append(f">{row['description']}\n{seq}")
        return '\n'.join(fasta)

    def _format_fasta_seq(self, seq, width=60):
        return '\n'.join([seq[i:i+width] for i in range(0, len(seq), width)])
