import os
import streamlit as st
from typing import Dict, Optional, Any
import logging

class AzureConfig:
    """Azure configuration manager for E2B converter application"""
    
    def __init__(self):
        # Setup logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.is_azure_deployment = self._detect_azure_deployment()
        self.config = self._load_configuration()
    
    def _detect_azure_deployment(self) -> bool:
        """Detect if running on Azure App Service"""
        return os.getenv('WEBSITE_SITE_NAME') is not None
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from appropriate source"""
        try:
            if self.is_azure_deployment:
                return self._load_azure_config()
            else:
                return self._load_local_config()
        except Exception as e:
            self.logger.error(f"Configuration loading failed: {str(e)}")
            return self._get_fallback_config()
    
    def _load_azure_config(self) -> Dict[str, Any]:
        """Load configuration from Azure environment variables"""
        config = {
            # Azure OpenAI Configuration
            "azure_openai": {
                "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                "api_key": os.getenv("AZURE_OPENAI_KEY"),
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4-32k")
            },
            
            # Azure Resource Configuration
            "azure_resource": {
                "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
                "resource_group": os.getenv("AZURE_RESOURCE_GROUP", "e2b-converter-rg"),
                "tenant_id": os.getenv("AZURE_TENANT_ID")
            },
            
            # Application Configuration
            "app": {
                "environment": "azure",
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "max_file_size": int(os.getenv("MAX_FILE_SIZE", "52428800")),  # 50MB
                "max_zip_size": int(os.getenv("MAX_ZIP_SIZE", "209715200"))   # 200MB
            }
        }
        
        return config
    
    def _load_local_config(self) -> Dict[str, Any]:
        """Load configuration from Streamlit secrets"""
        try:
            config = {
                # Azure OpenAI Configuration
                "azure_openai": {
                    "endpoint": st.secrets.get("azure", {}).get("AZURE_OPENAI_ENDPOINT"),
                    "api_key": st.secrets.get("azure", {}).get("AZURE_OPENAI_KEY"),
                    "api_version": st.secrets.get("azure", {}).get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                    "deployment_name": st.secrets.get("azure", {}).get("AZURE_OPENAI_DEPLOYMENT", "gpt-4-32k")
                },
                
                # Azure Resource Configuration
                "azure_resource": {
                    "subscription_id": st.secrets.get("azure", {}).get("AZURE_SUBSCRIPTION_ID"),
                    "resource_group": st.secrets.get("azure", {}).get("AZURE_RESOURCE_GROUP", "e2b-converter-rg"),
                    "tenant_id": st.secrets.get("azure", {}).get("AZURE_TENANT_ID")
                },
                
                # Application Configuration
                "app": {
                    "environment": "local",
                    "debug": True,
                    "max_file_size": 52428800,  # 50MB
                    "max_zip_size": 209715200   # 200MB
                }
            }
            
            return config
            
        except Exception as e:
            self.logger.warning(f"Failed to load local config: {str(e)}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration when other methods fail"""
        return {
            "azure_openai": {
                "endpoint": None,
                "api_key": None,
                "api_version": "2024-02-15-preview",
                "deployment_name": "gpt-4-32k"
            },

            "azure_resource": {
                "subscription_id": None,
                "resource_group": "e2b-converter-rg",
                "tenant_id": None
            },
            "app": {
                "environment": "fallback",
                "debug": False,
                "max_file_size": 52428800,
                "max_zip_size": 209715200
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration"""
        return self.config
    
    def get_azure_openai_config(self) -> Dict[str, Any]:
        """Get Azure OpenAI specific configuration"""
        return self.config.get("azure_openai", {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application specific configuration"""
        return self.config.get("app", {})
    
    def is_azure_services_available(self) -> bool:
        """Check if Azure services are properly configured"""
        azure_openai = self.get_azure_openai_config()
        return bool(azure_openai.get("endpoint") and azure_openai.get("api_key"))
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the current configuration"""
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        # Check Azure OpenAI configuration
        openai_config = self.get_azure_openai_config()
        if not openai_config.get("endpoint"):
            validation_result["issues"].append("Azure OpenAI endpoint not configured")
            validation_result["valid"] = False
        
        if not openai_config.get("api_key"):
            validation_result["issues"].append("Azure OpenAI API key not configured")
            validation_result["valid"] = False
        
        # Check application configuration
        app_config = self.get_app_config()
        if app_config.get("max_file_size", 0) <= 0:
            validation_result["warnings"].append("Invalid maximum file size configuration")
        
        return validation_result
    
    def get_configuration_status(self) -> str:
        """Get a human-readable configuration status"""
        if self.is_azure_deployment:
            if self.is_azure_services_available():
                return "Azure services fully configured"
            else:
                return "Azure deployment with incomplete configuration"
        else:
            if self.is_azure_services_available():
                return "Local development with Azure services"
            else:
                return "Local development mode (limited functionality)"
    
    def log_configuration_status(self) -> None:
        """Log the current configuration status"""
        status = self.get_configuration_status()
        validation = self.validate_configuration()
        
        self.logger.info(f"Configuration Status: {status}")
        
        if validation["issues"]:
            self.logger.error(f"Configuration Issues: {', '.join(validation['issues'])}")
        
        if validation["warnings"]:
            self.logger.warning(f"Configuration Warnings: {', '.join(validation['warnings'])}")
        
        self.logger.info(f"Environment: {self.config.get('app', {}).get('environment', 'unknown')}")
