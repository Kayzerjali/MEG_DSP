from typing import Any, Callable
import DataSource
import Filter
import Display


class Container():
    """
    This container keeps track of all the providers (the objects that provide instances) used.  
    """
    def __init__(self):
        
        # maps the provider name to a tuple containing the provider init and the bool which indicates if provider is singlton, i.e. there should only be one instance 
        self._providers: dict[str, Callable[[], Any]] = {}
        self._instances: dict[str, Any] = {}
        self._filters: dict[str, Callable[[], Any]] = {}
    
    def register(self, name: str, provider: Callable[[], Any]) -> None:
        self._providers[name] = (provider) # add the provider to the dict under the name
    
    def register_filter(self, name: str, provider: Callable[[], Any]) -> None:
        self._filters[name] = (provider) # add the provider to the dict under the name
        self._providers[name] = (provider) # also add to providers for resolution
    
    def resolve(self, name: str) -> Any:
    
        if name not in self._providers: # provider to create instance has not been registered
            raise ValueError(f"Provider {name} not registered")
        
        # At this point we know there exists provider for name
        provider = self._providers[name] # retrive provider from dict
        instance = provider()
        self._instances[name] = instance # add instance to dict

        return instance
    
    def get_instance(self, name: str) -> Any:
        if name in self._instances:
            return self._instances[name]
        
        else:
            raise ValueError(f"Instance for {name} not found, try resolving it first.")
    
    def run(self):
        """
        Run executes the pipeline for the project.
        In main populate the container (in order) with:
        "data_source"
        <filters>
        "filter_manager"
        "display_manager"
        It resolves a DataSource, FilterManager and DisplayManager.
        """

        """ Resolve objects (get instances) """

        # try resolve data source, default to mock source if fails
        try:

            data_source: DataSource.DataSource = self.resolve("data_source")

        except Exception as e: # if cannot resolve data source fallback on Mock Signal
            print(f"Warning: Could not initialize NIDAQ ({e}).")
            print("Switching to MockSignal for simulation.")

            # Re-register data_source as MockSignal
            self.register("data_source", lambda: DataSource.MockSignal())
            data_source = self.resolve("data_source")

        
        # resolve Filter Manager
        filter_manager: Filter.FilterManager  = self.resolve("filter_manager")

        # resolve Display Manager
        display_manager: Display.DisplayManager = self.resolve("display_manager")

        # populate Filter Manager with raw stream and filters
        filter_manager.add_raw_stream(data_source.data_stream())

        for filter_name in self._filters:
            filter_instance = self.resolve(filter_name)
            filter_manager.add_filter(filter_name, filter_instance)

        master_stream = filter_manager.transform()

        # populate Display Manager with master stream
        display_manager.add_master_stream(master_stream)

        display_manager.start()

        