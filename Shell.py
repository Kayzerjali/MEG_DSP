from cmd import Cmd
from Container import Container
import Display
import Filter



class DSPShell(Cmd):
    intro = "Welcome to the MEG DSP Shell. Type help or ? to list commands.\n" # printed to shell
    prompt = "dsp: " # prompt symbol at each line of shell

    def __init__(self, container: Container):
        super().__init__()
        self._container = container
    
    def do_axis(self, arg):
        """
        Changes the data source axis being read.
        Usage: axis x|y|z
        Example: axis x
        """

        if arg in ["x", "y", "z"]:
            try:
                # Change data source
                self._container.get_instance("data_source").set_axis(arg)

                # change graph titles
                self._container.get_instance("display_manager").change_title_axes(arg)

            except Exception as e:
                print(f"Error changing axis: {e}")
                
        else:
            print("Invalid axis")



    def do_bp_filt(self, arg):
        """
        Changes the characteristics (lowcut, highcut, order) of the bandpass filter.
        Usage: bp_filt lowcut highcut order
        Example: bp_filt 50 250 5
    
        """
        if self._container.get_instance("bp_filt") is None:
            print("Bandpass filter not initialized. Use 'add_filter bp_filt' to add it first.")
            return

        if len(arg.split()) == 3:
            try:
                lowcut, highcut, order = arg.split()

                self._container.get_instance("bp_filt").change_filt_coeffs(float(lowcut), float(highcut), int(order))

            except Exception as e:
                print(f"Error changing filter coefficients: {e}")
        else:
            print("Invalid arguments")                
                

    def do_remove_filter(self, arg):
        """
        Removes a filter from the filter manager.
        Usage: remove_filter filter_name
        Example: remove_filter bp_filt
        """
        try:
            filter_manager: Filter.FilterManager = self._container.get_instance("filter_manager")
            filter_manager.remove_filter(arg)


            print(f"Filter {arg} removed.")
        except Exception as e:
            print(f"Error removing filter: {e}")


    def do_list_current_filters(self, arg):
        """
        Lists all currently applied filters in the filter manager.
        Usage: list_filters
        Example: list_filters
        Output:
        Currently applied filters:
        - bp_filt
        - pca_filt
        """
        try:
            filter_manager = self._container.get_instance("filter_manager")
            filters: list[str] = filter_manager.list_filters()
            if filters:
                print("Currently applied filters:")
                for f in filters:
                    print(f"- {f}")
            else:
                print("No filters currently applied.")

        except Exception as e:
            print(f"Error retrieving filters: {e}")


    def do_list_registered_filters(self, arg):
        """
        Lists all available filters in the container.
        Usage: list_registered_filters
        Example: list_registered_filters
        Output:
        Available filters:
        - bp_filt
        - pca_filt
        """
        try:
            filters: list[str] = self._container.list_registered_filters()
            if filters:
                print("Available filters:")
                for f in filters:
                    print(f"- {f}")
            else:
                print("No filters available.")
        except Exception as e:
            print(f"Error retrieving available filters: {e}")
    


    def do_add_filter(self, arg):
        """
        Adds a filter to the filter manager. Filter must be registered in the container. To see available filters use 'list_filters'.
        Usage: add_filter filter_name
        Example: add_filter bp_filt
        """
        try:
            filter_manager: Filter.FilterManager = self._container.get_instance("filter_manager")
            filter_instance = self._container.resolve(arg)
            filter_manager.add_filter(arg, filter_instance)

            print(f"Filter {arg} added.")
        except Exception as e:
            print(f"Error adding filter: {e}")

    def do_recording(self, arg):
        """
        Controls the recording of the animation.
        Usage: recording start [filename] | stop
        Example: recording start my_signal.mp4
                 recording stop
        """
        args = arg.split()
        if not args:
            print("Usage: recording start [filename] | stop")
            return

        command = args[0].lower()
        display_manager = self._container.get_instance("display_manager")

        if command == "start":
            filename = args[1] if len(args) > 1 else "recording.mp4"
            display_manager.start_recording(filename)
        elif command == "stop":
            display_manager.stop_recording()
        else:
            print("Unknown command. Use 'start' or 'stop'.")

    def do_quit(self, arg):
        return True
    
