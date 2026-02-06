import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from collections import deque
import numpy as np
from typing import Literal





class DynamicDisplay():
    """
    Base class for different types of dynamic displays (e.g. time domain, frequency domain, PCA).
    Each display type will have its own logic for how to update the plot based on incoming data, but they will all share a common interface for updating the plot and changing the title axis.
    Implementations of this class should implement the update() method which takes in new data and updates the plot accordingly.

    The update_title_axis() method which changes the title of the plot to reflect the current axis being displayed.
    """

    def __init__(self):
        """

        :param data_generator: A data generator
        :param x_axis: If the x-axis is none will use regular time intervals, if specified (usually for fft displays) it will be used
        """
        self.lines = []

    def update(self, data):
        raise NotImplementedError
    
    def add_axis(self, ax):
        raise NotImplementedError

    def update_title_axis(self, axis):
        raise NotImplementedError

    def set_blitting(self, blitting: bool):
        raise NotImplementedError
       

class TimeDomain(DynamicDisplay):
    """
    Gets passed an ax object corresponding to a subplot from DisplayManger which this class manages. 
    This class create the plot for the ax and manages the lines by updating them in _update().
    _update() is called by DisplayManager 
    """

    def __init__(self, num_channels=2, sample_rate=1000, time_window=1.0, title="", blitting: bool = False):

        self.num_channels = num_channels
        self.num_points = int(sample_rate * time_window)
        self.deque_list = [deque(np.zeros(self.num_points), maxlen=self.num_points) for _ in range(num_channels)]
        self.title = title # ensure title has format "base title : X Axis"
        self.blitting = blitting


        self.t = np.arange(-self.num_points + 1, 1) / sample_rate
        

    def update(self, data):
        if data is None: return self.lines

        num_incoming_channels = data.shape[0]
        num_samples_in_chunk = data.shape[1] if num_incoming_channels > 0 else 0

        for i, line in enumerate(self.lines):
            if i < num_incoming_channels:
                # We have data for this channel, extend the deque
                self.deque_list[i].extend(data[i])
            else:
                # This channel is missing from the data, pad with zeros
                self.deque_list[i].extend(np.zeros(num_samples_in_chunk))

            line.set_ydata(self.deque_list[i])
        
        if not self.blitting:
            self.ax.relim()
            self.ax.autoscale_view(scalex=False, scaley=self.ax.get_autoscaley_on()) # the get_autoscaley_on() is a flag set false when ylim is set manually
            
        return self.lines

    def update_title_axis(self, axis):
        base_title, _ = self.title.split(" : ")
        self.ax.set_title(f"{base_title} : {axis.upper()} Axis")

    def set_blitting(self, blitting: bool):
        self.blitting = blitting
    
    def add_axis(self, ax):
        self.ax = ax
        self.lines = [self.ax.plot(self.t, np.zeros(self.num_points), label=f"Ch {i+1}")[0] for i in range(self.num_channels)]
        
        self.ax.set_title(self.title)
        if self.blitting:
            self.ax.set_ylim(-8000, 8000) # Required for efficient blitting
        self.ax.grid(True)



