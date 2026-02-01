import DataSource
import Filter
import Display
import Shell
import itertools
import matplotlib.pyplot as plt
import threading




def main():

    try:
        # Initialise Data Source
        data_source = DataSource.MockSignal()

        # Initialise Filters
        bp_filt = Filter.BandPass()
        pca_filt = Filter.PCA()

        # Create raw data stream
        data_stream = DataSource.ThreadedGenerator(data_source.data_stream()) # mock signal is seperate thread to avoid sleeping main

        # Create filtered data stream
        raw_stream, stream_to_filter = itertools.tee(data_stream) # create 2 streams, use one to filter and reserve 1 to display raw

        bp_filt_stream = bp_filt.filter(stream_to_filter)
        # pca_filt_stream = pca_filt.filter(bp_filt_stream)


        # Create Displays
        # raw
        raw_time_stream, raw_freq_stream = itertools.tee(raw_stream)
        raw_time_display = Display.TimeDomain(raw_time_stream, title="Raw Data", blited=True)
        raw_freq_display = Display.FrequencyDomain(raw_freq_stream, title="Raw Data", blited=True)

        # filtered
        filt_time_stream, filt_freq_stream = itertools.tee(bp_filt_stream)
        filt_time_display = Display.TimeDomain(filt_time_stream, title="Filtered Data", blited=True)
        filt_freq_display = Display.FrequencyDomain(filt_freq_stream, title="Filtered Data", blited=True)

        


        # Start CLI in seperate thread
        shell = Shell.DSPShell() # DSPShell should take all registered objects to improve extendability
        threading.Thread(target=shell.cmdloop, daemon=True).start()

        # Show Displays
        plt.show() # call is blocking

    
    except (KeyboardInterrupt, SystemExit): # Ctrl + C in terminal 
        print("Keyboard Interrupt")
        data_source.close()
        print("NIDAQ Task Closed")
    
    finally:
        data_source.close()
        print("NIDAQ Task Closed")


if __name__ == "__main__":

    main()
