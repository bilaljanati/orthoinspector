from webservice import WebService
from functools import cache


class Taxonomy(WebService):
    url_lineage = "https://lbgi.fr/api/taxonomy/lineage/%s"

    @cache
    def get_lineage(self, taxid):
        data = self._fetch(__class__.url_lineage % taxid)
        return self._format_lineage(data)

    def _format_lineage(self, d):
        if d["meta"]["status"] != "success":
            return None
        return [{"id": sp["id"], "name": sp["name"]} for sp in d["data"]]
