class CladeHandler:
    def __init__(self, species, ref_clades, model_species=None):
        self.species = species
        self.clades = ref_clades
        self.model_mask = self._create_model_mask(model_species)
        self._pre_compute(species, ref_clades)

    def _init_membership(self, species):
        m = {}
        for sp in species:
            m[sp['taxid']] = set()
        return m

    def _pre_compute(self, species, ref_clades):
        if ref_clades is None:
            return
        self.membership = self._init_membership(species)
        base_clades = []
        subclades = []
        for c in ref_clades:
            if isinstance(c, dict):
                base_clades.append(c['name'])
                subclades.append(c['clades'])
            else:
                base_clades.append(c)
        self._map_species_to_clade(species, base_clades)
        for sub in subclades:
            self._map_species_to_clade(species, sub)

    def _search_ancestor(self, species, ancestors):
        res = False
        for s in species['lineage']:
            if s['name'] in ancestors:
                res = s['name']
        return res

    def _map_species_to_clade(self, species, ref_clades):
        if len(ref_clades) == 0:
            return
        clades = set([c for c in ref_clades if isinstance(c, str)])
        clades |= set([c['name'] for c in ref_clades if isinstance(c, dict)])
        other_clades = set([c[6:] for c in clades if c.startswith("Other ")])
        clades -= other_clades
        unclassified = []
        for sp in species:
            found = self._search_ancestor(sp, clades)
            if found:
                self.membership[sp['taxid']].add(found)
            else:
                unclassified.append(sp)
        for sp in unclassified:
            found = self._search_ancestor(sp, other_clades)
            if found:
                self.membership[sp['taxid']].add("Other " + found)

    def _create_model_mask(self, model_species):
        if not model_species:
            return None
        mask = []
        models = set([s['taxid'] for s in model_species])
        for s in self.species:
            is_model = '1' if s['taxid'] in models else '0'
            mask.append(is_model)
        return ''.join(mask)

    def get_clade(self, taxid, clades):
        parent_clades = self.membership[int(taxid)]
        inter = parent_clades & set(clades)
        if len(inter) == 0:
            return None
        return inter.pop()

    def build_distribution(self, profile, clades=None, model_only=False):
        if model_only and not self.model_mask:
            return None
        if self.clades is None:
            return None
        if clades is None:
            clades = self.clades
        # flatten clade list
        parent_clades = []
        for c in clades:
            if isinstance(c, dict):
                c = c['name']
            parent_clades.append(c)
        # init dist
        dist = {}
        for c in parent_clades:
            dist[c] = {'name': c, 'total': 0, 'present': 0}
        # walk through profile
        for i, species in enumerate(self.species):
            if model_only and self.model_mask[i] == '0':
                continue
            taxid = species['taxid']
            clade = self.get_clade(taxid, parent_clades)
            if clade is None:
                continue
            present = profile[i] == "1"
            dist[clade]['total'] += 1
            dist[clade]['present'] += present
        # format ordered result
        res = []
        for c in clades:
            if isinstance(c, dict):
                tmp = dist[c['name']]
                tmp['children'] = self.build_distribution(profile, c['clades'])
            else:
                tmp = dist[c]
            res.append(tmp)
        return res
