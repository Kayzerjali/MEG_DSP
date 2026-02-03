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

    def do_list_filters(self, arg):
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


    def do_quit(self, arg):
        return True
    
