from dbservice import DbService


class GeneOntology(DbService):
    aspects = {'C': 'cellular component', 'F': 'molecular function', 'P': 'biological process'}

    def __init__(self, params):
        self.conn = self.connect(params['connection'])

    def get_annotations(self, access):
        sql = self.get_sql("go_annotations")
        return self.query(sql, {'access': access})

    def _format_data(self, rows):
        an = {v:[] for v in GeneOntology.aspects.values()}
        for r in rows:
            namespace, entry = self._format_row(r)
            if namespace not in an:
                an[namespace] = []
            an[namespace].append(entry)
        return {'annotations': an}

    def _format_row(self, row):
        aspects = GeneOntology.aspects
        namespace = aspects[row['aspect']]
        entry = {
            'id': row['id'],
            'term': row['term'],
            'evidence': [{'code': c, 'description': d} for c, d in zip(row['evidence_code'].split(','), row['evidence_description'].split(','))]
        }
        return namespace, entry

