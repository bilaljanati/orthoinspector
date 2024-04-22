SELECT p.access, p.name
FROM protein AS p
INNER JOIN species AS s ON s.pk_species = p.pk_species
WHERE s.taxid = %(taxid)s;
