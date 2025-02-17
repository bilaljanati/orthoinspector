from orthodb import OrthoDb
from functools import cache


class Warehouse:
    def __init__(self, config):
        self.dbcatalog = config["databases"]
        self.conninfo = config["hosts"]
        self.data_url = config["data_server_url"]
        self.databases = {}

    def _get_conn_info(self, hostname):
        info = self.conninfo[hostname]
        info["host"] = hostname
        return info

    def get_versions(self):
        return self.dbcatalog.keys()

    def get_dbinfo(self, name):
        return {
            "name": name,
            "description": self.dblist[name].get("description", ""),
            "active": self.dblist[name].get("active", True),
        }

    def get_dblist(self):
        res = {}
        for release, dbs in self.dbcatalog.items():
            res[release] = list(dbs.keys())
        return res

    def get_db(self, name, release):
        import traceback

        try:
            release = int(release)
            dbinfo = self.dbcatalog[release][name]
            dbname = dbinfo["dbname"]
            if dbname not in self.databases:
                hostname = dbinfo["host"]
                desc = dbinfo.get("description", "")
                self.databases[dbname] = OrthoDb(
                    name,
                    release,
                    dbname,
                    conninfo=self._get_conn_info(hostname),
                    description=desc,
                    data_url=self.data_url,
                    has_transverse=self.has_transverse(name, release),
                    clades=dbinfo.get("clades", None),
                )
            db = self.databases[dbname]
        except KeyError:
            traceback.print_exc()
            return False
        return db

    def has_transverse(self, name, release):
        return name == "Transverse" or (
            release in self.dbcatalog and "Transverse" in self.dbcatalog[release]
        )

    @cache
    def gather_stats(self):
        stats = {}
        for release, dbs in self.dbcatalog.items():
            stats[release] = {}
            for name in dbs.keys():
                stats[release][name] = self.get_db(name, release).get_stats()
        return stats

    # Identify domain of protein
    def get_primary_database(self, release, prot):
        avdbs = set(self.get_dblist()[release])
        pdb = []
        for taxon in prot["lineage"]:
            if taxon["name"] in avdbs:
                pdb = taxon["name"]
                break
        return pdb