class FrequencyDomain(DynamicDisplay):
    """
    Helper class for DisplayManager.
    Gets passed an ax object corresponding to a subplot from DisplayManger which this class manages. 
    This class create the plot for the ax and manages the lines by updating them in _update().
    _update() is called by DisplayManager 

    """
    def __init__(self, num_channels=2, sample_rate=1000, time_window=5.0, title="", blitting: bool = False):

        # display initalised without axis as axis s provided by display manager which calls add_axis()
        self.num_points = int(sample_rate * time_window)
        self.freq_domain = np.fft.rfftfreq(self.num_points, 1/sample_rate)
        self.time_deques = [deque(np.zeros(self.num_points), maxlen=self.num_points) for _ in range(num_channels)]
        self.title = title # ensure title has format "base title : X Axis"
        self.blitting = blitting
     
    
    def add_axis(self, ax):
        self.ax = ax
        self.lines = [self.ax.plot(self.freq_domain, np.zeros(self.freq_domain.size), label=f"Ch {i+1}")[0] for i in range(len(self.time_deques))]
        self.ax.set_title(self.title)
        if self.blitting:
            self.ax.set_ylim(0, 2000) # Required for efficient blitting
        self.ax.grid(True)
    


    def update(self, data):
        if data is None: return self.lines

        num_incoming_channels = data.shape[0]
        num_samples_in_chunk = data.shape[1] if num_incoming_channels > 0 else 0

        for i in range(len(self.lines)):
            if i < num_incoming_channels:
                # We have data for this channel, extend the deque
                self.time_deques[i].extend(data[i])
            else:
                # This channel is missing, pad with zeros to keep FFT stable
                self.time_deques[i].extend(np.zeros(num_samples_in_chunk))
        
        y_fft = np.abs(np.fft.rfft(np.array(self.time_deques), axis=1)) / self.num_points
        y_fft[:, 0] = 0 # DC offset removal
        y_fft[:, 1:] *= 2 
        
        for i, line in enumerate(self.lines):
            line.set_ydata(y_fft[i])
            
        if not self.blitting:
            self.ax.relim()
            self.ax.autoscale_view(scalex=True, scaley=self.ax.get_autoscaley_on())
            
        return self.lines

    def update_title_axis(self, axis):
        base_title, _ = self.title.split(" : ")
        self.ax.set_title(f"{base_title} : {axis.upper()} Axis")

    def set_blitting(self, blitting: bool):
        self.blitting = blitting


class PrincipleComponentDomain(DynamicDisplay):
    """
    A plot that shows sensor 1 values on the x-axis and sensor 2 values on the y-axis.
    Useful for visualizing correlations between two sensors.
    """

    def __init__(self, ax: plt.Axes = None, title="", num_points: int = 1000, blitting: bool = False): # type: ignore

        self.ax = ax
        self.title = title
        self.num_points = num_points
        self.blitting = blitting
        

        self.ch1_deque = deque((np.zeros(self.num_points)), maxlen=self.num_points)
        self.ch2_deque = deque((np.zeros(self.num_points)), maxlen=self.num_points)

    
    def update(self, data):
        if data is None: return self.lines
        if data.shape[0] < 2: return self.lines

        self.ch1_deque.extend(data[0])
        self.ch2_deque.extend(data[1])
        self.lines[0].set_xdata(self.ch1_deque)
        self.lines[0].set_ydata(self.ch2_deque)

        if not self.blitting:
            self.ax.relim()
            self.ax.autoscale_view(scalex=True, scaley=self.ax.get_autoscaley_on())
            
        return self.lines

    def update_title_axis(self, axis):
        base_title, _ = self.title.split(" : ")
        self.ax.set_title(f"{base_title} : {axis.upper()} Axis")
    
    def add_axis(self, ax):
        self.ax = ax 

        self.lines = [self.ax.plot(np.zeros(self.num_points), np.zeros(self.num_points), label="PCA", marker="o", linestyle="")[0]]
        self.ax.set_title(self.title)

        if self.blitting:
            self.ax.set_xlim(-8000, 8000)
            self.ax.set_ylim(-8000, 8000)

        self.ax.grid(True)
    

    def set_blitting(self, blitting: bool):
        self.blitting = blitting

