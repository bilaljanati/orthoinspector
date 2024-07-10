SELECT p.access,
	p.name,
	p.description,
	regexp_replace(description, '[^ ]* ([^=]+) [A-Z]{2}=.*', '\1') AS short_desc,
	p.sequence,
	LENGTH(p.sequence) AS length,
	s.taxid,
	s.lineage,
	s.name AS species
    ,profile
FROM protein AS p
INNER JOIN species AS s ON s.pk_species = p.pk_species
WHERE access IN %(access_list)s
