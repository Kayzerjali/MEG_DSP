import DataSource
import Filter
import Display
import Shell
import itertools
import matplotlib.pyplot as plt
import threading
from Container import Container



def create_master_stream(raw_stream, filt_stream):
    """
    Converts the streams into a single stream of the form ([[ch1_raw],[ch2_raw]], [[ch1_filt],[ch2_filt]]).
    Zip create tuples where the first element is first element from first array with first element of second.
    This takes the first object of raw which is [[ch1_raw],[ch2_raw]] and places it in a tuple with [[ch1_filt],[ch2_filt]]
    giving ([[ch1_raw],[ch2_raw]], [[ch1_filt],[ch2_filt]])
    
    :param raw_stream: Description
    :param filt_stream: Description
    """
    for raw, filt in zip(raw_stream, filt_stream):
        yield (raw, filt)


def main():

    try:
        # Register all objects
        container = Container()
        container.register("data_source", lambda: DataSource.MockSignal(), singleton=True)
        container.register("bp_filt", lambda: Filter.BandPass())
        container.register("pca_filt", lambda: Filter.PCA())

        # Resolve objects (get instances)
        data_source = container.resolve("data_source")
        bp_filt = container.resolve("bp_filt")
        pca_filt = container.resolve("pca_filt")


        # Create data stream
        raw_data_stream = data_source.data_stream()
        raw_stream, stream_to_filter = itertools.tee(raw_data_stream) # create 2 streams, one to keep one to filter

        bp_filt_stream = bp_filt.filter(stream_to_filter)
        master_stream = create_master_stream(raw_stream, bp_filt_stream)

        # Register Display Manager
        container.register("display_manager", lambda: Display.DisplayManager(master_stream))
        display_manager = container.resolve("display_manager")


        # Start CLI in seperate thread
        shell = Shell.DSPShell() # DSPShell should take all registered objects to improve extendability
        threading.Thread(target=shell.cmdloop, daemon=True).start()

        # Show Displays
        plt.show() # call is blocking

    
    except (KeyboardInterrupt, SystemExit): # Ctrl + C in terminal 
        print("Keyboard Interrupt")
        # data_source.close()
        print("NIDAQ Task Closed")
        return
    
    finally:
        # data_source.close()
        print("NIDAQ Task Closed")
        return


if __name__ == "__main__":

    main()
