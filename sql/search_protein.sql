SELECT access, name
FROM protein
WHERE access LIKE %(pattern)s
   OR name LIKE %(pattern)s
LIMIT %(limit)s
