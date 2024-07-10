SELECT t.goid AS value, t.goid AS desc, t.name AS label
FROM to_tsquery('english', %(pattern)s) query, name AS n
INNER JOIN occurence AS o ON o.term_id = n.term_id
INNER JOIN term AS t ON t.id = o.term_id
WHERE to_tsvector('english', n.name) @@ query
    AND o.taxid = %(taxid)s
GROUP BY t.goid, t.name, t.aspect
ORDER BY AVG(ts_rank_cd(to_tsvector('english', n.name), query, 2)) DESC
LIMIT %(limit)s
