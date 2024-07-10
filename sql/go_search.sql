SELECT DISTINCT p.access
FROM term AS parent
INNER JOIN relation AS r ON r.parent_term_id = parent.id
INNER JOIN term AS child ON child.id = r.child_term_id
INNER JOIN annotation AS a ON a.term_id = child.id
INNER JOIN protein AS p ON p.id = a.protein_id
WHERE parent.goid = %(goid)s
  AND p.taxid = %(taxid)s
