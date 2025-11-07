#!/usr/bin/env python3
"""Application CLI pour piloter le thermostat Netatmo."""
import argparse
import json
import sys
from typing import Any, Dict

from config import Config
from netatmo_client import NetatmoClient


def format_output(data: Any, json_output: bool = False) -> str:
    """Formate la sortie en texte ou JSON."""
    if json_output:
        return json.dumps(data, indent=2, ensure_ascii=False)
    return format_text_output(data)


def format_text_output(data: Any) -> str:
    """Formate la sortie en texte lisible."""
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                lines.append(f"{key}: {value}")
            elif isinstance(value, str):
                lines.append(f"{key}: {value}")
            elif isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key}: {sub_value}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    return str(data)


def cmd_status(client: NetatmoClient, args: argparse.Namespace) -> Dict[str, Any]:
    """Affiche le statut du thermostat."""
    try:
        status = client.get_thermostat_status(debug=args.debug)
        
        current_temp = status.get('current_temp')
        target_temp = status.get('target_temp')
        
        output = {
            'module_name': status.get('module_name', 'N/A'),
            'current_temperature': f"{current_temp:.1f}°C" if current_temp is not None else 'N/A',
            'target_temperature': f"{target_temp:.1f}°C" if target_temp is not None else 'N/A',
            'setpoint_mode': status.get('setpoint_mode', 'N/A'),
            'boiler_status': 'ON' if status.get('boiler_status') else 'OFF',
            'heating_power_request': status.get('heating_power_request', 0)
        }
        
        print(format_output(output, args.json))
        return output
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_set(client: NetatmoClient, args: argparse.Namespace) -> Dict[str, Any]:
    """Définit la température cible."""
    try:
        result = client.set_temperature(args.temperature)
        
        output = {
            'status': 'success',
            'temperature_set': args.temperature,
            'message': f"Température réglée à {args.temperature}°C"
        }
        
        print(format_output(output, args.json))
        return output
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_frost_guard(client: NetatmoClient, args: argparse.Namespace) -> Dict[str, Any]:
    """Active ou désactive le mode hors gel."""
    try:
        enabled = args.state.lower() == 'on'
        result = client.set_frost_guard(enabled)
        
        output = {
            'status': 'success',
            'frost_guard': 'enabled' if enabled else 'disabled',
            'message': f"Mode hors gel {'activé' if enabled else 'désactivé'}"
        }
        
        print(format_output(output, args.json))
        return output
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_history(client: NetatmoClient, args: argparse.Namespace) -> Dict[str, Any]:
    """Affiche l'historique des températures."""
    try:
        history = client.get_thermostat_history(args.days, debug=args.debug)
        
        if args.json:
            print(format_output(history, True))
            return history
        
        # Format texte pour l'historique
        print(f"Historique des températures (derniers {args.days} jours):")
        print("-" * 50)
        
        from datetime import datetime
        
        # Parser les données selon différentes structures possibles
        data_found = False
        
        if 'body' in history:
            body = history['body']
            
            # Structure 1: body est une liste
            if isinstance(body, list):
                for entry in body:
                    if 'value' in entry and entry['value']:
                        data_found = True
                        beg_time = entry.get('beg_time', 0)
                        step_time = entry.get('step_time', 3600)  # Par défaut 1 heure
                        
                        # Les valeurs sont dans value = [[temp1], [temp2], ...]
                        for index, value_set in enumerate(entry['value']):
                            if isinstance(value_set, list) and len(value_set) > 0:
                                temp = value_set[0]  # La température est le premier élément
                                if temp is not None:
                                    # Calculer le timestamp pour cette valeur
                                    timestamp = beg_time + (index * step_time)
                                    dt = datetime.fromtimestamp(timestamp)
                                    print(f"{dt.strftime('%Y-%m-%d %H:%M')}: {temp:.1f}°C")
            
            # Structure 2: body est un dict (structure alternative)
            elif isinstance(body, dict):
                for key, entry in body.items():
                    if isinstance(entry, dict) and 'value' in entry:
                        data_found = True
                        beg_time = entry.get('beg_time', 0)
                        step_time = entry.get('step_time', 3600)
                        
                        values = entry['value']
                        if isinstance(values, list):
                            for index, value_set in enumerate(values):
                                if isinstance(value_set, list) and len(value_set) > 0:
                                    temp = value_set[0]
                                    if temp is not None:
                                        timestamp = beg_time + (index * step_time)
                                        dt = datetime.fromtimestamp(timestamp)
                                        print(f"{dt.strftime('%Y-%m-%d %H:%M')}: {temp:.1f}°C")
        
        if not data_found:
            print("Aucune donnée disponible")
            if args.debug:
                import json
                print("\nDEBUG - Structure de la réponse:", file=sys.stderr)
                print(json.dumps(history, indent=2)[:2000], file=sys.stderr)
        
        return history
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cmd_stats(client: NetatmoClient, args: argparse.Namespace) -> Dict[str, Any]:
    """Affiche les statistiques."""
    try:
        stats = client.get_statistics(args.days, debug=args.debug)
        
        output = {
            'period_days': args.days,
            'average_temperature': f"{stats.get('average', 0):.1f}°C" if stats.get('average') else 'N/A',
            'min_temperature': f"{stats.get('min', 0):.1f}°C" if stats.get('min') else 'N/A',
            'max_temperature': f"{stats.get('max', 0):.1f}°C" if stats.get('max') else 'N/A',
            'data_points': stats.get('count', 0)
        }
        
        print(format_output(output, args.json))
        return output
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Point d'entrée principal de l'application CLI."""
    parser = argparse.ArgumentParser(
        description='Piloter votre thermostat Netatmo connecté à votre chaudière',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Arguments globaux partagés
    common_args = argparse.ArgumentParser(add_help=False)
    common_args.add_argument(
        '--json',
        action='store_true',
        help='Afficher la sortie au format JSON'
    )
    common_args.add_argument(
        '--debug',
        action='store_true',
        help='Mode debug (affiche plus de détails sur les erreurs)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Commande status
    parser_status = subparsers.add_parser('status', help='Afficher le statut du thermostat', parents=[common_args])
    parser_status.set_defaults(func=cmd_status)
    
    # Commande set
    parser_set = subparsers.add_parser('set', help='Définir la température cible', parents=[common_args])
    parser_set.add_argument('temperature', type=float, help='Température cible en °C')
    parser_set.set_defaults(func=cmd_set)
    
    # Commande frost-guard
    parser_frost = subparsers.add_parser('frost-guard', help='Activer/désactiver le mode hors gel', parents=[common_args])
    parser_frost.add_argument('state', choices=['on', 'off'], help='État: on ou off')
    parser_frost.set_defaults(func=cmd_frost_guard)
    
    # Commande history
    parser_history = subparsers.add_parser('history', help='Afficher l\'historique des températures', parents=[common_args])
    parser_history.add_argument('--days', type=int, default=7, help='Nombre de jours (défaut: 7)')
    parser_history.set_defaults(func=cmd_history)
    
    # Commande stats
    parser_stats = subparsers.add_parser('stats', help='Afficher les statistiques', parents=[common_args])
    parser_stats.add_argument('--days', type=int, default=7, help='Nombre de jours (défaut: 7)')
    parser_stats.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        config = Config()
        client = NetatmoClient(config)
        if args.debug:
            import logging
            logging.basicConfig(level=logging.DEBUG)
        args.func(client, args)
    except ValueError as e:
        print(f"Erreur de configuration: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

