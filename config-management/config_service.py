"""
Configuration Management Service
Centralized configuration for all 1,500 agents with dynamic updates
"""

import os
import json
import redis
import hvac
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from consul import Consul
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent configuration model"""
    agent_id: str
    name: str
    category: str
    port: int
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    rate_limit: int = 100
    rate_limit_window: int = 60
    replicas: int = 2
    enabled: bool = True
    # Feature flags
    circuit_breaker_enabled: bool = True
    caching_enabled: bool = True
    metrics_enabled: bool = True


class ConfigurationManager:
    """Central configuration management for all agents"""

    def __init__(
        self,
        consul_host: str = "localhost",
        consul_port: int = 8500,
        vault_addr: str = "http://localhost:8200",
        vault_token: Optional[str] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379
    ):
        # Consul for configuration
        self.consul = Consul(host=consul_host, port=consul_port)

        # Vault for secrets
        self.vault = hvac.Client(url=vault_addr, token=vault_token)

        # Redis for caching and feature flags
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

        logger.info("Configuration manager initialized")

    def register_agent(self, config: AgentConfig) -> bool:
        """Register agent configuration in Consul"""
        try:
            key = f"agents/{config.agent_id}/config"
            value = json.dumps(asdict(config))
            self.consul.kv.put(key, value)

            # Cache in Redis
            self.redis.setex(
                f"agent:config:{config.agent_id}",
                3600,  # 1 hour TTL
                value
            )

            logger.info(f"Registered agent: {config.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register agent {config.agent_id}: {e}")
            return False

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration with caching"""
        try:
            # Try cache first
            cached = self.redis.get(f"agent:config:{agent_id}")
            if cached:
                data = json.loads(cached)
                return AgentConfig(**data)

            # Fetch from Consul
            _, data = self.consul.kv.get(f"agents/{agent_id}/config")
            if data:
                config_dict = json.loads(data['Value'])
                config = AgentConfig(**config_dict)

                # Update cache
                self.redis.setex(
                    f"agent:config:{agent_id}",
                    3600,
                    json.dumps(asdict(config))
                )

                return config

            return None
        except Exception as e:
            logger.error(f"Failed to get config for {agent_id}: {e}")
            return None

    def update_agent_config(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent configuration dynamically"""
        try:
            config = self.get_agent_config(agent_id)
            if not config:
                return False

            # Update fields
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            # Save updated config
            return self.register_agent(config)
        except Exception as e:
            logger.error(f"Failed to update config for {agent_id}: {e}")
            return False

    def get_secret(self, secret_path: str, key: str) -> Optional[str]:
        """Retrieve secret from Vault"""
        try:
            secret = self.vault.secrets.kv.v2.read_secret_version(path=secret_path)
            return secret['data']['data'].get(key)
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_path}/{key}: {e}")
            return None

    def set_feature_flag(self, feature: str, enabled: bool, scope: str = "global") -> bool:
        """Set feature flag for dynamic feature toggling"""
        try:
            key = f"feature_flags:{scope}:{feature}"
            self.redis.set(key, "1" if enabled else "0")
            logger.info(f"Set feature flag {feature} to {enabled} for scope {scope}")
            return True
        except Exception as e:
            logger.error(f"Failed to set feature flag {feature}: {e}")
            return False

    def is_feature_enabled(self, feature: str, agent_id: Optional[str] = None) -> bool:
        """Check if feature is enabled (supports per-agent overrides)"""
        try:
            # Check agent-specific override first
            if agent_id:
                key = f"feature_flags:agent:{agent_id}:{feature}"
                value = self.redis.get(key)
                if value is not None:
                    return value == "1"

            # Check global flag
            key = f"feature_flags:global:{feature}"
            value = self.redis.get(key)
            return value == "1" if value else False
        except Exception as e:
            logger.error(f"Failed to check feature flag {feature}: {e}")
            return False

    def list_all_agents(self) -> list[str]:
        """List all registered agents"""
        try:
            _, agents = self.consul.kv.get("agents/", recurse=True)
            if agents:
                agent_ids = set()
                for item in agents:
                    key = item['Key']
                    # Extract agent_id from path like "agents/{agent_id}/config"
                    parts = key.split('/')
                    if len(parts) >= 2:
                        agent_ids.add(parts[1])
                return sorted(agent_ids)
            return []
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []

    def bulk_update(self, updates: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """Bulk update multiple agents"""
        results = {}
        for agent_id, config_updates in updates.items():
            results[agent_id] = self.update_agent_config(agent_id, config_updates)
        return results

    def get_environment_config(self, environment: str = "production") -> Dict[str, Any]:
        """Get environment-specific configuration"""
        try:
            _, data = self.consul.kv.get(f"environments/{environment}")
            if data:
                return json.loads(data['Value'])
            return {}
        except Exception as e:
            logger.error(f"Failed to get environment config: {e}")
            return {}


class EnvironmentConfig:
    """Environment-specific configuration loader"""

    @staticmethod
    def load_from_env() -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            # Infrastructure
            "consul_host": os.getenv("CONSUL_HOST", "localhost"),
            "consul_port": int(os.getenv("CONSUL_PORT", "8500")),
            "vault_addr": os.getenv("VAULT_ADDR", "http://localhost:8200"),
            "vault_token": os.getenv("VAULT_TOKEN"),
            "redis_host": os.getenv("REDIS_HOST", "localhost"),
            "redis_port": int(os.getenv("REDIS_PORT", "6379")),

            # Database
            "db_host": os.getenv("DB_HOST", "localhost"),
            "db_port": int(os.getenv("DB_PORT", "5432")),
            "db_name": os.getenv("DB_NAME", "agents_db"),
            "db_user": os.getenv("DB_USER", "agents_admin"),

            # API Keys
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),

            # Application
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "debug": os.getenv("DEBUG", "false").lower() == "true",
        }


if __name__ == "__main__":
    # Example usage
    config_manager = ConfigurationManager()

    # Register example agent
    agent_config = AgentConfig(
        agent_id="business_plan_agent_009",
        name="Business Plan Agent",
        category="business_ops",
        port=8209
    )

    config_manager.register_agent(agent_config)

    # Retrieve configuration
    retrieved = config_manager.get_agent_config("business_plan_agent_009")
    print(f"Retrieved config: {retrieved}")

    # Set feature flag
    config_manager.set_feature_flag("new_prompt_template", True)

    # Check feature
    enabled = config_manager.is_feature_enabled("new_prompt_template")
    print(f"Feature enabled: {enabled}")
