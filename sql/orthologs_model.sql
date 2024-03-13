WITH mtmlist1 AS (
	SELECT mtm.pk_mtm, mtm.pk_inparaloga, mtm.pk_inparalogb
	FROM mtm
	INNER JOIN ln_inparalog_protein AS l ON l.pk_inparalog = mtm.pk_inparaloga
	INNER JOIN protein AS s ON s.pk_protein = l.pk_protein
	WHERE s.access = %(access)s
), mtmlist2 AS (
	SELECT mtm.pk_mtm, mtm.pk_inparaloga, mtm.pk_inparalogb
	FROM mtm
	INNER JOIN ln_inparalog_protein AS l ON l.pk_inparalog = mtm.pk_inparalogb
	INNER JOIN protein AS s ON s.pk_protein = l.pk_protein
	WHERE s.access = %(access)s
)
SELECT type, inparalogs, orthologs, species FROM
(
	SELECT 'One-to-One' AS type, %(access)s AS inparalogs, sr.access AS orthologs, o.taxid AS species, 0, 0
	FROM oto
	INNER JOIN protein AS sq ON oto.pk_proteina = sq.pk_protein
	INNER JOIN protein AS sr ON sr.pk_protein = oto.pk_proteinb
	INNER JOIN species AS o ON o.pk_species = sr.pk_species
	WHERE sq.access = %(access)s
	  AND o.model

	UNION

	SELECT 'One-to-one' AS type, %(access)s AS inparalogs, sr.access AS orthologs, o.taxid AS species, 0, 0
	FROM oto
	INNER JOIN protein AS sq ON oto.pk_proteinb = sq.pk_protein
	INNER JOIN protein AS sr ON sr.pk_protein = oto.pk_proteina
	INNER JOIN species AS o ON o.pk_species = sr.pk_species
	WHERE sq.access = %(access)s
	  AND o.model

	UNION

	SELECT 'One-to-many' AS type, %(access)s AS inparalogs, string_agg(DISTINCT sr.access, ' ') AS orthologs, o.taxid AS species, 0, 0
	FROM otm
	INNER JOIN protein AS sq ON otm.pk_proteina = sq.pk_protein
	INNER JOIN ln_inparalog_protein AS ln ON ln.pk_inparalog = otm.pk_inparalogb
	INNER JOIN protein AS sr ON sr.pk_protein = ln.pk_protein
	INNER JOIN species AS o ON o.pk_species = sr.pk_species
	WHERE sq.access = %(access)s
	  AND o.model
	GROUP BY otm.pk_otm, o.taxid

	UNION

	SELECT 'Many-to-one' AS type, string_agg(DISTINCT sq.access, ' ') AS inparalogs, sr.access AS orthologs, o.taxid AS species, 0, 0
	FROM otm
	INNER JOIN ln_inparalog_protein AS ln ON otm.pk_inparalogb = ln.pk_inparalog
	INNER JOIN protein AS sq ON ln.pk_protein = sq.pk_protein
	INNER JOIN protein AS sr ON sr.pk_protein = otm.pk_proteina
	INNER JOIN species AS o ON o.pk_species = sr.pk_species
	WHERE otm.pk_inparalogb IN (
		SELECT l.pk_inparalog
		FROM ln_inparalog_protein AS l
		INNER JOIN protein AS s ON s.pk_protein = l.pk_protein
		WHERE s.access = %(access)s
	)
	  AND o.model
	GROUP BY sr.access, o.taxid

	UNION

	SELECT 'Many-to-many' AS type, subb.seqs AS inparalogs, suba.seqs AS orthologs, suba.taxid AS species, 0, 0
	FROM
	(
		SELECT mtm.pk_mtm, STRING_AGG(pa.access, ' ') AS seqs
		FROM mtmlist1 AS mtm
		INNER JOIN ln_inparalog_protein AS la ON la.pk_inparalog = mtm.pk_inparaloga
		INNER JOIN protein AS pa ON pa.pk_protein = la.pk_protein
		GROUP BY mtm.pk_mtm, mtm.pk_inparalogb
	) AS subb
	INNER JOIN (
		SELECT mtm.pk_mtm, STRING_AGG(pb.access, ' ') AS seqs, sp.taxid
		FROM mtmlist1 AS mtm
		INNER JOIN ln_inparalog_protein AS lb ON lb.pk_inparalog = mtm.pk_inparalogb
		INNER JOIN protein AS pb ON pb.pk_protein = lb.pk_protein
		INNER JOIN species AS sp ON sp.pk_species = pb.pk_species
		GROUP BY mtm.pk_mtm, mtm.pk_inparaloga, sp.taxid
	) AS suba ON subb.pk_mtm = suba.pk_mtm
	WHERE suba

	UNION

	SELECT 'Many-to-many' AS type, suba.seqs AS inparalogs, subb.seqs AS orthologs, subb.taxid AS species, 0, 0
	FROM
	(
		SELECT mtm.pk_mtm, STRING_AGG(pa.access, ' ') AS seqs, sp.taxid
		FROM mtmlist2 AS mtm
		INNER JOIN ln_inparalog_protein AS la ON la.pk_inparalog = mtm.pk_inparaloga
		INNER JOIN protein AS pa ON pa.pk_protein = la.pk_protein
		INNER JOIN species AS sp ON sp.pk_species = pa.pk_species
		GROUP BY mtm.pk_mtm, mtm.pk_inparalogb, sp.taxid
	) AS subb
	INNER JOIN (
		SELECT mtm.pk_mtm, STRING_AGG(pb.access, ' ') AS seqs
		FROM mtmlist2 AS mtm
		INNER JOIN ln_inparalog_protein AS lb ON lb.pk_inparalog = mtm.pk_inparalogb
		INNER JOIN protein AS pb ON pb.pk_protein = lb.pk_protein
		GROUP BY mtm.pk_mtm, mtm.pk_inparaloga
	)
	AS suba ON subb.pk_mtm = suba.pk_mtm
) AS o
ORDER BY type DESC
