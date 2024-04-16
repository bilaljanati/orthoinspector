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
SELECT type, inparalogs, orthologs, length, taxid, species, lineage FROM
(
    SELECT 'One-to-One' AS type,
			sq.access || ',' || sq.name AS inparalogs,
			sr.access || ',' || sr.name AS orthologs,
			LENGTH(sr.sequence)::text AS length,
			o.taxid,
			o.name AS species,
			o.lineage
    FROM oto
    INNER JOIN protein AS sq ON oto.pk_proteina = sq.pk_protein
    INNER JOIN protein AS sr ON sr.pk_protein = oto.pk_proteinb
    INNER JOIN species AS o ON o.pk_species = sr.pk_species
    WHERE sq.access = %(access)s
	  AND o.model

    UNION

    SELECT 'One-to-one' AS type,
			sq.access || ',' || sq.name AS inparalogs,
			sr.access || ',' || sr.name AS orthologs,
			LENGTH(sr.sequence)::text AS length,
			o.taxid,
			o.name AS species,
			o.lineage
    FROM oto
    INNER JOIN protein AS sq ON oto.pk_proteinb = sq.pk_protein
    INNER JOIN protein AS sr ON sr.pk_protein = oto.pk_proteina
    INNER JOIN species AS o ON o.pk_species = sr.pk_species
    WHERE sq.access = %(access)s
	  AND o.model

    UNION

    SELECT 'One-to-many' AS type,
			sq.access || ',' || sq.name AS inparalogs,
			string_agg(DISTINCT sr.access || ',' || sr.name, ' ') AS orthologs,
			string_agg(LENGTH(sr.sequence)::text, ' ') AS length,
			o.taxid,
			o.name AS species,
			o.lineage
    FROM otm
    INNER JOIN protein AS sq ON otm.pk_proteina = sq.pk_protein
    INNER JOIN ln_inparalog_protein AS ln ON ln.pk_inparalog = otm.pk_inparalogb
    INNER JOIN protein AS sr ON sr.pk_protein = ln.pk_protein
    INNER JOIN species AS o ON o.pk_species = sr.pk_species
    WHERE sq.access = %(access)s
	  AND o.model
    GROUP BY otm.pk_otm, o.taxid, o.name, o.lineage, sq.access, sq.name

    UNION

    SELECT 'Many-to-one' AS type,
			string_agg(DISTINCT sq.access || ',' || sq.name, ' ') AS inparalogs,
			sr.access || ',' || sr.name AS orthologs,
			LENGTH(sr.sequence)::text AS length,
			o.taxid,
			o.name AS species,
			o.lineage
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
    GROUP BY sr.access, o.taxid, o.name, o.lineage, sr.sequence, sr.name

    UNION

    SELECT 'Many-to-many' AS type,
			subb.seqs AS inparalogs,
			suba.seqs AS orthologs,
			suba.lengths AS length,
			suba.taxid,
			s.name AS species,
			s.lineage
    FROM
    (
        SELECT mtm.pk_mtm, string_agg(pa.access || ',' || pa.name, ' ') AS seqs
        FROM mtmlist1 AS mtm
        INNER JOIN ln_inparalog_protein AS la ON la.pk_inparalog = mtm.pk_inparaloga
        INNER JOIN protein AS pa ON pa.pk_protein = la.pk_protein
        GROUP BY mtm.pk_mtm, mtm.pk_inparalogb
    ) AS subb
    INNER JOIN (
        SELECT mtm.pk_mtm, string_agg(pb.access || ',' || pb.name, ' ') AS seqs, string_agg(LENGTH(pb.sequence)::text, ' ') AS lengths, sp.taxid
        FROM mtmlist1 AS mtm
        INNER JOIN ln_inparalog_protein AS lb ON lb.pk_inparalog = mtm.pk_inparalogb
        INNER JOIN protein AS pb ON pb.pk_protein = lb.pk_protein
        INNER JOIN species AS sp ON sp.pk_species = pb.pk_species
		WHERE sp.model
        GROUP BY mtm.pk_mtm, mtm.pk_inparaloga, sp.taxid
    ) AS suba ON subb.pk_mtm = suba.pk_mtm
    INNER JOIN species AS s ON s.taxid = suba.taxid

    UNION

    SELECT 'Many-to-many' AS type,
			suba.seqs AS inparalogs,
			subb.seqs AS orthologs,
			subb.lengths AS length,
			subb.taxid,
			s.name AS species,
			s.lineage
    FROM
    (
        SELECT mtm.pk_mtm, STRING_AGG(pa.access || ',' || pa.name, ' ') AS seqs, string_agg(LENGTH(pa.sequence)::text, ' ') AS lengths, sp.taxid
        FROM mtmlist2 AS mtm
        INNER JOIN ln_inparalog_protein AS la ON la.pk_inparalog = mtm.pk_inparaloga
        INNER JOIN protein AS pa ON pa.pk_protein = la.pk_protein
        INNER JOIN species AS sp ON sp.pk_species = pa.pk_species
		WHERE sp.model
        GROUP BY mtm.pk_mtm, mtm.pk_inparalogb, sp.taxid
    ) AS subb
    INNER JOIN (
        SELECT mtm.pk_mtm, STRING_AGG(pb.access || ',' || pb.name, ' ') AS seqs
        FROM mtmlist2 AS mtm
        INNER JOIN ln_inparalog_protein AS lb ON lb.pk_inparalog = mtm.pk_inparalogb
        INNER JOIN protein AS pb ON pb.pk_protein = lb.pk_protein
        GROUP BY mtm.pk_mtm, mtm.pk_inparaloga
    ) AS suba ON subb.pk_mtm = suba.pk_mtm
    INNER JOIN species AS s ON s.taxid = subb.taxid
) AS o
ORDER BY type DESC
