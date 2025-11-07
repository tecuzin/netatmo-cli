#!/bin/bash
# Script de test avec curl pour diagnostiquer l'authentification Netatmo

# Charger les variables d'environnement
if [ ! -f .env ]; then
    echo "Erreur: fichier .env non trouvé"
    exit 1
fi

# Charger le .env en évitant les problèmes de format
set -a
source .env 2>/dev/null || {
    # Méthode alternative : parser ligne par ligne
    while IFS='=' read -r key value; do
        # Ignorer les commentaires et lignes vides
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        # Exporter la variable
        export "$key=$value"
    done < .env
}
set +a

echo "Test d'authentification Netatmo avec curl"
echo "=========================================="
echo "Client ID: ${NETATMO_CLIENT_ID:0:10}..."
echo "Username: $NETATMO_USERNAME"
echo ""

echo "Test 1: Authentification sans scope"
echo "-------------------------------------"
response=$(curl -s -w "\n%{http_code}" -X POST "https://api.netatmo.com/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" \
  -H "User-Agent: NetatmoCLI/1.0" \
  -d "grant_type=password" \
  -d "client_id=690dd6fff019c6165603dabe" \
  -d "client_secret=2FSlGWsp9csrZyYmqBtKA3Q4F2JAfiFTZZbudBylheV" \
  -d "username=david.rochelet@lilo.org" \
  -d "password=Mamaison2025#")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "  ✓ Succès! Token obtenu"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo "  ✗ Échec (HTTP $http_code)"
    if echo "$body" | grep -q '"error"'; then
        error_type=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', 'unknown'))" 2>/dev/null || echo "unknown")
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
        
        if [ "$error_type" = "invalid_client" ]; then
            echo ""
            echo "  ⚠ Le Client ID ou Client Secret est incorrect."
            echo "  Vérifiez dans le portail développeur (https://dev.netatmo.com/) que:"
            echo "    - Le Client ID correspond exactement à celui de votre application"
            echo "    - Le Client Secret correspond exactement à celui de votre application"
            echo "    - Il n'y a pas d'espaces dans le fichier .env"
        elif [ "$error_type" = "invalid_grant" ]; then
            echo ""
            echo "  ⚠ Le username/password est incorrect ou le grant type n'est pas autorisé."
        elif [ "$error_type" = "invalid_scope" ]; then
            echo ""
            echo "  ⚠ Le scope demandé n'est pas autorisé pour votre application."
        fi
    elif echo "$body" | grep -q "blocked"; then
        echo "  La requête a été bloquée par Netatmo"
        echo "  Référence: $(echo "$body" | grep -oP 'x-azure-ref[^<]*' | head -1 || echo 'N/A')"
    fi
fi
echo "  Status HTTP: $http_code"

echo ""
echo "Test 2: Authentification avec scope read_thermostat"
echo "----------------------------------------------------"
response=$(curl -s -w "\n%{http_code}" -X POST "https://api.netatmo.com/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded;charset=UTF-8" \
  -H "User-Agent: NetatmoCLI/1.0" \
  -d "grant_type=password" \
  -d "client_id=$NETATMO_CLIENT_ID" \
  -d "client_secret=$NETATMO_CLIENT_SECRET" \
  -d "username=$NETATMO_USERNAME" \
  -d "password=$NETATMO_PASSWORD" \
  -d "scope=read_thermostat")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "  ✓ Succès! Token obtenu"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo "  ✗ Échec (HTTP $http_code)"
    if echo "$body" | grep -q "error"; then
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    elif echo "$body" | grep -q "blocked"; then
        echo "  La requête a été bloquée par Netatmo"
    fi
fi
echo "  Status HTTP: $http_code"

echo ""
echo "=========================================="
echo "Si vous obtenez toujours 403, le problème vient probablement de:"
echo "1. La configuration de l'application dans le portail développeur"
echo "2. Les identifiants incorrects"
echo "3. Des restrictions de sécurité sur le compte Netatmo"

