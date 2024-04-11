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
             'description': self.dblist[name].get('description', ""),
             'active': self.dblist[name].get('active', True)
         }

    def get_dblist(self):
        res = []
        for name in self.dblist.keys():
            res.append(self.get_dbinfo(name))
        return res

    def get_db(self, name):
        try:
            dbname = self.dblist[name]['dbname']
            if dbname not in self.databases:
                hostname = self.dblist[name]['host']
                desc = self.dblist[name]['description']
                self.databases[dbname] = OrthoDb(name, dbname, conninfo=self._get_conn_info(hostname), description=desc)
            db = self.databases[dbname]
        except KeyError:
            return False
        return db
