from typing import Any, Callable
from DataSource import DataSource as DS, MockSignal as MS
from Filter import Filter as F, FilterManager as FM
from Display import DynamicDisplay as DD, DisplayManager as DM


class Container():
    """
    This container keeps track of all the providers (the objects that provide instances) used.  
    """
    def __init__(self):
        
        # maps the provider name to a tuple containing the provider init and the bool which indicates if provider is singlton, i.e. there should only be one instance 
        self._providers: dict[str, Callable[..., Any]] = {}
        self._instances: dict[str, Any] = {}


        self._filters: dict[str, Callable[[], F]] = {}
        self._displays: dict[str, Callable[..., DD]] = {}
    
    def register(self, name: str, provider: Callable[[], Any]) -> None: # register a provider (class) to a name to be stored in container
        self._providers[name] = (provider) # add the provider to the dict under the name
    
    def register_filter(self, name: str, provider: Callable[[], F]) -> None:
        self._filters[name] = (provider) # add the provider to the dict under the name
        self._providers[name] = (provider) # also add to providers for resolution
    
    def list_registered_filters(self) -> list[str]:
        return list(self._filters.keys())

    def register_display(self, title: str, provider: Callable[..., DD]) -> None:
        """
        Docstring for register_display
        
        :param title: Title of the display, used for identification and display purposes. Must have format "<Base Title> : X Axis" where X is the name axis
        :type title: str
        :param provider: A callable that returns an instance of a display when called. The provider should take a title argument to set the title of the display it creates.
        :type provider: Callable[..., DD]
        """

        self._displays[title] = (provider) # add the display to the dict of displays
        self._providers[title] = (provider) # add the provider to the dict under the name


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

            data_source: DS = self.resolve("data_source")

        except Exception as e: # if cannot resolve data source fallback on Mock Signal
            print(f"Warning: Could not initialize NIDAQ ({e}).")
            print("Switching to MockSignal for simulation.")

            # Re-register data_source as MockSignal
            self.register("data_source", lambda: MS())
            data_source: DS = self.resolve("data_source")

        
        # resolve Filter Manager
        filter_manager: FM  = self.resolve("filter_manager")

        # resolve Display Manager
        display_manager: DM = self.resolve("display_manager")

        # populate Filter Manager with raw stream
        filter_manager.add_raw_stream(data_source.data_stream())

        master_stream = filter_manager.transform()

        # populate Display Manager with displays and master stream
        for title, provider in self._displays.items():
            display: DD = provider(title = title)
            display_manager.add_plot(display)
        

        display_manager.add_master_stream(master_stream)

        display_manager.start()

        