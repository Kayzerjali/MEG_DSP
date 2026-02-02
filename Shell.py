from cmd import Cmd
from Container import Container



class DSPShell(Cmd):
    intro = "Welcome to the MEG DSP Shell. Type help or ? to list commands.\n" # printed to shell
    prompt = "dsp: " # prompt symbol at each line of shell

    def __init__(self, container: Container):
        super().__init__()
        self._container = container
    
    def do_axis(self, arg):

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
                


    def do_quit(self, arg):
        return True
    

