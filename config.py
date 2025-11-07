"""Gestion de la configuration et des identifiants API Netatmo."""
import os
from pathlib import Path
from dotenv import load_dotenv

def _should_load_dotenv():
    """
    Détermine si le fichier .env doit être chargé.
    
    Le .env n'est chargé que si :
    - On n'est pas dans un environnement CI
    - Les variables d'environnement requises ne sont pas déjà définies
    """
    # Vérifier si on est dans un environnement CI
    is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'
    
    if is_ci:
        return False
    
    # Vérifier si les variables requises sont déjà définies
    required_vars = ['NETATMO_CLIENT_ID', 'NETATMO_CLIENT_SECRET']
    has_required_vars = all(os.getenv(var) for var in required_vars)
    
    # Si les variables sont déjà définies, pas besoin de charger .env
    if has_required_vars:
        return False
    
    # Sinon, on peut charger le .env
    return True

# Charger les variables d'environnement depuis .env si nécessaire
if _should_load_dotenv():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)


class Config:
    """Configuration pour l'API Netatmo."""
    
    def __init__(self):
        self.client_id = os.getenv('NETATMO_CLIENT_ID')
        self.client_secret = os.getenv('NETATMO_CLIENT_SECRET')
        self.username = os.getenv('NETATMO_USERNAME')
        self.password = os.getenv('NETATMO_PASSWORD')
        self.refresh_token = os.getenv('NETATMO_REFRESH_TOKEN')
        
    def validate(self):
        """Valide que toutes les variables requises sont présentes."""
        missing = []
        
        if not self.client_id:
            missing.append('NETATMO_CLIENT_ID')
        if not self.client_secret:
            missing.append('NETATMO_CLIENT_SECRET')
        
        # Soit username/password, soit refresh_token est requis
        has_credentials = (self.username and self.password)
        has_refresh_token = bool(self.refresh_token)
        
        if not has_credentials and not has_refresh_token:
            missing.append('NETATMO_USERNAME et NETATMO_PASSWORD (ou NETATMO_REFRESH_TOKEN)')
            
        if missing:
            raise ValueError(
                f"Variables d'environnement manquantes: {', '.join(missing)}\n"
                f"Veuillez créer un fichier .env avec au minimum:\n"
                f"  - NETATMO_CLIENT_ID\n"
                f"  - NETATMO_CLIENT_SECRET\n"
                f"  - NETATMO_USERNAME et NETATMO_PASSWORD (pour la première authentification)\n"
                f"  - OU NETATMO_REFRESH_TOKEN (si vous avez déjà un refresh token)"
            )
        
        return True
    
    def get_auth_params(self):
        """Retourne les paramètres d'authentification."""
        return {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.username,
            'password': self.password,
        }

