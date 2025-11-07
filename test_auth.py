#!/usr/bin/env python3
"""Script de test pour diagnostiquer les problèmes d'authentification Netatmo."""
import requests
import sys
from config import Config

def test_auth():
    """Teste l'authentification avec différents formats."""
    config = Config()
    config.validate()
    
    print("Test d'authentification Netatmo")
    print("=" * 50)
    print(f"Client ID: {config.client_id[:10]}..." if config.client_id else "Client ID: NON DÉFINI")
    print(f"Client Secret: {'*' * 10}..." if config.client_secret else "Client Secret: NON DÉFINI")
    print(f"Username: {config.username}")
    print(f"Password: {'*' * len(config.password) if config.password else 'NON DÉFINI'}")
    print()
    
    # Utiliser uniquement api.netatmo.com (api.netatmo.net sera retiré le 8 septembre 2025)
    url = "https://api.netatmo.com/oauth2/token"
    print(f"\nTest avec URL: {url}")
    print("-" * 50)
    
    # Test 1: Sans scope, avec headers standards
    print("Test 1: Authentification sans scope...")
    data = {
        'grant_type': 'password',
        'client_id': config.client_id,
        'client_secret': config.client_secret,
        'username': config.username,
        'password': config.password,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'User-Agent': 'NetatmoCLI/1.0'
    }
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"  ✓ Succès! Access token obtenu")
            print(f"  Token expire dans: {token_data.get('expires_in', 'N/A')} secondes")
            return True
        else:
            print(f"  ✗ Échec")
            if 'application/json' in response.headers.get('Content-Type', ''):
                error_data = response.json()
                print(f"  Erreur: {error_data.get('error', 'N/A')}")
                print(f"  Description: {error_data.get('error_description', 'N/A')}")
            else:
                print(f"  Réponse HTML (bloquée)")
                print(f"  Premiers 200 caractères: {response.text[:200]}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")
    
    print()
    
    # Test 2: Avec scope read_thermostat
    print("Test 2: Authentification avec scope 'read_thermostat'...")
    data_with_scope = data.copy()
    data_with_scope['scope'] = 'read_thermostat'
    
    try:
        response = requests.post(url, data=data_with_scope, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"  ✓ Succès! Access token obtenu")
            return True
        else:
            print(f"  ✗ Échec")
            if 'application/json' in response.headers.get('Content-Type', ''):
                error_data = response.json()
                print(f"  Erreur: {error_data.get('error', 'N/A')}")
                print(f"  Description: {error_data.get('error_description', 'N/A')}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")
    
    print()
    print("=" * 50)
    print("Diagnostic:")
    print("Si toutes les tentatives échouent avec 403, vérifiez:")
    print("1. Les identifiants dans le fichier .env sont corrects")
    print("2. L'application est bien créée et active sur https://dev.netatmo.com/")
    print("3. L'application a les permissions Energy API / Thermostat")
    print("4. Le compte Netatmo (username/password) est valide")
    print("5. Il n'y a pas de restrictions de sécurité sur l'application")
    
    return False

if __name__ == '__main__':
    try:
        success = test_auth()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

