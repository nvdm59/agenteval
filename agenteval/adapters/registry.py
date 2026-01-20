"""Registry for agent adapters."""

from typing import Dict, List, Type
from agenteval.adapters.base import BaseAdapter


class AdapterRegistry:
    """
    Registry for managing agent adapters.

    Adapters can be registered using the decorator pattern or directly.
    This allows for discovery and instantiation of adapters by name.

    Example:
        @AdapterRegistry.register("my_provider")
        class MyAdapter(BaseAdapter):
            ...

        # Later, get the adapter
        adapter = AdapterRegistry.get_adapter("my_provider", config)
    """

    _adapters: Dict[str, Type[BaseAdapter]] = {}
    _metadata: Dict[str, Dict] = {}

    @classmethod
    def register(
        cls,
        name: str,
        description: str = "",
        supports_tools: bool = True,
        supports_streaming: bool = True,
    ):
        """
        Decorator to register an adapter.

        Args:
            name: Unique name for the adapter (e.g., "anthropic", "openai")
            description: Human-readable description
            supports_tools: Whether adapter supports tool calling
            supports_streaming: Whether adapter supports streaming

        Returns:
            Decorator function

        Example:
            @AdapterRegistry.register(
                "anthropic",
                description="Anthropic Claude adapter",
                supports_tools=True
            )
            class AnthropicAdapter(BaseAdapter):
                ...
        """

        def decorator(adapter_class: Type[BaseAdapter]):
            if name in cls._adapters:
                raise ValueError(f"Adapter '{name}' is already registered")

            if not issubclass(adapter_class, BaseAdapter):
                raise TypeError(f"Adapter must be a subclass of BaseAdapter")

            cls._adapters[name] = adapter_class
            cls._metadata[name] = {
                "name": name,
                "class_name": adapter_class.__name__,
                "description": description,
                "supports_tools": supports_tools,
                "supports_streaming": supports_streaming,
            }
            return adapter_class

        return decorator

    @classmethod
    def register_adapter(
        cls,
        name: str,
        adapter_class: Type[BaseAdapter],
        description: str = "",
        **kwargs,
    ) -> None:
        """
        Register an adapter directly (without decorator).

        Args:
            name: Unique name for the adapter
            adapter_class: Adapter class to register
            description: Human-readable description
            **kwargs: Additional metadata

        Raises:
            ValueError: If adapter name is already registered
            TypeError: If adapter_class is not a BaseAdapter subclass
        """
        if name in cls._adapters:
            raise ValueError(f"Adapter '{name}' is already registered")

        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError(f"Adapter must be a subclass of BaseAdapter")

        cls._adapters[name] = adapter_class
        cls._metadata[name] = {
            "name": name,
            "class_name": adapter_class.__name__,
            "description": description,
            **kwargs,
        }

    @classmethod
    def get_adapter(cls, name: str, config: Dict) -> BaseAdapter:
        """
        Get adapter instance by name.

        Args:
            name: Adapter name
            config: Configuration dictionary for the adapter

        Returns:
            Instantiated adapter

        Raises:
            ValueError: If adapter name is not registered
        """
        if name not in cls._adapters:
            available = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unknown adapter: '{name}'. Available adapters: {available}"
            )

        adapter_class = cls._adapters[name]
        return adapter_class(config)

    @classmethod
    def list_adapters(cls) -> List[str]:
        """
        List all registered adapter names.

        Returns:
            List of adapter names
        """
        return list(cls._adapters.keys())

    @classmethod
    def get_adapter_info(cls, name: str) -> Dict:
        """
        Get metadata for a specific adapter.

        Args:
            name: Adapter name

        Returns:
            Dictionary with adapter metadata

        Raises:
            ValueError: If adapter name is not registered
        """
        if name not in cls._metadata:
            raise ValueError(f"Unknown adapter: '{name}'")

        return cls._metadata[name].copy()

    @classmethod
    def get_all_adapter_info(cls) -> Dict[str, Dict]:
        """
        Get metadata for all registered adapters.

        Returns:
            Dictionary mapping adapter names to their metadata
        """
        return cls._metadata.copy()

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if an adapter is registered.

        Args:
            name: Adapter name

        Returns:
            True if registered, False otherwise
        """
        return name in cls._adapters

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister an adapter.

        Args:
            name: Adapter name

        Raises:
            ValueError: If adapter name is not registered
        """
        if name not in cls._adapters:
            raise ValueError(f"Adapter '{name}' is not registered")

        del cls._adapters[name]
        del cls._metadata[name]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters (mainly for testing)."""
        cls._adapters.clear()
        cls._metadata.clear()


# Convenience function
def get_adapter(name: str, config: Dict) -> BaseAdapter:
    """
    Convenience function to get an adapter instance.

    Args:
        name: Adapter name
        config: Configuration dictionary

    Returns:
        Instantiated adapter

    Raises:
        ValueError: If adapter name is not registered
    """
    return AdapterRegistry.get_adapter(name, config)


def list_adapters() -> List[str]:
    """
    Convenience function to list available adapters.

    Returns:
        List of adapter names
    """
    return AdapterRegistry.list_adapters()
