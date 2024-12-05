from dbservice import DbService
from functools import lru_cache
import re


class GeneOntology(DbService):
    aspects = {
        "C": "cellular component",
        "F": "molecular function",
        "P": "biological process",
    }

    def __init__(self, params):
        conninfo = params["connection"]
        super().__init__("go", conninfo)

    @lru_cache(maxsize=512)
    def get_annotations(self, access):
        data = self._fetch_annotations(access)
        return self._format_data(data)

    def _fetch_annotations(self, access):
        sql = self._get_sql("go_annotations")
        return self._query(sql, {"access": access})

    def _format_data(self, rows):
        an = {v: [] for v in GeneOntology.aspects.values()}
        for r in rows:
            namespace, entry = self._format_row(r)
            if namespace not in an:
                an[namespace] = []
            an[namespace].append(entry)
        return {"annotations": an}

    def _format_row(self, row):
        aspects = GeneOntology.aspects
        namespace = aspects[row["aspect"]]
        entry = {
            "id": row["id"],
            "term": row["term"],
            "evidence": [
                {"code": c, "description": d}
                for c, d in zip(
                    row["evidence_code"].split(","),
                    row["evidence_description"].split(","),
                )
            ],
        }
        return namespace, entry

    @lru_cache(maxsize=128)
    def search_term(self, pattern, taxid, limit=10):
        if re.match(r"GO:[0-9]{2,}", pattern):
            sql = self._get_sql("go_autocomplete_term")
            pattern = f"{pattern}%"
        else:
            sql = self._get_sql("go_autocomplete_fts")
            pattern = f"{pattern}:*".replace(" ", "\ ")
        res = self._query(sql, {"pattern": pattern, "taxid": taxid, "limit": limit})
        return res

    def get_matching_proteins(self, goid, taxid):
        sql = self._get_sql("go_search")
        res = self._query(sql, {"goid": goid, "taxid": taxid})
        return [row["access"] for row in res]
