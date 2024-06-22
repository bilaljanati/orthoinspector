import psycopg2
import psycopg2.extras
import random
import math
from functools import cache, lru_cache


class OrthoDb():
    def __init__(self, display_name, release, dbname, conninfo, description, data_url, has_transverse):
        self.display_name = display_name
        self.dbname = dbname
        self.release = release
        self.conn = self._connect(conninfo)
        self.conn.autocommit = True
        self.description = description
        self.data_url = data_url

        self.has_models = False
        self.has_profiles = False
        self.has_distances = False
        self.has_data = False
        self.has_transverse = has_transverse
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
        self.has_data = self._check_for_data()

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
                 FROM distance
                 LIMIT 1"""
        try:
            res = self._query(sql)
            has_dist = True
        except Exception:
            has_dist = False
        return has_dist

    def get_info(self):
        return {
            'name': self.display_name,
            'release': self.release,
            'description': self.description,
            'has_models': self.has_models,
            'has_profiles': self.has_profiles,
            'has_distances': self.has_distances,
            'has_data': self.has_data,
            'has_transverse': self.has_transverse
        }

    def get_status(self):
        return {
            'names': self.has_names
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
        protid = random.randrange(0, stats['proteins'])
        sql = """SELECT access
                 FROM protein
                 WHERE pk_protein = %(protid)s;"""
        res = self._query(sql, {'protid': protid})
        return res[0]['access']

    @cache
    def get_species_list(self):
        sql = """SELECT taxid, name, lineage
                 FROM species
                 ORDER BY name ASC"""
        species = []
        for row in self._query(sql):
            species.append({
                'taxid': row['taxid'],
                'name': row['name'],
                'lineage': self._format_lineage(row['lineage'])
            })
        return species

    def get_nb_proteins(self):
        sql = """SELECT COUNT(pk_protein) AS count
                 FROM protein"""
        res = self._query(sql)
        return res[0]['count']

    def get_protein(self, access):
        sql = self._get_sql("protein")
        sql = '\n'.join(line for line in sql.splitlines() if 'model' not in line)
        res = self._query(sql, {'access': access})
        if res:
            res = res[0]
            res['lineage'] = self._format_lineage(res['lineage'])
        return res

    def get_orthologs(self, access, model=False):
        res = self._fetch_orthologs(access, model)
        query = self.get_protein(access)
        return self._format_orthologs(res, query)

    def _fetch_orthologs(self, access, model=False):
        query = "orthologs" + ("_model" if model else "")
        sql = self._get_sql(query)
        return self._query(sql, {'access': access})

    def _format_orthologs(self, data, query):
        return [self._format_ortholog_row(row, query) for row in data]

    def _format_ortholog_row(self, row, query):
        res = {}
        res['type'] = row['type']
        res['inparalogs'] = self._format_seq_array(row['inparalogs'])
        res['orthologs'] = self._format_seq_array(row['orthologs'])
        res['length'] = list(map(int, row['length'].split(' ')))
        res['species'] = {'taxid': row['taxid'], 'name': row['species']}
        lineage = self._format_lineage(row['lineage'])
        res['fullTaxonomy'] = lineage
        res['reducedTaxonomy'] = self._reduce_lineage(lineage)
        res['taxoDist'] = self._compute_taxo_distance(lineage, query['lineage'])
        return res

    def _compute_taxo_distance(self, lineage1, lineage2):
        lca = 0
        while lca < min(len(lineage1), len(lineage2)) and lineage1[lca]['taxid'] == lineage2[lca]['taxid']:
            lca += 1
        return len(lineage1)+len(lineage2)-2*lca

    def _format_seq_array(self, group):
        return [{"access": pair.split(',')[0], "name": pair.split(',')[1]} for pair in group.split()]

    def _format_lineage(self, lineage, ignore_top_taxons=0):
        l = lineage.split(';')
        if ignore_top_taxons > 0 and len(l) > ignore_top_taxons:
            #l = l[ignore_top_taxons:]
            l = l.slice(ignore_top_taxons)
        taxons = [{'taxid': l[i], 'name': l[i+1]} for i in range(0, len(l), 2)]
        return taxons

    # TODO
    def _reduce_lineage(self, lineage):
        return lineage[-6:]

    def _fetch_lineages(self):
        sql = """SELECT lineage
                 FROM species"""
        return self._query(sql)

    def _get_lineages(self):
        exclude = []
        lineages = self._fetch_lineages()
        res = []
        for r in lineages:
            l = r['lineage'].split(';')
            l = [(int(l[i]), l[i+1]) for i in range(0, len(l), 2)]
            res.append(l)
        return res

    def get_proximal_proteins(self, access):
        sql = self._get_sql("proximal")
        return self._query(sql, {'access': access})

    @cache
    def _get_species_tree(self, exclude=[], maxdepth=math.inf):
        taxons = {}
        for l in self._get_lineages():
            parent = ""

            depth = 0
            for sp in l:
                depth += 1
                if depth > maxdepth:
                    break
                taxid, name = sp
                if name in exclude:
                    continue
                if taxid not in taxons:
                    taxons[taxid] = {'name': name, 'parent': parent, 'value': 1}
                else:
                    taxons[taxid]['value'] += 1
                parent = taxid
        return taxons

    def get_sun_tree(self, maxdepth=10):
        taxons = self._get_species_tree(exclude=('root', 'cellular organisms'), maxdepth=maxdepth)
        return [{'id': key, **taxons[key]} for key in taxons]

    def get_profile_tree(self):
        taxons = self._get_species_tree()
        root = {key: value for key, value in taxons.items() if value.get('parent', '') == ''}

        childindex = {}
        for taxid, sp in taxons.items():
            parent = sp['parent']
            if not parent:
                root = taxid
                continue
            if parent not in childindex:
                childindex[parent] = []
            childindex[parent].append(taxid)

        def _get_node_rec(taxid, taxons, index):
            sp = taxons[taxid]
            children = index[taxid] if taxid in index else []

            return {
                'taxid': taxid,
                'title': sp['name'],
                'folder': len(children)>0,
                'children': [_get_node_rec(childid, taxons, index) for childid in children]
            }
        return _get_node_rec(root, taxons, childindex)

    @lru_cache(maxsize=64)
    def search_protein(self, pattern, limit=10):
        sql = self._get_sql("search_protein")
        pattern = pattern.strip().upper()
        return self._query(sql, {'pattern': pattern+'%', 'limit': limit})

    def get_sequences(self, access_list):
        sql = """SELECT description, sequence
                FROM protein
                WHERE access IN %s
              """
        return self._query(sql, [tuple(access_list)])

    def get_fasta(self, access_list):
        fasta = []
        for row in self.get_sequences(access_list):
            seq = self._format_fasta_seq(row['sequence'])
            fasta.append(f">{row['description']}\n{seq}")
        return '\n'.join(fasta)

    def _format_fasta_seq(self, seq, width=60):
        return '\n'.join([seq[i:i+width] for i in range(0, len(seq), width)])

    @cache
    def _fetch_profile_species(self):
        sql = """SELECT taxid
                FROM species
                ORDER BY pk_species ASC"""
        return self._query(sql)

    def _list_to_profile(self, taxid_list, exclude=-1):
        species = [int(r['taxid']) for r in self._fetch_profile_species()]
        taxid_list = set([int(t) for t in taxid_list])
        taxid_list.discard(int(exclude))
        p = []
        for taxid in species:
            p.append('1' if taxid in taxid_list else '0')
        return ''.join(p)

    def search_by_profile(self, taxid, present, absent):
        sql = """SELECT p.access
                ,p.name
                ,LENGTH(p.sequence) AS length
                ,p.profile
                ,regexp_replace(p.description, '[^ ]* ([^=]+) [A-Z]{2}=.*', '\\1') AS short_desc
                FROM protein AS p
                INNER JOIN species AS s ON s.pk_species = p.pk_species
                WHERE s.taxid = %(taxid)s"""
        zeroes = '0' * self.get_stats()['species']
        if len(present) > 0:
            pp = self._list_to_profile(present, taxid)
            sql += f"\nAND p.profile & B'{pp}' = B'{pp}'"
        if len(absent) > 0:
            pa = self._list_to_profile(absent, taxid)
            sql += f"\nAND p.profile & B'{pa}' = B'{'0'*len(pa)}'"
        return self._query(sql, {'taxid': taxid})

    # API

    def get_species_proteins(self, taxid):
        sql = self._get_sql("species_proteins")
        return self._query(sql, {'taxid': taxid})

    def get_protein_api(self, access):
        p = self.get_protein(access)
        if not p:
            return {}
        return {
            'access': p['access'],
            'name': p['name'],
            'description': p['short_desc'],
            'sequence': p['sequence'],
            'species': p['taxid']
        }

    def get_orthologs_api(self, access):
        raw = self._fetch_orthologs(access, model=False)
        res = []
        for r in raw:
            tmp = {
                'type': r['type'],
                'species': r['taxid'],
                'inparalogs': self._format_orthologs_api(r['inparalogs']),
                'orthologs': self._format_orthologs_api(r['orthologs'])
            }
            res.append(tmp)
        return res

    def _format_orthologs_api(self, seqs):
        return [pair.split(',')[0] for pair in seqs.split(' ')]

    # Published data

    def _get_base_data_url(self):
        return f'{self.data_url}/{self.display_name}'

    def _get_proteomes_url(self):
        return f'{self._get_base_data_url()}/proteomes.tar.gz'

    def _get_data_url(self):
        taxid = self.get_species_list()[0]['taxid']
        return f'{self._get_base_data_url()}/data/{taxid}.tsv.gz'

    def _fetch_data(self, url):
        import requests
        try:
            response = requests.head(url)
        except:
            return False
        return response.status_code == 200

    @cache
    def _check_for_data(self):
        return self._fetch_data(self._get_proteomes_url()) and self._fetch_data(self._get_data_url())

    # For background jobs

    def _format_sequence_batch(self, batch):
        prots = []
        for row in batch:
            s = ">" + row['description'] + "\n" + self._format_fasta_seq(row['sequence'])
            prots.append(s)
        return '\n'.join(prots)

    # Generator returning the whole proteome as FASTA
    def get_proteome(self, batch_size=100):
        sql = """SELECT description, sequence
                 FROM protein
                 WHERE pk_protein > %(offset)s
                 ORDER BY pk_protein
                 LIMIT %(batch_size)s"""
        offset = 0
        while True:
            batch = self._query(sql, {'offset': offset, 'batch_size': batch_size})
            if len(batch) == 0:
                break
            offset += batch_size
            yield self._format_sequence_batch(batch)

    def get_distances(self, access_list):
        if len(access_list) == 0:
            return []
        sql = self._get_sql("distance")
        return self._query(sql, {"access_list": tuple(access_list)})
