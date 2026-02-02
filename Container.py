from typing import Any, Callable
class Container():
    """
    This container keeps track of all the providers (the objects that provide instances) used.  
    """
    def __init__(self):
        
        # maps the provider name to a tuple containing the provider init and the bool which indicates if provider is singlton, i.e. there should only be one instance 
        self._providers: dict[str, tuple[Callable[[], Any], bool]] = {}
        self._singletons: dict[str, Any] = {}
        self._instances: dict[str, Any] = {}
    
    def register(self, name: str, provider: Callable[[], Any], singleton: bool = False) -> None:
        self._providers[name] = (provider, singleton) # add the provider to the dict under the name
    
    def resolve(self, name: str) -> Any:
        # if name is a signleton and already have one therefore can return it
        if name in self._singletons:
            return self._singletons[name]
         
        if name not in self._providers: # provider to create instance has not been registered
            raise ValueError(f"Provider {name} not registered")
        
        # At this point we know there exists provider for name
        provider, singleton = self._providers[name] # retrive provider from dict
        instance = provider()
        self._instances[name] = instance # add instance to dict

        if singleton:
            self._singletons[name] = instance
        
        return instance
    
    def get_instance(self, name: str) -> Any:
        if name in self._instances:
            return self._instances[name]
        
        else:
            raise ValueError(f"Instance for {name} not found, try resolving it first.")