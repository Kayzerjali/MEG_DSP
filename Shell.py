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

    def onecmd(self, line):
        """
        Runs one command, reporting any unexpected error instead of propagating it.

        The shell runs in its own thread (see dsp.py). An exception escaping a do_*
        method would escape cmdloop() and kill that thread, which leaves the graphs
        running but the prompt dead and unable to accept anything. Catching here keeps
        the prompt alive whatever a single command does.
        """
        try:
            return super().onecmd(line)
        except Exception as e:
            print(f"Command failed: {e}")
            print("(The prompt is still running, you can keep typing.)")
            return False


    def do_axis(self, arg):
        """
        Changes the data source axis being read.
        'mag' combines all three axes into a single overall field strength.
        Usage: axis x|y|z|mag
        Example: axis x
        """

        if arg in ["x", "y", "z", "mag"]:
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
        Frequencies are in Hz. Order controls the steepness of the cutoff.

        You must run 'add_filt bp' before using this command.

        Usage: bp_filt lowcut highcut order
        Example: bp_filt 50 250 5

        """
        try:
            # get_instance raises if bp has never been added, it does not return None
            bp_filter = self._container.get_instance("bp")
        except Exception:
            bp_filter = None

        if bp_filter is None:
            print("Bandpass filter not initialized. Use 'add_filt bp' to add it first.")
            return

        if len(arg.split()) == 3:
            try:
                lowcut, highcut, order = arg.split()

                bp_filter.change_filt_coeffs(float(lowcut), float(highcut), int(order))

            except Exception as e:
                print(f"Error changing filter coefficients: {e}")
        else:
            print("Invalid arguments")                
                

    def do_remove_filt(self, arg):
        """
        Removes a filter from the filter manager. Use 'all' to remove all filters.
        Usage: remove_filt filter_name
        Example: remove_filt bp
                 remove_filt all
        """
        try:
            filter_manager: Filter.FilterManager = self._container.get_instance("filter_manager")
            filter_manager.remove_filter(arg)


            print(f"Filter {arg} removed.")
        except Exception as e:
            print(f"Error removing filter: {e}")


    def do_list_current_filters(self, arg):
        """
        Lists the filters that are switched on right now, in the order they are applied.
        Usage: list_current_filters
        Example: list_current_filters
        Output:
        Currently applied filters:
        - notch
        - bp
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
        Lists every filter you are allowed to add with 'add_filt'.
        Usage: list_registered_filters
        Example: list_registered_filters
        Output:
        Available filters:
        - bp
        - notch
        - pca
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
    


    def do_add_filt(self, arg):
        """
        Adds a filter to the filter manager. Filter must be registered in the container.
        To see available filters use 'list_registered_filters'.
        Filters are applied in the order you add them.
        Usage: add_filt filter_name
        Example: add_filt notch
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

        *** NOT IMPLEMENTED ***
        Saving the animation to a video file was never finished, so this command
        reports that and does nothing. To save a picture of the graphs, use the save
        icon in the graph window toolbar.

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
            start_recording = getattr(display_manager, "start_recording", None)
            if start_recording is None:
                self._print_recording_unimplemented()
                return
            start_recording(filename)
        elif command == "stop":
            stop_recording = getattr(display_manager, "stop_recording", None)
            if stop_recording is None:
                self._print_recording_unimplemented()
                return
            stop_recording()
        else:
            print("Unknown command. Use 'start' or 'stop'.")

    def _print_recording_unimplemented(self):
        print("Recording is not implemented in this version, so nothing was recorded.")
        print("To save a picture of the graphs, use the save icon in the graph window toolbar.")
    
    def do_set_axis_limits(self, arg):
        """
        Sets the y-axis limits for a specific subplot, stopping it from auto-rescaling.
        Counting starts at zero: row 0 is the raw (top) row, row 1 is the filtered
        (bottom) row; columns are 0, 1, 2 from left to right.
        Do not put a space inside the brackets.
        Usage: set_axis_limits (row,col) ymin ymax
        Example: set_axis_limits (1,0) -2000 2000
        """
        args = arg.split()
        if len(args) != 3:
            print("Invalid arguments! Usage: set_axis_limits (row, col) ymin ymax")
            print(f"Expected 3 arguments, got {len(args)}")
            return

        try:
            row, col = map(int, args[0][1:-1].split(","))
            ymin = float(args[1])
            ymax = float(args[2])
            display_manager: Display.DisplayManager = self._container.get_instance("display_manager")
            if display_manager.set_axis_limits((row, col), (ymin, ymax)):
                print(f"Y-axis limits set to [{ymin}, {ymax}] for subplot ({row}, {col})")
        except ValueError:
            print("Invalid limits. Please provide numeric values.")
        except Exception as e:
            print(f"Error setting axis limits: {e}")

    def do_set_auto_scale(self, arg):
        """
        Undoes set_axis_limits, letting a subplot rescale itself again.
        Counting starts at zero, as for set_axis_limits.
        Do not put a space inside the brackets.

        Usage: set_auto_scale (row,col)
        Example: set_auto_scale (1,0)
        """
        args = arg.split()
        if len(args) != 1:
            print("Invalid arguments! Usage: set_auto_scale (row, col)")
            return
        try:
            row, col = map(int, args[0][1:-1].split(","))
            display_manager: Display.DisplayManager = self._container.get_instance("display_manager")
            if display_manager.set_auto_scale((row, col)):
                print(f"Y-axis auto-scaling enabled for subplot ({row}, {col})")
        except Exception as e:
            print(f"Error setting auto scale: {e}")
        


    def do_quit(self, arg):
        """
        Closes the program and shuts down the data source cleanly.
        Usage: quit
        Example: quit
        """
        return True
    
