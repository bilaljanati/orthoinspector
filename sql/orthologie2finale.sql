SELECT pr.access AS access1, ps.access AS access2
FROM oto
INNER JOIN protein AS pr ON oto.pk_proteina = pr.pk_protein
INNER JOIN protein AS ps ON ps.pk_protein = oto.pk_proteinb
INNER JOIN species AS ss ON ss.pk_species = ps.pk_species
INNER JOIN species AS sr ON sr.pk_species = pr.pk_species
WHERE ss.taxid IN (%(species1)s, %(species2)s)
AND sr.taxid IN (%(species1)s, %(species2)s)

UNION ALL

SELECT pr.access AS one, pn.access AS many
FROM otm
INNER JOIN protein AS pr ON pr.pk_protein = otm.pk_proteina -- links prota to pk of protein db (to get access)
INNER JOIN ln_inparalog_protein AS ln ON ln.pk_inparalog = otm.pk_inparalogb -- links paralog to the paralog key
INNER JOIN protein AS pn ON pn.pk_protein = ln.pk_protein -- links paralog to the protein db (get access)
INNER JOIN species AS sr ON sr.pk_species = pr.pk_species
INNER JOIN species AS sn ON sn.pk_species = pn.pk_species
WHERE sr.taxid IN (%(species1)s, %(species2)s)
AND sn.taxid IN (%(species1)s, %(species2)s)

UNION ALL 

SELECT pr.access AS one, pn.access AS many
FROM mtm
INNER JOIN ln_inparalog_protein AS lr ON lr.pk_inparalog = mtm.pk_inparaloga
INNER JOIN protein AS pr ON pr.pk_protein = lr.pk_protein -- links prota to pk of protein db (to get access)
INNER JOIN ln_inparalog_protein AS ln ON ln.pk_inparalog = mtm.pk_inparalogb -- links paralog to the paralog key
INNER JOIN protein AS pn ON pn.pk_protein = ln.pk_protein -- links paralog to the protein db (get access)
INNER JOIN species AS sr ON sr.pk_species = pr.pk_species
INNER JOIN species AS sn ON sn.pk_species = pn.pk_species
WHERE sr.taxid IN (%(species1)s, %(species2)s)
AND sn.taxid IN (%(species1)s, %(species2)s)

