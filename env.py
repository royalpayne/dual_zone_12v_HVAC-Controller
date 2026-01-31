# Environment Detection and Loading
# ==================================
#
# This module provides environment-based configuration for the RV thermostat.
#
# Environments:
#   - dev:  Development/testing on local hardware or simulator
#   - prod: Production deployment in the RV
#
# To set the environment:
#   1. Create a file named 'ENVIRONMENT' containing: dev, test, or prod
#   2. Or create config_local.py with: ENV = "dev"
#   3. Default is "prod" if no environment is specified

import sys

# Default environment
_current_env = "prod"

def _read_env_file():
    """Try to read environment from ENVIRONMENT file"""
    try:
        with open("ENVIRONMENT", "r") as f:
            env = f.read().strip().lower()
            if env in ("dev", "test", "prod"):
                return env
    except:
        pass
    return None

def _read_env_from_local():
    """Try to read environment from config_local.py"""
    try:
        from config_local import ENV
        if ENV in ("dev", "test", "prod"):
            return ENV
    except:
        pass
    return None

def get_env():
    """Get the current environment name"""
    global _current_env

    # Priority: ENVIRONMENT file > config_local.py > default
    env = _read_env_file()
    if env:
        _current_env = env
        return _current_env

    env = _read_env_from_local()
    if env:
        _current_env = env
        return _current_env

    return _current_env

def is_dev():
    """Check if running in development environment"""
    return get_env() == "dev"

def is_test():
    """Check if running in test environment"""
    return get_env() == "test"

def is_prod():
    """Check if running in production environment"""
    return get_env() == "prod"

def load_env_config():
    """
    Load environment-specific configuration.
    Returns a dict of config values that override defaults.
    """
    env = get_env()
    overrides = {}

    # Load environment-specific config
    try:
        if env == "dev":
            from config_dev import CONFIG as env_config
            overrides.update(env_config)
        elif env == "test":
            from config_test import CONFIG as env_config
            overrides.update(env_config)
        elif env == "prod":
            from config_prod import CONFIG as env_config
            overrides.update(env_config)
    except ImportError:
        pass  # No env-specific config file

    # Load local overrides (highest priority)
    try:
        from config_local import CONFIG as local_config
        overrides.update(local_config)
    except (ImportError, AttributeError):
        pass  # No local config or no CONFIG dict

    return overrides

# Initialize on import
_current_env = get_env()
print(f"[env] Environment: {_current_env}")
