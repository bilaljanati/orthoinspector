SELECT t.goid AS value, t.goid AS desc, t.name AS label
FROM name AS n
INNER JOIN term AS t ON t.id = n.term_id
INNER JOIN occurence AS o ON o.term_id = n.term_id
WHERE t.goid LIKE %(pattern)s
  AND o.taxid = %(taxid)s
LIMIT %(limit)s
