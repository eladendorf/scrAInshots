"""
Configuration manager for API keys and credentials
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration including API keys"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.scrainshots'
        self.config_file = self.config_dir / 'integrations.json'
        self.key_file = self.config_dir / '.key'
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize encryption
        self.cipher = self._get_cipher()
    
    def _get_cipher(self) -> Fernet:
        """Get or create encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
        
        return Fernet(key)
    
    def _encrypt(self, value: str) -> str:
        """Encrypt a string value"""
        if not value:
            return ""
        return base64.b64encode(self.cipher.encrypt(value.encode())).decode()
    
    def _decrypt(self, value: str) -> str:
        """Decrypt a string value"""
        if not value:
            return ""
        try:
            return self.cipher.decrypt(base64.b64decode(value.encode())).decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ""
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                encrypted_config = json.load(f)
            
            # Decrypt sensitive fields
            config = {}
            for key, value in encrypted_config.items():
                if key in ['fireflies_api_key', 'email_password', 
                          'outlook_client_secret']:
                    config[key] = self._decrypt(value) if value else ""
                else:
                    config[key] = value
            
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration with encryption"""
        try:
            # Encrypt sensitive fields
            encrypted_config = {}
            for key, value in config.items():
                if key in ['fireflies_api_key', 'email_password', 
                          'outlook_client_secret']:
                    encrypted_config[key] = self._encrypt(value) if value else ""
                else:
                    encrypted_config[key] = value
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(encrypted_config, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
            
            logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            # Fireflies
            'fireflies_api_key': '',
            
            # Email settings
            'email_enabled': False,
            'email_provider': 'gmail',
            'email_address': '',
            'email_password': '',
            
            # Custom IMAP settings
            'imap_server': '',
            'imap_port': 993,
            
            # Outlook OAuth (advanced)
            'outlook_enabled': False,
            'outlook_client_id': '',
            'outlook_client_secret': '',
            'outlook_tenant_id': '',
            
            # General settings
            'screenshot_dir': os.path.expanduser('~/Desktop/screenshots'),
            'macos_notes_enabled': True
        }
    
    def update_fireflies_key(self, api_key: str) -> bool:
        """Update Fireflies API key"""
        config = self.get_config()
        config['fireflies_api_key'] = api_key
        return self.save_config(config)
    
    def update_email_settings(self, provider: str, address: str, 
                            password: str, imap_server: str = None,
                            imap_port: int = 993) -> bool:
        """Update email settings"""
        config = self.get_config()
        config['email_enabled'] = True
        config['email_provider'] = provider
        config['email_address'] = address
        config['email_password'] = password
        
        if imap_server:
            config['imap_server'] = imap_server
            config['imap_port'] = imap_port
        
        return self.save_config(config)
    
    def get_env_dict(self) -> Dict[str, str]:
        """Get configuration as environment variables"""
        config = self.get_config()
        
        env_dict = {}
        
        # Fireflies
        if config.get('fireflies_api_key'):
            env_dict['FIREFLIES_API_KEY'] = config['fireflies_api_key']
        
        # Email
        if config.get('email_enabled') and config.get('email_address'):
            env_dict['EMAIL_ADDRESS'] = config['email_address']
            env_dict['EMAIL_PASSWORD'] = config.get('email_password', '')
            env_dict['EMAIL_PROVIDER'] = config.get('email_provider', 'gmail')
            
            if config.get('imap_server'):
                env_dict['IMAP_SERVER'] = config['imap_server']
                env_dict['IMAP_PORT'] = str(config.get('imap_port', 993))
        
        # Outlook
        if config.get('outlook_enabled'):
            if config.get('outlook_client_id'):
                env_dict['OUTLOOK_CLIENT_ID'] = config['outlook_client_id']
            if config.get('outlook_client_secret'):
                env_dict['OUTLOOK_CLIENT_SECRET'] = config['outlook_client_secret']
            if config.get('outlook_tenant_id'):
                env_dict['OUTLOOK_TENANT_ID'] = config['outlook_tenant_id']
        
        # General
        if config.get('screenshot_dir'):
            env_dict['SCREENSHOT_DIR'] = config['screenshot_dir']
        
        return env_dict
    
    def test_email_connection(self) -> Dict[str, Any]:
        """Test email connection with current settings"""
        config = self.get_config()
        
        if not config.get('email_enabled') or not config.get('email_address'):
            return {'success': False, 'error': 'Email not configured'}
        
        try:
            from integrations.simple_email_integration import SimpleEmailIntegration
            
            email_client = SimpleEmailIntegration(
                email_address=config['email_address'],
                password=config['email_password'],
                provider=config['email_provider']
            )
            
            # Set custom IMAP settings if provided
            if config.get('imap_server'):
                email_client.settings['imap_server'] = config['imap_server']
                email_client.settings['imap_port'] = config['imap_port']
            
            email_client.connect()
            email_client.disconnect()
            
            return {'success': True, 'message': 'Email connection successful'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_fireflies_connection(self) -> Dict[str, Any]:
        """Test Fireflies API connection"""
        config = self.get_config()
        
        if not config.get('fireflies_api_key'):
            return {'success': False, 'error': 'Fireflies API key not configured'}
        
        try:
            from integrations.fireflies_integration import FirefliesIntegration
            
            fireflies = FirefliesIntegration(api_key=config['fireflies_api_key'])
            
            # Try a simple query to test the connection
            query = """
            query TestConnection {
                user {
                    email
                }
            }
            """
            
            result = fireflies._make_graphql_request(query)
            
            if result and 'user' in result:
                return {
                    'success': True, 
                    'message': f"Connected as {result['user'].get('email', 'Unknown')}"
                }
            else:
                return {'success': False, 'error': 'Invalid API response'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}