SELECT access, name, regexp_replace(description, '[^ ]* ([^=]+) [A-Z]{2}=.*', '\1') AS description, distance FROM
(
	SELECT pr.access, pr.name, pr.description, d.distance
	FROM protein AS pq
	INNER JOIN distance AS d ON d.pk_proteina = pq.pk_protein
	INNER JOIN protein AS pr ON pr.pk_protein = d.pk_proteinb
	WHERE pq.access = %(access)s

	UNION

	SELECT pr.access, pr.name, pr.description, d.distance
	FROM protein AS pq
	INNER JOIN distance AS d ON d.pk_proteinb = pq.pk_protein
	INNER JOIN protein AS pr ON pr.pk_protein = d.pk_proteina
	WHERE pq.access = %(access)s
) AS dist
ORDER BY distance ASC
