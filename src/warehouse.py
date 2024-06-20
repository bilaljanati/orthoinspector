from orthodb import OrthoDb


class Warehouse():
    def __init__(self, config):
        self.dbcatalog = config['databases']
        self.conninfo = config['hosts']
        self.data_url = config['data_server_url']
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
             'description': self.dblist[name].get('description', ""),
             'active': self.dblist[name].get('active', True)
         }

    def get_dblist(self):
        res = {}
        for release, dbs in self.dbcatalog.items():
            res[release] = list(dbs.keys())
        return res

    def get_db(self, name, release):
        try:
            dbinfo = self.dbcatalog[release][name]
            dbname = dbinfo['dbname']
            if dbname not in self.databases:
                hostname = dbinfo['host']
                desc = dbinfo['description']
                self.databases[dbname] = OrthoDb(name, release, dbname, conninfo=self._get_conn_info(hostname), description=desc, data_url=self.data_url)
            db = self.databases[dbname]
        except KeyError:
            return False
        return db
