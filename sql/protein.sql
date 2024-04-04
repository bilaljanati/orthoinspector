SELECT p.access,
	split_part(split_part(identifier, ' ', 1), '|', 3) AS uniprot_id,
	split_part(split_part(identifier, '|', 3), '_', 1) AS gene_name,
	p.description,
	regexp_replace(description, '[^ ]* ([^=]+) [A-Z]{2}=.*', '\1') AS short_desc,
	p.sequence,
	LENGTH(p.sequence) AS length,
	s.taxid,
	s.name AS species
	,s.model
FROM protein AS p
INNER JOIN species AS s ON s.pk_species = p.pk_species
WHERE access = %(access)s
