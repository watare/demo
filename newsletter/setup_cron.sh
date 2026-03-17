#!/bin/bash
# ============================================================
# Titanair Executive Brief — Installation du cron quotidien
# ============================================================
# Ce script installe une tâche cron qui envoie la newsletter
# tous les jours du lundi au vendredi à 7h30 (heure de Paris).
#
# Usage: bash setup_cron.sh
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CRON_SCHEDULE="${CRON_SCHEDULE:-30 7 * * 1-5}"  # Lun-Ven 07:30

CRON_JOB="${CRON_SCHEDULE} cd ${SCRIPT_DIR} && ${PYTHON_BIN} main.py >> ${SCRIPT_DIR}/output/cron.log 2>&1"
CRON_MARKER="# titanair-newsletter"

echo "=== Titanair Newsletter — Configuration cron ==="
echo ""
echo "Répertoire : ${SCRIPT_DIR}"
echo "Python      : ${PYTHON_BIN}"
echo "Planning    : ${CRON_SCHEDULE} (Lun-Ven 07:30)"
echo ""

# Vérifier que .env existe
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    echo "ERREUR : Fichier .env introuvable."
    echo "Copiez .env.example en .env et remplissez les valeurs :"
    echo "  cp ${SCRIPT_DIR}/.env.example ${SCRIPT_DIR}/.env"
    exit 1
fi

# Vérifier les dépendances Python
echo "Vérification des dépendances Python..."
"${PYTHON_BIN}" -c "import sib_api_v3_sdk; import dotenv" 2>/dev/null || {
    echo "Installation des dépendances..."
    "${PYTHON_BIN}" -m pip install -r "${SCRIPT_DIR}/requirements.txt"
}

# Créer le répertoire output
mkdir -p "${SCRIPT_DIR}/output"

# Supprimer l'ancien cron s'il existe, puis ajouter le nouveau
(crontab -l 2>/dev/null | grep -v "${CRON_MARKER}") | {
    cat
    echo "${CRON_JOB} ${CRON_MARKER}"
} | crontab -

echo ""
echo "Cron installé avec succès !"
echo "La newsletter sera envoyée du lundi au vendredi à 07:30."
echo ""
echo "Vérification :"
crontab -l | grep "${CRON_MARKER}"
echo ""
echo "Pour tester manuellement :"
echo "  cd ${SCRIPT_DIR} && ${PYTHON_BIN} main.py --dry-run"
echo ""
echo "Pour désinstaller :"
echo "  crontab -l | grep -v '${CRON_MARKER}' | crontab -"
