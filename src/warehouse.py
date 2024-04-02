from orthodb import OrthoDb


class Warehouse():
    def __init__(self, config):
        self.dblist = config['databases']
        self.conninfo = config['connection']
        self.databases = {}

    def format_name(self, name, version):
        pat = self.conninfo['pattern']
        return pat.replace(':name:', name).replace(':version:', version)

    def get_versions():
        return self.databases.keys()

    def get_dblist(self, version=None):
        res = {version:d['list'] for version, d in self.dblist.items()}
        if version:
            res = res[version]
        return res

    def get_db(self, name, version):
        n = self.format_name(name, version)
        if n not in self.databases:
            has_t = 'Transverse' in self.dblist[version]['list']
            self.databases[n] = OrthoDb(n, conninfo=self.conninfo, has_transverse=has_t)
        return self.databases[n]

    def get_stats(self):
        stats = {}
        for version, e in self.dblist.items():
            tmp = {}
            if version != '2023':
                continue
            for name in e['list']:
                s = self.get_db(name, version).get_stats()
                tmp[name] = s
            stats[version] = tmp
        return stats
