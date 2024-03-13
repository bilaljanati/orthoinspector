from webservice import WebService
from functools import lru_cache


class Interpro(WebService):
    url = 'https://www.ebi.ac.uk/interpro/api/entry/InterPro/protein/reviewed/%s'

    @lru_cache(maxsize=512)
    def get_domains(self, access):
        data = self._fetch(Interpro.url % access)
        return self._format(data)

    def _format(self, data, filter=['domain']):
        domains = []
        for r in data['results']:
            m = r['metadata']
            if m['type'] not in filter:
                continue
            fragments = []
            for prot in r['proteins']:
                for e in prot['entry_protein_locations']:
                    fragments += [{'start': f['start'], 'end': f['end']} for f in e['fragments']]
            d = {
                'id': m['accession'],
                'name': m['name'],
                'source': list(m['member_databases'].keys()),
                'fragments': fragments
            }
            domains.append(d)
        return {'domains': domains}
