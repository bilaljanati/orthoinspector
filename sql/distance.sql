WITH prots AS (
	SELECT pk_protein, access
	FROM protein
	WHERE access IN %(access_list)s
)
SELECT pa.access AS a, pb.access as b
FROM distance AS d
INNER JOIN prots AS pa ON pa.pk_protein = d.pk_proteina
INNER JOIN prots AS pb ON pb.pk_protein = d.pk_proteinb