class DisplayManager():
    """
    Takes a data generator which yields tuples of (raw_data, filtered_data) and displays them in a 2x2 grid of plots.
    Before calling start(), use add_master_stream() to set the data generator.

    """
    def __init__(self, blitting: bool = False):
        self.blitting = blitting
        self.data_generator = None
        self.plots: list[DynamicDisplay] = []
        self.plot_info: list[tuple[DynamicDisplay, tuple[int, int]]] = []

        
    def add_master_stream(self, data_generator):
        self.data_generator = data_generator
    
    def set_blitting(self, blitting: bool):
        self.blitting = blitting

    def add_plot(self, plot: DynamicDisplay, row: int = 0, col: int = 0):
        self.plot_info.append((plot, (row, col)))
        self.plots.append(plot)



    def start(self):

        if self.data_generator is None:
            raise ValueError("Data generator not set. Use add_master_stream() to set it before starting the display.")
        
        
        num_plots = len(self.plots)
        
        # Calculate grid size automatically (2 rows, N columns)
        rows = 2
        cols = max(1, num_plots // rows)

        self.fig, self.axes = plt.subplots(rows, cols, figsize=(12, 8)) # creates subplot grid based on number of plots, assumes even number of plots for simplicity and 2 rows (raw, filtered)
        
        # Ensure axes is always addressable as 2D array even if 1x1 or 1xN
        if num_plots == 1: self.axes = np.array([[self.axes]])
        elif rows == 1 or cols == 1: self.axes = self.axes.reshape(rows, cols)

        # add the axes to the corresponding plot objects
        for i, plot in enumerate(self.plots):
            # Automatically assign axis based on order of addition: Row 0 then Row 1
            r = i // cols
            c = i % cols
            if r < rows and c < cols:
                plot.add_axis(self.axes[r, c])
                
            # Sync blitting setting
            
            plot.set_blitting(self.blitting)


        # Initialize the sub-managers with specific axes
        # self.plots: list[DynamicDisplay] = [
        #     TimeDomain(self.axes[0, 0], title="Raw Time Domain : X Axis", blitting=self.blitting),
        #     FrequencyDomain(self.axes[0, 1], title="Raw Frequency Domain : X Axis", blitting=self.blitting),
        #     PrincipleComponentDomain(self.axes[0, 2], title="Raw PCA : X Axis", blitting=self.blitting),

        #     TimeDomain(self.axes[1, 0], title="Filtered Time Domain : X Axis", blitting=self.blitting),
        #     FrequencyDomain(self.axes[1, 1], title="Filtered Frequency Domain : X Axis", blitting=self.blitting),
        #     PrincipleComponentDomain(self.axes[1, 2], title="Filtered PCA : X Axis", blitting=self.blitting),
        # ]
        
        self.fig.tight_layout()
        
        # ONE animation for all 4 plots
        self.anim = FuncAnimation(self.fig, self._main_update, frames=self.data_generator, 
                                  interval=50, blit=self.blitting, cache_frame_data=False)



    def _main_update(self, frame):
        if frame is None: return [line for p in self.plots for line in p.lines]
        
        raw_data, filt_data = frame # We expect the generator to yield a tuple
        
        # Update each plot logic
        all_lines = []
        
        # Dynamically update plots based on the number of registered displays
        # Assumes the first half are Raw (use raw_data) and the second half are Filtered (use filt_data)
        midpoint = len(self.plots) // 2
        for i, plot in enumerate(self.plots):
            data_source = raw_data if i < midpoint else filt_data
            all_lines.extend(plot.update(data_source))
        
        return all_lines
    
    def change_title_axes(self, axis: Literal["x", "y", "z", "mag"]):
        
        for plot in self.plots:
            plot.update_title_axis(axis)
            
        self.fig.canvas.draw_idle() # to force a redraw dispite blitting

    def set_axis_limits(self, plot: tuple[int, int], limits: tuple[float, float]):
        """
        Sets the y-axis limits for a specific plot.
        :param plot: tuple of (row, col) indices for the subplot
        :param limits: (ymin, ymax)
        """
        row, col = plot
        if 0 <= row <= 2 and 0 <= col <= 2:
            ax = self.axes[row, col]
            try:
                ax.set_ylim(limits)
                self.fig.canvas.draw_idle()
            except Exception as e:
                print(f"Error setting axis limits: {e}")
        else:
            print(f"Invalid plot index: {plot}")
    
    def set_auto_scale(self, plot: tuple[int, int]):
        """
        Sets the y-axis to auto-scale for a specific plot.
        :param plot: tuple of (row, col) indices for the subplot
        """
        row, col = plot
        if 0 <= row < 2 and 0 <= col < 2:
            ax = self.axes[row, col]
            ax.set_autoscaley_on(True)
            self.fig.canvas.draw_idle()
        else:
            print(f"Invalid plot index: {plot}")