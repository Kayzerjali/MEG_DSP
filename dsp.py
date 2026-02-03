import DataSource
import Filter
import Display
import Shell
import matplotlib.pyplot as plt
import threading
from Container import Container



def main():

    try:
        """ Register all objects in container """

        container = Container()
        container.register("data_source", lambda: DataSource.NIDAQ())

        # Register Filters
        container.register_filter("bp_filt", lambda: Filter.BandPass())
        container.register_filter("pca_filt", lambda: Filter.PCA())

        # Register Managers
        container.register("filter_manager", lambda: Filter.FilterManager())
        
        container.register("display_manager", lambda: Display.DisplayManager())
        

        """ Resolve objects and run pipeline """

        container.run()


        # Start CLI in seperate thread
        shell = Shell.DSPShell(container) # DSPShell takes container to access all providersf

        threading.Thread(target=shell.cmdloop, daemon=True).start()

        # Show Displays
        plt.show() # call is blocking

    
    except (KeyboardInterrupt, SystemExit): # Ctrl + C in terminal 

        print("Keyboard Interrupt")
    
    finally:

        try:
            container.get_instance("data_source").close()
            print("NIDAQ Task Closed")

        except Exception:
            pass


if __name__ == "__main__":

    main()
