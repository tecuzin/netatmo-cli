# CLI Netatmo Thermostat

Application en ligne de commande pour piloter votre thermostat Netatmo connecté à votre chaudière.

> **Note importante** : Cette application utilise exclusivement `api.netatmo.com`. Le domaine `api.netatmo.net` sera retiré le 8 septembre 2025 par Netatmo.

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Obtenir les identifiants API Netatmo :
   - Rendez-vous sur [https://dev.netatmo.com/](https://dev.netatmo.com/)
   - Créez un compte développeur si ce n'est pas déjà fait
   - Allez dans "My Apps" et créez une nouvelle application
   - Notez votre `Client ID` et `Client Secret`

3. Configurer les identifiants :
   Créez un fichier `.env` à la racine du projet avec le contenu suivant :
```bash
NETATMO_CLIENT_ID=your_client_id_here
NETATMO_CLIENT_SECRET=your_client_secret_here
NETATMO_USERNAME=your_email@example.com
NETATMO_PASSWORD=your_password_here
```
   Remplacez les valeurs par vos identifiants réels.

## Utilisation

### Afficher le statut du thermostat
```bash
python netatmo_cli.py status
```

### Régler la température cible
```bash
python netatmo_cli.py set 20.5
```

### Activer/désactiver le mode hors gel
```bash
python netatmo_cli.py frost-guard on
python netatmo_cli.py frost-guard off
```

### Afficher l'historique
```bash
python netatmo_cli.py history
python netatmo_cli.py history --days 14
```

### Afficher les statistiques
```bash
python netatmo_cli.py stats
```

### Format JSON (pour intégration avec d'autres outils)
```bash
python netatmo_cli.py status --json
```

## Commandes disponibles

- `status` : Affiche la température actuelle, la température cible, le mode et le statut
- `set <température>` : Définit une nouvelle température cible (en °C)
- `frost-guard on|off` : Active ou désactive le mode hors gel
- `history [--days N]` : Affiche l'historique des températures (par défaut 7 jours)
- `stats` : Affiche des statistiques (température moyenne, min, max)

## Options globales

- `--json` : Affiche la sortie au format JSON
- `--debug` : Mode debug (affiche plus de détails sur les erreurs)

## Dépannage

### Erreur 403 Forbidden / "The request is blocked" lors de l'authentification

Si vous obtenez une erreur 403 ou le message "The request is blocked", vérifiez :

1. **Identifiants corrects** : Vérifiez que votre `Client ID`, `Client Secret`, `username` et `password` dans le fichier `.env` sont corrects.
   - Le `Client ID` et `Client Secret` doivent être ceux de votre application créée sur https://dev.netatmo.com/
   - Le `username` et `password` sont ceux de votre compte Netatmo (celui utilisé pour vous connecter à l'application mobile)

2. **Configuration de l'application dans le portail développeur** :
   - Allez sur https://dev.netatmo.com/ et connectez-vous
   - Vérifiez que votre application est bien créée et active
   - Assurez-vous que l'application a les permissions nécessaires (Energy API / Thermostat)
   - Vérifiez que l'application n'a pas de restrictions IP ou autres restrictions de sécurité

3. **Format du fichier .env** : Vérifiez que le fichier `.env` est bien formaté :
   - Pas d'espaces autour du `=`
   - Pas de guillemets autour des valeurs (sauf si nécessaire pour les caractères spéciaux)
   - Pas de lignes vides ou de commentaires mal formatés
   - Exemple correct :
     ```
     NETATMO_CLIENT_ID=abc123def456
     NETATMO_CLIENT_SECRET=xyz789
     NETATMO_USERNAME=email@example.com
     NETATMO_PASSWORD=MonMotDePasse#123
     ```

4. **Caractères spéciaux dans le mot de passe** : Si votre mot de passe contient des caractères spéciaux, assurez-vous qu'ils sont correctement écrits dans le fichier `.env`.

5. **Mode debug** : Utilisez l'option `--debug` pour obtenir plus d'informations sur l'erreur :
   ```bash
   python netatmo_cli.py status --debug
   ```

**Note importante** : Si la requête est bloquée par Netatmo, cela peut aussi indiquer que votre compte ou votre application a des restrictions de sécurité. Dans ce cas, contactez le support Netatmo.

### Scripts de diagnostic

Deux scripts de test sont disponibles pour diagnostiquer les problèmes d'authentification :

**Script Python :**
```bash
python3 test_auth.py
```

**Script curl (pour tester directement avec curl) :**
```bash
./test_curl.sh
```

Ces scripts testent différentes méthodes d'authentification et affichent des informations détaillées pour aider à identifier le problème.

### Vérifications importantes dans le portail développeur

Si vous obtenez toujours une erreur 403 **même avec curl**, le problème vient de la configuration Netatmo, pas du code. Vérifiez dans le portail développeur Netatmo (https://dev.netatmo.com/) :

1. **Type d'authentification** : 
   - Vérifiez que votre application utilise bien le type d'authentification "Password" 
   - Certaines applications peuvent nécessiter un flux OAuth2 avec redirection au lieu du grant type "password"
   - Vérifiez dans les paramètres de l'application si le grant type "password" est activé

2. **Permissions API** : 
   - Assurez-vous que l'application a accès à l'API **Energy** (pour les thermostats)
   - Vérifiez que les scopes `read_thermostat` et `write_thermostat` sont autorisés

3. **État de l'application** : 
   - Vérifiez que l'application est bien **"Active"** et non en attente d'approbation
   - Certaines applications nécessitent une validation manuelle par Netatmo

4. **Whitelist IP / Restrictions de sécurité** : 
   - Si votre application a une whitelist IP, assurez-vous que votre adresse IP est autorisée
   - Vérifiez s'il y a d'autres restrictions de sécurité activées

5. **Identifiants** :
   - Vérifiez que le `Client ID` et `Client Secret` correspondent exactement à ceux affichés dans le portail
   - Assurez-vous qu'il n'y a pas d'espaces ou de caractères invisibles
   - Recréez une nouvelle application si nécessaire pour obtenir de nouveaux identifiants

6. **Compte Netatmo** :
   - Le `username` et `password` doivent être ceux de votre compte Netatmo principal
   - Testez que vous pouvez vous connecter avec ces identifiants sur https://my.netatmo.com/

**Si toutes ces vérifications sont correctes et que l'erreur 403 persiste**, il est possible que :
- Netatmo ait restreint le grant type "password" pour votre région/compte
- L'application nécessite une approbation spéciale pour accéder à l'API Energy
- Il y ait un problème temporaire avec l'API Netatmo

Dans ce cas, **contactez le support Netatmo** avec les références d'erreur (x-azure-ref dans les headers de réponse) pour obtenir de l'aide.

