from dbservice import DbService
import random
import math
from functools import cache, lru_cache


class OrthoDb(DbService):
    def __init__(self, display_name, release, dbname, conninfo, description, data_url, has_transverse, clades=None, subclades={}):
        super().__init__(dbname, conninfo)

        self.display_name = display_name
        self.dbname = dbname
        self.release = release
        self.description = description
        self.data_url = data_url
        self.clades = clades
        self.subclades = subclades

        self.has_models = False
        self.has_profiles = False
        self.has_distances = False
        self.has_data = False
        self.has_clades = False
        self.has_transverse = has_transverse
        self._analyze_db()
        self._format_clades()

    def _deprecate_connect(self, ci):
        return psycopg2.connect(
            dbname=self.dbname,
            host=ci['host'],
            port=ci['port'],
            user=ci['user'],
            password=ci['password']
        )

    @cache
    def _deprecate_get_sql(self, _query):
        with open(f"sql/{_query}.sql") as f:
            sql = f.read()
        return sql

    def _deprecate_query(self, sql, parameters=None):
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
        self.has_clades = self.clades is not None

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

    def _format_clades(self):
        self.clades = self._generic_format_clades(self.clades)
        if not self.subclades:
            self.subclades = {}
        self.subclades = {k: self._generic_format_clades(v) for k, v in self.subclades.items()}

    def _generic_format_clades(self, clades):
        if not clades:
            return []
        new_clades = {}
        for row in self.get_species_list():
            for sp in row['lineage']:
                if sp['name'] in clades:
                    new_clades[sp['taxid']] = sp['name']
        name_order = {name: index for index, name in enumerate(clades)}
        res = [{'taxid': k, 'name': v} for k, v in new_clades.items()]
        return sorted(res, key=lambda d: name_order.get(d['name'], float('inf')))

    def get_info(self):
        return {
            'name': self.display_name,
            'release': self.release,
            'description': self.description,
            'clades': self.clades,
            'has_models': self.has_models,
            'has_profiles': self.has_profiles,
            'has_distances': self.has_distances,
            'has_data': self.has_data,
            'has_transverse': self.has_transverse,
            'has_clades': self.has_clades
        }

    def get_status(self):
        return {
            'names': self.has_names
        }

    @cache
    def get_stats(self):
        species = self.get_species_list()
        nb_species = len(species)
        nb_proteins = self.get_nb_proteins()
        stats = {
            'species': nb_species,
            'proteins': nb_proteins
        }
        if self.has_models:
            nb_models = len([sp for sp in species if 'model' in sp and sp['model']])
            stats['model_species'] = nb_models
        return stats

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
        if self.has_models:
            sql = "SELECT taxid, name, lineage, model"
        else:
            sql = "SELECT taxid, name, lineage"
        sql += " FROM species ORDER BY name ASC"
        species = []
        for row in self._query(sql):
            sp = {
                'taxid': row['taxid'],
                'name': row['name'],
                'lineage': self._format_lineage(row['lineage'])
            }
            if self.has_models:
                sp['model'] = row['model']
            species.append(sp)
        return species

    # Species list with only taxid and name
    def get_simple_species_list(self):
        species = self.get_species_list()
        return [{'taxid': s['taxid'], 'name': s['name']} for s in species]

    def get_nb_proteins(self):
        sql = """SELECT COUNT(pk_protein) AS count
                 FROM protein"""
        res = self._query(sql)
        return res[0]['count']

    def get_protein(self, access):
        sql = self._get_sql("protein")
        if not self.has_models:
            sql = '\n'.join(line for line in sql.splitlines() if 'model' not in line)
        if not self.has_profiles:
            sql = '\n'.join(line for line in sql.splitlines() if 'profile' not in line)
        res = self._query(sql, {'access': access})
        if res:
            res = res[0]
            res['lineage'] = self._format_lineage(res['lineage'])
        return res

    def get_proteins(self, access_list):
        sql = self._get_sql("protein_list")
        if not self.has_profiles:
            sql = '\n'.join(line for line in sql.splitlines() if 'profile' not in line)
        return self._query(sql, {'access_list': tuple(access_list)})

    # test if species is in a reference clade
    def _species_in_clade(self, species, clades):
        clades_ids = set([c['taxid'] for c in clades])
        ancestors = set([a['taxid'] for a in species['lineage']])
        match = list(clades_ids & ancestors)
        if len(match) == 0:
            return None
        return match[0]

    # make inventory of matches in given clades
    def _count_for_clades(self, profile, species, clades):
        res = {}
        membership = {}
        # determine each species' clade
        for sp in species:
            match = self._species_in_clade(sp, clades)
            match = 0 if not match else int(match)
            membership[sp['taxid']] = match
        # index reference clades by id
        indexed_clades = {int(s['taxid']): s['name'] for s in clades}
        indexed_clades[0] = "Other"
        # enumerate relationships for each ref clade
        for i, taxid in enumerate([s['taxid'] for s in self._fetch_profile_species()]):
            clade = membership[taxid]
            present = int(profile[i])
            if clade not in res:
                res[clade] = {'taxid': clade, 'name': indexed_clades[clade], 'total': 0, 'present': 0}
            res[clade]['total'] += 1
            res[clade]['present'] += present
        res = list(res.values())
        # sort to conserve order of 'clades' list
        order = {name: index for index, name in enumerate([c['name'] for c in clades])}
        return sorted(res, key=lambda d: order.get(d['name'], float('inf')))

    # distribution for display
    def build_distribution(self, prot):
        if not self.has_clades or not 'profile' in prot:
            return None
        profile = prot['profile']
        species = self.get_species_list()
        res = self._count_for_clades(profile, species, self.clades)
        if not self.subclades:
            return res

        parent_clades_names = set(self.subclades.keys())
        for clade in res:
            clade_name = clade['name']
            if clade_name not in parent_clades_names:
                continue
            subclade = self.subclades[clade_name]
            clade['children'] = self._count_for_clades(profile, species, subclade)
        return res

        res = {}
        membership = {}
        # determine each species' clade
        for sp in self.get_species_list():
            match = self._species_clade(sp)
            match = 0 if not match else int(match)
            membership[sp['taxid']] = match
        # index reference clades by id
        indexed_clades = {int(s['taxid']): s['name'] for s in self.clades}
        indexed_clades[0] = "Other"
        # enumerate relationships for each ref clade
        for i, taxid in enumerate([s['taxid'] for s in self._fetch_profile_species()]):
            clade = membership[taxid]
            present = int(prot['profile'][i])
            if clade not in res:
                res[clade] = {'taxid': clade, 'name': indexed_clades[clade], 'total': 0, 'present': 0}
            res[clade]['total'] += 1
            res[clade]['present'] += present
        return list(res.values())

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
    
    def search_by_go(self, taxid, goterm, goservice):
        matches = goservice.get_matching_proteins(goterm, taxid)
        return self.get_proteins(access_list=matches)

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
        return f'{self.data_url}/{self.display_name}{self.release}'

    def _get_proteomes_url(self):
        taxid = self.get_species_list()[0]['taxid']
        return f'{self._get_base_data_url()}/proteomes/{taxid}.fasta.gz'

    def _get_data_url(self):
        taxid = self.get_species_list()[0]['taxid']
        return f'{self._get_base_data_url()}/orthologs/{taxid}.tsv.gz'

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
