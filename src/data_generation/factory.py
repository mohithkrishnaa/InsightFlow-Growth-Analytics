# Generator Factory Layer for InsightFlow Synthetic Data Generation Engine
"""
This module defines the Generator Factory responsible for loading configuration
exactly once and instantiating individual generator components with injected
validated configurations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Type
from src.data_generation.config import AppConfig, load_config

# Setup local logger
logger = logging.getLogger("InsightFlowGenerator")

class BaseGenerator(ABC):
    """
    Abstract Base Class for all InsightFlow synthetic data generators.
    All future generator components must extend this class.
    """
    def __init__(self, config: AppConfig):
        """
        Initializes the generator with a shared, validated configuration object.

        Args:
            config (AppConfig): The application configuration settings block.
        """
        self.config = config

    @abstractmethod
    def generate(self, *args, **kwargs):
        """
        Generates synthetic records. Must be implemented by concrete subclasses.
        """
        pass


class UserGenerator(BaseGenerator):
    """Generator component responsible for producing user demographics and credit history profiles."""
    def generate(self, *args, **kwargs):
        logger.info("Executing UserGenerator logic...")
        raise NotImplementedError("UserGenerator logic not implemented yet.")


class MarketingEventGenerator(BaseGenerator):
    """Generator component responsible for producing campaign attribution clickstream logs."""
    def generate(self, *args, **kwargs):
        logger.info("Executing MarketingEventGenerator logic...")
        raise NotImplementedError("MarketingEventGenerator logic not implemented yet.")


class AppEventGenerator(BaseGenerator):
    """Generator component responsible for producing user action, pageview, and clickstream events."""
    def generate(self, *args, **kwargs):
        logger.info("Executing AppEventGenerator logic...")
        raise NotImplementedError("AppEventGenerator logic not implemented yet.")


class LoanEventGenerator(BaseGenerator):
    """Generator component responsible for producing loan application lifecycle transactions."""
    def generate(self, *args, **kwargs):
        logger.info("Executing LoanEventGenerator logic...")
        raise NotImplementedError("LoanEventGenerator logic not implemented yet.")


class ExperimentGenerator(BaseGenerator):
    """Generator component responsible for producing A/B split assignments and outcomes."""
    def generate(self, *args, **kwargs):
        logger.info("Executing ExperimentGenerator logic...")
        raise NotImplementedError("ExperimentGenerator logic not implemented yet.")


class GeneratorFactory:
    """
    Factory class responsible for initializing the application configuration exactly once
    and creating specific generator instances with dependency injection of the AppConfig.
    """
    # Shared configuration instance to prevent multiple loading calls (Class-level singleton state)
    _config_instance: AppConfig = None

    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initializes the factory and loads configuration parameters exactly once.

        Args:
            config_path (str): File path to settings YAML configuration.
        """
        if GeneratorFactory._config_instance is None:
            try:
                # Load and validate configuration settings
                GeneratorFactory._config_instance = load_config(config_path)
                logger.info("Application configuration successfully initialized exactly once in GeneratorFactory.")
            except Exception as e:
                logger.error(f"Failed to initialize configuration in GeneratorFactory: {e}")
                raise e
        
        self.config = GeneratorFactory._config_instance

        # Registry for mapping generator types to their respective classes
        self._generator_registry: Dict[str, Type[BaseGenerator]] = {
            "user": UserGenerator,
            "marketing_event": MarketingEventGenerator,
            "app_event": AppEventGenerator,
            "loan_event": LoanEventGenerator,
            "experiment": ExperimentGenerator,
        }

    def get_generator(self, generator_type: str) -> BaseGenerator:
        """
        Creates and returns an instance of a registered generator.
        Injects the shared validated configuration object.

        Args:
            generator_type (str): Name string of the desired generator (e.g. 'user', 'app_event').

        Returns:
            BaseGenerator: Concrete subclass generator instance initialized with AppConfig.

        Raises:
            KeyError: If the requested generator type is unregistered or unknown.
        """
        gen_type_lower = generator_type.lower().strip()
        if gen_type_lower not in self._generator_registry:
            error_msg = (
                f"Unknown generator type '{generator_type}'. "
                f"Supported types: {list(self._generator_registry.keys())}"
            )
            logger.error(error_msg)
            raise KeyError(error_msg)

        generator_class = self._generator_registry[gen_type_lower]
        logger.info(f"Instantiating and returning generator: {generator_class.__name__}")
        return generator_class(self.config)
