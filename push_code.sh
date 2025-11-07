#!/bin/bash

# Script de push du code vers le dépôt Git
# Utilise les credentials depuis .env.gitcredentials

set -e  # Arrêter en cas d'erreur

# Vérifier que le fichier .env.gitcredentials existe
if [ ! -f ".env.gitcredentials" ]; then
    echo "Erreur: Le fichier .env.gitcredentials n'existe pas"
    exit 1
fi

# Charger les variables d'environnement depuis .env.gitcredentials
export $(grep -v '^#' .env.gitcredentials | xargs)

# Vérifier que toutes les variables nécessaires sont définies
if [ -z "$GIT_HTTP_REPO_URL" ]; then
    echo "Erreur: GIT_HTTP_REPO_URL n'est pas défini dans .env.gitcredentials"
    exit 1
fi

if [ -z "$GIT_API_TOKEN" ]; then
    echo "Erreur: GIT_API_TOKEN n'est pas défini dans .env.gitcredentials"
    exit 1
fi

if [ -z "$GIT_API_LOGIN" ]; then
    echo "Erreur: GIT_API_LOGIN n'est pas défini dans .env.gitcredentials"
    exit 1
fi

echo "Configuration du dépôt Git..."

# Extraire l'URL avec les credentials
# Format: https://username:token@host/path/repo.git
# Pour GitHub, on peut utiliser juste le token ou username:token
# Extraire le nom d'utilisateur de l'email si nécessaire
GIT_USERNAME=$(echo "$GIT_API_LOGIN" | cut -d'@' -f1)
REPO_URL_WITH_CREDENTIALS=$(echo "$GIT_HTTP_REPO_URL" | sed "s|https://|https://${GIT_USERNAME}:${GIT_API_TOKEN}@|")

# Configurer le remote origin s'il n'existe pas, sinon le mettre à jour
if git remote get-url origin &>/dev/null; then
    echo "Mise à jour du remote origin..."
    git remote set-url origin "$REPO_URL_WITH_CREDENTIALS"
else
    echo "Ajout du remote origin..."
    git remote add origin "$REPO_URL_WITH_CREDENTIALS"
fi

# Afficher le remote (sans le token pour la sécurité)
echo "Remote configuré: $(echo $GIT_HTTP_REPO_URL | sed 's|https://|https://***:***@|')"

# Ajouter tous les fichiers (sauf ceux dans .gitignore)
echo "Ajout des fichiers..."
# Exclure explicitement .env.gitcredentials pour éviter de commiter les secrets
git add . -- ':!.env.gitcredentials' 2>/dev/null || true

# Vérifier s'il y a des changements à committer
if ! git diff --staged --quiet; then
    # Créer un commit avec un message par défaut ou utiliser celui fourni
    COMMIT_MESSAGE="${1:-Update code}"
    echo "Création du commit: $COMMIT_MESSAGE"
    git commit -m "$COMMIT_MESSAGE"
else
    echo "Aucun changement à committer"
fi

# Push vers le dépôt
echo "Push vers le dépôt..."
BRANCH=$(git branch --show-current)
echo "Branche actuelle: $BRANCH"

# Push avec configuration des credentials
if ! git push -u origin "$BRANCH"; then
    echo "Erreur lors du push. Tentative avec force push (nécessaire après nettoyage de l'historique)..."
    git push -u origin "$BRANCH" --force
fi

echo "Push réussi!"

