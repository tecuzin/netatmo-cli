#!/bin/bash
# Commande curl brute pour tester l'authentification Netatmo
# Remplacez les valeurs entre < > par vos identifiants réels

curl -X POST "https://api.netatmo.com/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "User-Agent: NetatmoCLI/1.0" \
  -d "grant_type=password" \
  -d "client_id=<VOTRE_CLIENT_ID>" \
  -d "client_secret=<VOTRE_CLIENT_SECRET>" \
  -d "username=<VOTRE_EMAIL>" \
  -d "password=<VOTRE_MOT_DE_PASSE>" \
  -d "scope=read_thermostat write_thermostat"

