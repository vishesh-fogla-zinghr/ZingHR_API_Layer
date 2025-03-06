from typing import Dict, Type, Callable

class CustomMediator:
    _instance = None
    _handler_providers: Dict[Type, Callable] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomMediator, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register_handler(cls, command_type: Type, handler_provider: Callable):
        """Register a handler provider for a command type"""
        cls._handler_providers[command_type] = handler_provider

    async def send(self, command):
        """Send a command to its registered handler"""
        handler_provider = self._handler_providers.get(type(command))
        if not handler_provider:
            raise ValueError(f"No handler registered for command {type(command)}")
        
        # Get handler instance from the provider and handle the command
        handler = handler_provider()
        return await handler.handle(command)

# Create a singleton instance
mediator = CustomMediator() 