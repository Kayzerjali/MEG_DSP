## How to use
Navigate to folder which this environment is stored in a CLI. dsp.py is the application entry point so run "python dsp.py". Graphs will appear and real time configuration is available through the terminal. 
There are no filters applied initally. Use add_filter 'filter name' to add filters, use list_filters to list available filters

## Extending
When adding new classes such as new data sources, filters (SSP, SSS) or displays ensure they satisfy the interface specified by the parent classes and that they are children of the relevant parent.
All providers (classes that provide an instane to use) must be registered in the container. This allow us to keep track of instances which is particularly helpful for DSPShell which modifies the instances at runtime.
When registering a Filter use the register_filter() method and when registering a display use the register_display() method.

To add commands to the custom CLI in DSPShell, prefix the command name with do_ as seen in the class. In the CLI, whatever is typed after the command is passed as a string to the arg parameter. You can access this in the your do_ function.

### Recommended Extensions
1) Be able to add and remove display at runtime similar to the filters
2) implement SSP and SSS
3) Allow to choose different axes such as x from sensor 1 and y from sensor 2 to get better correlated data
4) use PCA on all 6 channels
5) Implement more data visualistion displays similar to PrincipleComponentDomain to better understand the correlations or the efficacy of certaining filtering. For example plotting the proportion of the signal PC1 represents using diagonstic functions from the sk-learn library 



## Dependancies
1) scikit-learn : "pip install scikit-learn"



