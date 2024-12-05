WITH mtmlist1 AS (
    SELECT mtm.pk_mtm, mtm.pk_inparaloga, mtm.pk_inparalogb
    FROM mtm
    INNER JOIN ln_inparalog_protein AS lr ON lr.pk_inparalog = mtm.pk_inparaloga
    INNER JOIN protein AS pr ON pr.pk_protein = lr.pk_protein -- links prota to pk of protein db (to get access)
    INNER JOIN ln_inparalog_protein AS ln ON ln.pk_inparalog = mtm.pk_inparalogb -- links paralog to the paralog key
    INNER JOIN protein AS pn ON pn.pk_protein = ln.pk_protein -- links paralog to the protein db (get access)
    INNER JOIN species AS sr ON sr.pk_species = pr.pk_species
    INNER JOIN species AS sn ON sn.pk_species = pn.pk_species
    WHERE sn.taxid IN (%(species1)s, %(species2)s)
    AND sr.taxid IN (%(species1)s, %(species2)s)
), mtmlist2 AS (
    SELECT mtm.pk_mtm, mtm.pk_inparaloga, mtm.pk_inparalogb
    FROM mtm
    INNER JOIN ln_inparalog_protein AS lr ON lr.pk_inparalog = mtm.pk_inparaloga
    INNER JOIN protein AS pr ON pr.pk_protein = lr.pk_protein -- links prota to pk of protein db (to get access)
    INNER JOIN ln_inparalog_protein AS ln ON ln.pk_inparalog = mtm.pk_inparalogb -- links paralog to the paralog key
    INNER JOIN protein AS pn ON pn.pk_protein = ln.pk_protein -- links paralog to the protein db (get access)
    INNER JOIN species AS sr ON sr.pk_species = pr.pk_species
    INNER JOIN species AS sn ON sn.pk_species = pn.pk_species
    WHERE sn.taxid IN (%(species1)s, %(species2)s)
    AND sr.taxid IN (%(species1)s, %(species2)s)
)
SELECT type, inparalogs, orthologs, length, taxid2, taxid1, species1, species2, lineage1, lineage2 FROM
(
    SELECT 'One-to-One' AS type,
			pr.access || ',' || pr.name AS inparalogs,
                        sr.taxid AS taxid1,
                        sr.name AS species1,
                        sr.lineage AS lineage1,
			ps.access || ',' || ps.name AS orthologs,
			LENGTH(pr.sequence)::text AS length,
                        ss.taxid AS taxid2,
			ss.name AS species2,
			ss.lineage AS lineage2
    FROM oto
    INNER JOIN protein AS pr ON oto.pk_proteina = pr.pk_protein
    INNER JOIN protein AS ps ON ps.pk_protein = oto.pk_proteinb
    INNER JOIN species AS ss ON ss.pk_species = ps.pk_species
    INNER JOIN species AS sr ON sr.pk_species = pr.pk_species
    WHERE ss.taxid IN (%(species1)s, %(species2)s)
    AND sr.taxid IN (%(species1)s, %(species2)s)

    UNION--Fait

    SELECT 'One-to-many' AS type,
			pr.access || ',' || pr.name AS inparalogs,
			sr.taxid AS taxid1,
			sr.name AS species1,
			sr.lineage AS lineage1,
			string_agg(DISTINCT pn.access || ',' || pn.name, ' ') AS orthologs,
			string_agg(LENGTH(pn.sequence)::text, ' ') AS length,
			sn.taxid AS taxid2,
			sn.name AS species2,
			sn.lineage AS lineage2
    FROM otm
    INNER JOIN protein AS pr ON pr.pk_protein = otm.pk_proteina -- links prota to pk of protein db (to get access)
    INNER JOIN ln_inparalog_protein AS ln ON ln.pk_inparalog = otm.pk_inparalogb -- links paralog to the paralog key
    INNER JOIN protein AS pn ON pn.pk_protein = ln.pk_protein -- links paralog to the protein db (get access)
    INNER JOIN species AS sr ON sr.pk_species = pr.pk_species
    INNER JOIN species AS sn ON sn.pk_species = pn.pk_species
    WHERE sr.taxid IN (%(species1)s, %(species2)s)
    AND sn.taxid IN (%(species1)s, %(species2)s)

    GROUP BY otm.pk_otm, sn.taxid, sn.name, sn.lineage, pr.access, pr.name, sr.taxid, sr.name, sr.lineage

    UNION-- Fait

    SELECT 'Many-to-one' AS type,
			string_agg(DISTINCT pr.access || ',' || pr.name, ' ') AS inparalogs,
			sr.taxid AS taxid1,
			sr.name AS species1,
			sr.lineage AS lineage1,
			pn.access || ',' || pn.name AS orthologs,
			LENGTH(pr.sequence)::text AS length,
			sn.taxid AS taxid2,
			sn.name AS species2,
			sn.lineage AS lineage2
    FROM otm
    INNER JOIN protein AS pr ON pr.pk_protein = otm.pk_proteina -- links prota to pk of protein db (to get access)
    INNER JOIN ln_inparalog_protein AS ln ON ln.pk_inparalog = otm.pk_inparalogb -- links paralog to the paralog key
    INNER JOIN protein AS pn ON pn.pk_protein = ln.pk_protein -- links paralog to the protein db (get access)
    INNER JOIN species AS sr ON sr.pk_species = pr.pk_species
    INNER JOIN species AS sn ON sn.pk_species = pn.pk_species
    WHERE sr.taxid IN (%(species1)s, %(species2)s)
    AND sn.taxid IN (%(species1)s, %(species2)s)
    GROUP BY pr.access, pn.access, sn.taxid, sr.taxid, sn.name, sr.name, sn.lineage, sr.lineage, pr.sequence, pr.name, pn.name

    UNION-- Fait: erreur: must have the same number of columns as the others

    SELECT 'Many-to-many' AS type,
			subb.seqs AS inparalogs,
			subb.taxid AS taxid1,
			sa.name AS species1,
			sa.lineage AS lineage1,
			suba.seqs AS orthologs,
			suba.lengths AS length,
			suba.taxid AS taxid2,
			s.name AS species2,
			s.lineage AS lineage2
    FROM
    (
        SELECT mtm.pk_mtm, string_agg(pa.access || ',' || pa.name, ' ') AS seqs, sa.taxid AS taxid
        FROM mtmlist1 AS mtm
        INNER JOIN ln_inparalog_protein AS la ON la.pk_inparalog = mtm.pk_inparaloga
        INNER JOIN protein AS pa ON pa.pk_protein = la.pk_protein
        INNER JOIN species AS sa ON sa.pk_species = pa.pk_species
        GROUP BY mtm.pk_mtm, mtm.pk_inparalogb, sa.taxid
    ) AS subb
    INNER JOIN (
        SELECT mtm.pk_mtm, string_agg(pb.access || ',' || pb.name, ' ') AS seqs, string_agg(LENGTH(pb.sequence)::text, ' ') AS lengths, sp.taxid AS taxid
        FROM mtmlist1 AS mtm
        INNER JOIN ln_inparalog_protein AS lb ON lb.pk_inparalog = mtm.pk_inparalogb
        INNER JOIN protein AS pb ON pb.pk_protein = lb.pk_protein
        INNER JOIN species AS sp ON sp.pk_species = pb.pk_species
        GROUP BY mtm.pk_mtm, mtm.pk_inparaloga, sp.taxid
    ) AS suba ON subb.pk_mtm = suba.pk_mtm
    INNER JOIN species AS s ON s.taxid = suba.taxid
    INNER JOIN species AS sa ON sa.taxid = subb.taxid

    UNION

    SELECT 'Many-to-many' AS type,
			suba.seqs AS inparalogs,
			suba.taxid AS taxid1,
			sa.name AS species1,
			sa.lineage AS lineage1,
			subb.seqs AS orthologs,
			subb.lengths AS length,
			subb.taxid AS taxid2,
			s.name AS species2,
			s.lineage AS lineage2
    FROM
    (
        SELECT
            mtm.pk_mtm, STRING_AGG(pa.access || ',' || pa.name, ' ') AS seqs,
            string_agg(LENGTH(pa.sequence)::text, ' ') AS lengths, sp.taxid AS taxid
        FROM mtmlist2 AS mtm
        INNER JOIN ln_inparalog_protein AS la ON la.pk_inparalog = mtm.pk_inparaloga
        INNER JOIN protein AS pa ON pa.pk_protein = la.pk_protein
        INNER JOIN species AS sp ON sp.pk_species = pa.pk_species
        GROUP BY mtm.pk_mtm, mtm.pk_inparalogb, sp.taxid
    ) AS subb
    INNER JOIN (
        SELECT mtm.pk_mtm, STRING_AGG(pb.access || ',' || pb.name, ' ') AS seqs, sb.taxid AS taxid
        FROM mtmlist2 AS mtm
        INNER JOIN ln_inparalog_protein AS lb ON lb.pk_inparalog = mtm.pk_inparalogb
        INNER JOIN protein AS pb ON pb.pk_protein = lb.pk_protein
        INNER JOIN species AS sb ON sb.pk_species = pb.pk_species
        GROUP BY mtm.pk_mtm, mtm.pk_inparaloga, sb.taxid
    ) AS suba ON subb.pk_mtm = suba.pk_mtm
    INNER JOIN species AS s ON s.taxid = subb.taxid
    INNER JOIN species AS sa ON sa.taxid = suba.taxid
) AS o
ORDER BY type DESC
