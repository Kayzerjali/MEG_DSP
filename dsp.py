import DataSource
import Filter
import Display
import Shell
import matplotlib.pyplot as plt
import threading
from Container import Container
import traceback



def main():

    try:
        # Register all objects in container

        container = Container()
        container.register("data_source", lambda: DataSource.NIDAQ())

        # Register Filters
        container.register_filter("bp", lambda: Filter.BandPass())
        container.register_filter("notch", lambda: Filter.Notch())
        container.register_filter("pca", lambda: Filter.PCA())
        container.register_filter("diff", lambda: Filter.Differential())
        container.register_filter("ipca", lambda: Filter.IncrementalPCA())
        container.register_filter("kpca", lambda: Filter.KPCA())
        container.register_filter("spca", lambda: Filter.SPCA())

        # Register Displays
        # Row 1: Raw Data
        container.register_display("Raw Time Domain : X Axis", lambda title: Display.TimeDomain(title=title))
        container.register_display("Raw Frequency Domain : X Axis", lambda title: Display.FrequencyDomain(title=title))
        container.register_display("Raw PCA : X Axis", lambda title: Display.PrincipleComponentDomain(title=title))
        
        # Row 2: Filtered Data
        container.register_display("Filtered Time Domain : X Axis", lambda title: Display.TimeDomain(title=title))
        container.register_display("Filtered Frequency Domain : X Axis", lambda title: Display.FrequencyDomain(title=title))
        container.register_display("Filtered PCA : X Axis", lambda title: Display.PrincipleComponentDomain(title=title))

        # Register Managers

        container.register("filter_manager", lambda: Filter.FilterManager())
        container.register("display_manager", lambda: Display.DisplayManager())
        

        # Resolve objects and run pipeline with run()

        container.run()


        # Start CLI in seperate thread
        shell = Shell.DSPShell(container) # DSPShell takes container to access all providersf

        threading.Thread(target=shell.cmdloop, daemon=True).start()

        # Show Displays
        plt.show() # call is blocking

    
    except (KeyboardInterrupt, SystemExit): # Ctrl + C in terminal 

        print("Keyboard Interrupt")

    except Exception:
        print("An unexpected error occurred:")
        traceback.print_exc()

    
    finally:

        try:
            plt.close('all')
            # Safely attempt to close the data source
            ds = container.get_instance("data_source")
            if ds:
                ds.close()
                print("Data Source Closed")

        except Exception:
            pass


if __name__ == "__main__":

    main()
