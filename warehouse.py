from orthodb import OrthoDb
from orthodb1 import OrthoDb1
from orthodb2 import OrthoDb2


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
            dbtype = self.dblist[version]['type']
            if dbtype == 1:
                self.databases[n] = OrthoDb1(n, conninfo=self.conninfo, has_transverse=has_t)
            elif dbtype == 2:
                self.databases[n] = OrthoDb2(n, conninfo=self.conninfo, has_transverse=has_t)
        return self.databases[n]
