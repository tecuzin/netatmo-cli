"""Client API Netatmo pour interagir avec le thermostat."""
import requests
import time
import sys
from typing import Dict, List, Optional, Any
from config import Config


class NetatmoClient:
    """Client pour interagir avec l'API Netatmo."""
    
    BASE_URL = "https://api.netatmo.com"
    OAUTH_URL = f"{BASE_URL}/oauth2/token"
    
    def __init__(self, config: Config):
        """Initialise le client avec la configuration."""
        self.config = config
        self.config.validate()
        self.access_token = None
        self.refresh_token = config.refresh_token
        self.token_expires_at = 0
        
    def _authenticate(self) -> str:
        """Authentifie le client et retourne le token d'accès."""
        # Si on a un refresh token dans la config, l'utiliser en priorité
        if self.refresh_token and not self.access_token:
            try:
                return self._refresh_access_token()
            except Exception:
                # Si le refresh échoue, on fait une authentification complète
                pass
        
        # Si on a déjà un token valide, le retourner
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # Si on a un refresh token valide (mais token expiré), le rafraîchir
        if self.refresh_token and time.time() < self.token_expires_at + 86400:  # Refresh token valide encore 24h
            try:
                return self._refresh_access_token()
            except Exception:
                # Si le refresh échoue, on fait une authentification complète
                pass
        
        # Authentification complète avec username/password
        # Les headers sont importants pour éviter le blocage
        # Note: La doc Netatmo spécifie charset=UTF-8 dans Content-Type
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'User-Agent': 'NetatmoCLI/1.0'
        }
        
        data = {
            'grant_type': 'password',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'username': self.config.username,
            'password': self.config.password,
        }
        
        # Essayer d'abord sans scope
        response = requests.post(self.OAUTH_URL, data=data, headers=headers)
        
        # Si 403 ou autre erreur, essayer avec scope
        if response.status_code != 200:
            # Essayer avec différents scopes possibles
            scopes_to_try = [
                'read_thermostat write_thermostat',
                'read_thermostat',
                'write_thermostat',
            ]
            
            for scope in scopes_to_try:
                data_with_scope = data.copy()
                data_with_scope['scope'] = scope
                response = requests.post(self.OAUTH_URL, data=data_with_scope, headers=headers)
                if response.status_code == 200:
                    break
        
        # Vérifier la réponse
        if response.status_code != 200:
            error_msg = f"Erreur d'authentification ({response.status_code})"
            
            # Vérifier si c'est une réponse HTML (blocage)
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                error_msg += ": La requête a été bloquée par Netatmo"
                error_msg += "\nCauses possibles:"
                error_msg += "\n  - Identifiants incorrects (Client ID, Client Secret, username, password)"
                error_msg += "\n  - Application non configurée correctement dans le portail développeur"
                error_msg += "\n  - Restrictions de sécurité sur le compte Netatmo"
            else:
                # Essayer de parser comme JSON
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_code = error_data.get('error')
                        error_msg += f": {error_code}"
                        
                        # Messages d'erreur spécifiques selon le code d'erreur
                        if error_code == 'invalid_client':
                            error_msg += "\nLe Client ID ou Client Secret est incorrect."
                            error_msg += "\nVérifiez dans le portail développeur (https://dev.netatmo.com/) que:"
                            error_msg += "\n  - Le Client ID correspond exactement à celui de votre application"
                            error_msg += "\n  - Le Client Secret correspond exactement à celui de votre application"
                            error_msg += "\n  - Il n'y a pas d'espaces ou de caractères invisibles dans le fichier .env"
                        elif error_code == 'invalid_grant':
                            error_msg += "\nLe username ou password est incorrect, ou le grant type n'est pas autorisé."
                            error_msg += "\nVérifiez que:"
                            error_msg += "\n  - Le username et password sont ceux de votre compte Netatmo"
                            error_msg += "\n  - Le grant type 'password' est activé pour votre application"
                        elif error_code == 'invalid_scope':
                            error_msg += "\nLe scope demandé n'est pas autorisé pour votre application."
                            error_msg += "\nVérifiez dans le portail développeur que votre application a accès à l'API Energy."
                        
                        if 'error_description' in error_data:
                            error_msg += f"\nDescription: {error_data.get('error_description')}"
                except:
                    # Si ce n'est pas du JSON, prendre les 200 premiers caractères
                    text = response.text[:200].replace('\n', ' ')
                    if text:
                        error_msg += f": {text}"
            
            raise ValueError(error_msg)
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        self.refresh_token = token_data.get('refresh_token', self.refresh_token)
        # Netatmo utilise généralement 10800 secondes (3 heures) pour expires_in
        self.token_expires_at = time.time() + token_data.get('expires_in', 10800) - 60  # -60 pour marge de sécurité
        
        # Afficher un message informatif si un nouveau refresh token est obtenu
        if 'refresh_token' in token_data:
            print(f"✓ Authentification réussie. Refresh token sauvegardé dans la config.", file=sys.stderr)
        
        return self.access_token
    
    def _refresh_access_token(self) -> str:
        """Rafraîchit le token d'accès avec le refresh token."""
        if not self.refresh_token:
            raise ValueError("Aucun refresh token disponible pour rafraîchir l'authentification")
        
        # Note: La doc Netatmo spécifie charset=UTF-8 dans Content-Type
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'User-Agent': 'NetatmoCLI/1.0'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret
        }
        
        response = requests.post(self.OAUTH_URL, data=data, headers=headers)
        
        if response.status_code != 200:
            error_msg = f"Erreur de rafraîchissement du token ({response.status_code})"
            
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                error_msg += ": La requête a été bloquée par Netatmo"
            else:
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_code = error_data.get('error')
                        error_msg += f": {error_code}"
                        if error_code == 'invalid_grant':
                            error_msg += "\nLe refresh token est invalide ou expiré. Une nouvelle authentification est nécessaire."
                except:
                    text = response.text[:200].replace('\n', ' ')
                    if text:
                        error_msg += f": {text}"
            
            raise ValueError(error_msg)
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        # Le refresh token peut être renouvelé, on garde le nouveau s'il est fourni
        self.refresh_token = token_data.get('refresh_token', self.refresh_token)
        self.token_expires_at = time.time() + token_data.get('expires_in', 10800) - 60  # Netatmo utilise 10800s (3h)
        
        return self.access_token
    
    def _get_access_token(self) -> str:
        """Récupère un token d'accès valide."""
        if not self.access_token or time.time() >= self.token_expires_at:
            self._authenticate()
        return self.access_token
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Effectue une requête authentifiée à l'API Netatmo."""
        token = self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        
        # Gestion améliorée des erreurs
        if response.status_code != 200:
            error_msg = f"Erreur API ({response.status_code})"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f": {error_data.get('error')}"
                if 'error_description' in error_data:
                    error_msg += f" - {error_data.get('error_description')}"
            except:
                # Si ce n'est pas du JSON, prendre les premiers caractères
                text = response.text[:200].replace('\n', ' ')
                if text:
                    error_msg += f": {text}"
            raise ValueError(error_msg)
        
        return response.json()
    
    def get_homes_data(self) -> Dict[str, Any]:
        """Récupère la liste des maisons et leurs données."""
        return self._request('GET', '/api/homesdata')
    
    def get_home_status(self, home_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère le statut de la maison et des thermostats.
        
        Args:
            home_id: ID de la maison (optionnel, si non fourni, utilise la première maison)
        """
        # Si home_id n'est pas fourni, obtenir la liste des maisons d'abord
        if not home_id:
            homes_data = self.get_homes_data()
            homes = homes_data.get('body', {}).get('homes', [])
            if not homes:
                raise ValueError("Aucune maison trouvée dans votre compte Netatmo")
            home_id = homes[0].get('id')
            if not home_id:
                raise ValueError("Impossible de déterminer l'ID de la maison")
        
        # Appeler homestatus avec le home_id
        return self._request('GET', '/api/homestatus', params={'home_id': home_id})
    
    def get_thermostat_status(self, debug: bool = False) -> Dict[str, Any]:
        """Récupère le statut du thermostat."""
        # Obtenir d'abord la liste des maisons pour trouver le home_id
        homes_data = self.get_homes_data()
        
        if debug:
            import json
            print("DEBUG - homes_data structure:", file=sys.stderr)
            print(json.dumps(homes_data, indent=2)[:2000], file=sys.stderr)
        
        homes = homes_data.get('body', {}).get('homes', [])
        
        if not homes:
            raise ValueError("Aucune maison trouvée dans votre compte Netatmo")
        
        # Parcourir les maisons pour trouver un thermostat
        for home in homes:
            home_id = home.get('id')
            if not home_id:
                continue
            
            # Obtenir le statut de cette maison
            try:
                home_status = self.get_home_status(home_id)
                
                if debug:
                    import json
                    print(f"\nDEBUG - home_status structure for {home_id}:", file=sys.stderr)
                    print(json.dumps(home_status, indent=2)[:2000], file=sys.stderr)
            except Exception as e:
                if debug:
                    print(f"DEBUG - Error getting home_status: {e}", file=sys.stderr)
                continue
            
            # La structure est : body.home.rooms (données de température) et body.home.modules (infos modules)
            home_data = home_status.get('body', {}).get('home', {})
            rooms = home_data.get('rooms', [])
            modules = home_data.get('modules', [])
            
            # Chercher le module thermostat dans les modules
            thermostat_module = None
            for module in modules:
                module_type = module.get('type')
                if module_type in ['NATherm1', 'NRV', 'OTM', 'OTM-C']:
                    thermostat_module = module
                    break
            
            if not thermostat_module:
                continue
            
            # Trouver la room correspondante
            thermostat_room = None
            module_id = thermostat_module.get('id')
            
            # Méthode 1: Utiliser room_id du module (depuis homes_data)
            module_room_id = None
            for mod in home.get('modules', []):
                if mod.get('id') == module_id:
                    module_room_id = mod.get('room_id')
                    break
            
            # Chercher la room correspondante dans home_status
            for room in rooms:
                room_id = room.get('id')
                # Vérifier si c'est la room du module
                if room_id == module_room_id:
                    thermostat_room = room
                    break
                
                # Vérifier aussi via module_ids dans homes_data
                for r in home.get('rooms', []):
                    if r.get('id') == room_id and module_id in r.get('module_ids', []):
                        thermostat_room = room
                        break
                    if thermostat_room:
                        break
                if thermostat_room:
                    break
            
            # Si pas de room trouvée, utiliser la première room (fallback)
            if not thermostat_room and rooms:
                thermostat_room = rooms[0]
            
            if thermostat_room:
                # Obtenir le nom du module depuis homes_data
                module_name = thermostat_module.get('name', 'Thermostat')
                for mod in home.get('modules', []):
                    if mod.get('id') == module_id:
                        module_name = mod.get('name', 'Thermostat')
                        break
                
                return {
                    'home_id': home_id,
                    'room_id': thermostat_room.get('id'),
                    'module_id': module_id,
                    'module_name': module_name,
                    'current_temp': thermostat_room.get('therm_measured_temperature'),
                    'target_temp': thermostat_room.get('therm_setpoint_temperature'),
                    'setpoint_mode': thermostat_room.get('therm_setpoint_mode'),
                    'boiler_status': thermostat_module.get('boiler_status', False),
                    'heating_power_request': thermostat_room.get('heating_power_request', 0),
                }
        
        # Si debug, afficher la structure complète pour diagnostic
        if debug:
            import json
            print("\nDEBUG - Structure complète des données:", file=sys.stderr)
            print(json.dumps(homes_data, indent=2)[:5000], file=sys.stderr)
        
        raise ValueError("Aucun thermostat trouvé dans vos maisons Netatmo")
    
    def set_thermpoint(self, home_id: str, room_id: str, mode: str, 
                       temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Définit le point de consigne du thermostat.
        
        Args:
            home_id: ID de la maison
            room_id: ID de la pièce
            mode: Mode ('manual', 'away', 'hg' pour hors gel, 'program', 'off')
            temperature: Température cible (requis pour mode 'manual')
        """
        data = {
            'home_id': home_id,
            'room_id': room_id,
            'mode': mode
        }
        
        if mode == 'manual' and temperature is not None:
            data['temp'] = temperature
        
        return self._request('POST', '/api/setthermpoint', json=data)
    
    def set_temperature(self, temperature: float) -> Dict[str, Any]:
        """Définit la température cible en mode manuel."""
        status = self.get_thermostat_status()
        return self.set_thermpoint(
            status['home_id'],
            status['room_id'],
            'manual',
            temperature
        )
    
    def set_frost_guard(self, enabled: bool) -> Dict[str, Any]:
        """Active ou désactive le mode hors gel."""
        status = self.get_thermostat_status()
        mode = 'hg' if enabled else 'program'
        return self.set_thermpoint(
            status['home_id'],
            status['room_id'],
            mode
        )
    
    def get_measure(self, device_id: str, module_id: str, scale: str = '1day',
                   types: List[str] = None, start_date: Optional[int] = None,
                   end_date: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les mesures historiques.
        
        Args:
            device_id: ID du device
            module_id: ID du module
            scale: Échelle de temps ('max', '30min', '1hour', '3hours', '1day', '1week', '1month')
            types: Types de mesures (ex: ['Temperature'])
            start_date: Timestamp de début (optionnel)
            end_date: Timestamp de fin (optionnel)
        """
        if types is None:
            types = ['Temperature']
        
        params = {
            'device_id': device_id,
            'module_id': module_id,
            'scale': scale,
            'type': ','.join(types)
        }
        
        if start_date:
            params['date_begin'] = start_date
        if end_date:
            params['date_end'] = end_date
        
        return self._request('GET', '/api/getmeasure', params=params)
    
    def get_thermostat_history(self, days: int = 7, debug: bool = False) -> Dict[str, Any]:
        """Récupère l'historique des températures."""
        status = self.get_thermostat_status()
        home_id = status['home_id']
        module_id = status['module_id']
        
        # Obtenir les informations du module pour trouver le bridge
        homes_data = self.get_homes_data()
        homes = homes_data.get('body', {}).get('homes', [])
        
        bridge_id = None
        for home in homes:
            if home.get('id') == home_id:
                for module in home.get('modules', []):
                    if module.get('id') == module_id:
                        bridge_id = module.get('bridge')
                        break
                break
        
        if not bridge_id:
            raise ValueError("Bridge ID non trouvé pour le thermostat")
        
        end_date = int(time.time())
        start_date = end_date - (days * 24 * 3600)
        
        # Pour getmeasure avec un thermostat bridgé:
        # - device_id = bridge (NAPlug)
        # - module_id = module thermostat (NATherm1)
        result = self.get_measure(
            bridge_id,  # Le bridge (NAPlug) comme device_id
            module_id,  # Le thermostat comme module_id
            scale='1hour',
            types=['Temperature'],
            start_date=start_date,
            end_date=end_date
        )
        
        if debug:
            import json
            print("\nDEBUG - getmeasure response structure:", file=sys.stderr)
            print(json.dumps(result, indent=2)[:3000], file=sys.stderr)
        
        return result
    
    def get_statistics(self, days: int = 7, debug: bool = False) -> Dict[str, Any]:
        """Calcule les statistiques de température."""
        history = self.get_thermostat_history(days, debug=debug)
        
        # Parser les données de mesure
        # La structure peut être différente selon l'API
        temperatures = []
        
        # Structure 1: body est une liste
        if 'body' in history:
            body = history['body']
            if isinstance(body, list):
                for entry in body:
                    if 'value' in entry and entry['value']:
                        # Les valeurs sont stockées comme [[temp1], [temp2], ...]
                        # Chaque élément de value est une liste avec une seule température
                        for value_set in entry['value']:
                            if isinstance(value_set, list) and len(value_set) > 0:
                                temp = value_set[0]  # La température est le premier élément
                                if temp is not None:
                                    temperatures.append(temp)
            elif isinstance(body, dict):
                # Structure alternative
                for key, entry in body.items():
                    if isinstance(entry, dict) and 'value' in entry:
                        values = entry['value']
                        if isinstance(values, list):
                            for value_set in values:
                                if isinstance(value_set, list) and len(value_set) > 0:
                                    temp = value_set[0]
                                    if temp is not None:
                                        temperatures.append(temp)
        
        if not temperatures:
            return {
                'average': None,
                'min': None,
                'max': None,
                'count': 0
            }
        
        return {
            'average': sum(temperatures) / len(temperatures),
            'min': min(temperatures),
            'max': max(temperatures),
            'count': len(temperatures)
        }

