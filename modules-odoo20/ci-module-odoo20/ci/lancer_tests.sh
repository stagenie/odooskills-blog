#!/bin/bash
# Lance les tests Odoo 20 d'une liste de modules sur une base neuve, et échoue
# si le code de sortie OU le journal montre un problème.
# Usage : ODOO="venv/bin/python odoo/odoo-bin --addons-path=…" ci/lancer_tests.sh <base_neuve> <module1,module2>
# Connexion PostgreSQL : variables PGHOST, PGPORT, PGUSER, PGPASSWORD.
set -o pipefail
BASE=$1
MODULES=$2
TAGS="/${MODULES//,/,/}"                 # oski_a,oski_b -> /oski_a,/oski_b
JOURNAL=${JOURNAL:-tests.log}

$ODOO -d "$BASE" -i "$MODULES" --with-demo --test-tags "$TAGS" \
      --db-filter="^${BASE}\$" --http-port="${ODOO_HTTP_PORT:-8069}" \
      --stop-after-init 2>&1 | tee "$JOURNAL"
RC=$?
echo "Code de sortie d'Odoo : $RC"

grep -q "odoo.tests.result: .* of 0 tests" "$JOURNAL" && { echo "ÉCHEC : aucun test lancé"; RC=1; }
grep -q " skipped" "$JOURNAL" && { echo "ÉCHEC : au moins un test sauté"; grep -m3 -E "SkipTest|skipped" "$JOURNAL"; RC=1; }
grep -qE "^[0-9-]+ [0-9:,]+ [0-9]+ (ERROR|CRITICAL) " "$JOURNAL" && { echo "ÉCHEC : ERROR ou CRITICAL dans le journal"; RC=1; }
grep -q "odoo.tests.result" "$JOURNAL" || { echo "ÉCHEC : pas de ligne de résultat"; RC=1; }
echo "Code de sortie : $RC"
exit $RC
