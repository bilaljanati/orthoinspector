from orthodb import OrthoDb


class Warehouse():
    def __init__(self, config):
        self.dblist = config['databases']
        self.conninfo = config['hosts']
        self.databases = {}

    def _get_conn_info(self, hostname):
        info = self.conninfo[hostname]
        info['host'] = hostname
        return info

    def get_versions():
        return self.databases.keys()

    def get_dbinfo(self, name):
        return {
            'name': name,
            'description': self.dblist[name]['description']
        }

    def get_dblist(self):
        res = []
        for name in self.dblist.keys():
            res.append(self.get_dbinfo(name))
        return res

    def get_db(self, name):
        dbname = self.dblist[name]['dbname']
        if dbname not in self.databases:
            hostname = self.dblist[name]['host']
            self.databases[dbname] = OrthoDb(dbname, conninfo=self._get_conn_info(hostname))
        return self.databases[dbname]
