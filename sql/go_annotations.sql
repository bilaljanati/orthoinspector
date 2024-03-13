SELECT tc.goid AS id,
		tc.name AS term,
		string_agg(DISTINCT e.code, ',') as evidence_code,
		string_agg(DISTINCT e.description, ',') as evidence_description,
		tc.aspect
FROM term tc
INNER JOIN annotation a ON a.term_id = tc.id
INNER JOIN protein p ON p.id = a.protein_id
INNER JOIN evidence e ON e.id = a.evidence_id
WHERE true
  AND p.access = %(access)s
GROUP BY tc.goid, tc.name, tc.aspect
ORDER BY tc.goid ASC
