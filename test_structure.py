#!/usr/bin/env python3
"""Script de test pour valider la structure de l'application."""
import sys
import importlib.util

def test_imports():
    """Teste que tous les modules peuvent être importés."""
    print("Test des imports...")
    try:
        from config import Config
        print("  ✓ config.py")
        
        from netatmo_client import NetatmoClient
        print("  ✓ netatmo_client.py")
        
        from netatmo_cli import cmd_status, cmd_set, cmd_frost_guard, cmd_history, cmd_stats
        print("  ✓ netatmo_cli.py (commandes)")
        
        return True
    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return False

def test_config():
    """Teste la classe Config."""
    print("\nTest de la configuration...")
    try:
        from config import Config
        config = Config()
        
        # Vérifier que la validation fonctionne
        try:
            config.validate()
            print("  ✓ Validation de la configuration OK")
        except ValueError as e:
            print(f"  ⚠ Configuration incomplète (normal si .env n'est pas configuré): {e}")
        
        return True
    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return False

def test_client_structure():
    """Teste la structure du client."""
    print("\nTest de la structure du client...")
    try:
        from netatmo_client import NetatmoClient
        from config import Config
        
        # Vérifier que toutes les méthodes publiques existent
        required_methods = [
            'get_home_status',
            'get_thermostat_status',
            'set_temperature',
            'set_frost_guard',
            'get_thermostat_history',
            'get_statistics'
        ]
        
        for method in required_methods:
            if hasattr(NetatmoClient, method):
                print(f"  ✓ Méthode {method} présente")
            else:
                print(f"  ✗ Méthode {method} manquante")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return False

def test_cli_commands():
    """Teste que toutes les commandes CLI sont définies."""
    print("\nTest des commandes CLI...")
    try:
        from netatmo_cli import (
            cmd_status, cmd_set, cmd_frost_guard, 
            cmd_history, cmd_stats, format_output
        )
        
        commands = [
            ('cmd_status', cmd_status),
            ('cmd_set', cmd_set),
            ('cmd_frost_guard', cmd_frost_guard),
            ('cmd_history', cmd_history),
            ('cmd_stats', cmd_stats),
        ]
        
        for name, func in commands:
            if callable(func):
                print(f"  ✓ {name} est callable")
            else:
                print(f"  ✗ {name} n'est pas callable")
                return False
        
        # Tester format_output
        test_data = {'test': 'value', 'number': 42}
        text_output = format_output(test_data, False)
        json_output = format_output(test_data, True)
        
        if text_output and json_output:
            print(f"  ✓ format_output fonctionne")
        else:
            print(f"  ✗ format_output ne fonctionne pas")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Exécute tous les tests."""
    print("=" * 50)
    print("Tests de structure de l'application Netatmo CLI")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_client_structure,
        test_cli_commands,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Erreur lors du test {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Résumé:")
    passed = sum(results)
    total = len(results)
    print(f"Tests réussis: {passed}/{total}")
    
    if all(results):
        print("✓ Tous les tests sont passés!")
        return 0
    else:
        print("✗ Certains tests ont échoué")
        return 1

if __name__ == '__main__':
    sys.exit(main())

