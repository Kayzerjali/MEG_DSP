import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from collections import deque
import numpy as np
from typing import Literal






class DynamicDisplay():

    def __init__(self):
        """

        :param data_generator: A data generator
        :param x_axis: If the x-axis is none will use regular time intervals, if specified (usually for fft displays) it will be used
        """
       

class TimeDomain(DynamicDisplay):
    """
    Helper class for DisplayManager.
    Gets passed an ax object corresponding to a subplot from DisplayManger which this class manages. 
    This class create the plot for the ax and manages the lines by updating them in _update().
    _update() is called by DisplayManager 
    """
    def __init__(self, ax, num_channels=2, sample_rate=1000, time_window=1.0, title="", blitting: bool = True):
        self.ax = ax
        self.num_points = int(sample_rate * time_window)
        self.deque_list = [deque(np.zeros(self.num_points), maxlen=self.num_points) for _ in range(num_channels)]
        self.title = title # ensure title has format "base title : X Axis"
        self.blitting = blitting


        t = np.arange(-self.num_points + 1, 1) / sample_rate
        self.lines = [self.ax.plot(t, np.zeros(self.num_points), label=f"Ch {i+1}")[0] for i in range(num_channels)]
        
        self.ax.set_title(title)
        if self.blitting:
            self.ax.set_ylim(-8000, 8000) # Required for efficient blitting
        self.ax.grid(True)

    def update(self, data):
        if data is None: return self.lines
        for i, line in enumerate(self.lines):
            self.deque_list[i].extend(data[i])
            line.set_ydata(self.deque_list[i])
        
        if not self.blitting:
            self.ax.relim()
            self.ax.autoscale_view(scalex=False, scaley=True)
            
        return self.lines

    def update_title_axis(self, axis):
        base_title, _ = self.title.split(" : ")
        self.ax.set_title(f"{base_title} : {axis.upper()} Axis")


class FrequencyDomain(DynamicDisplay):
    """
    Helper class for DisplayManager.
    Gets passed an ax object corresponding to a subplot from DisplayManger which this class manages. 
    This class create the plot for the ax and manages the lines by updating them in _update().
    _update() is called by DisplayManager 

    """
    def __init__(self, ax, num_channels=2, sample_rate=1000, time_window=5.0, title="", blitting: bool = True):
        self.ax = ax
        self.num_points = int(sample_rate * time_window)
        self.freq_domain = np.fft.rfftfreq(self.num_points, 1/sample_rate)
        self.time_deques = [deque(np.zeros(self.num_points), maxlen=self.num_points) for _ in range(num_channels)]
        self.title = title # ensure title has format "base title : X Axis"
        self.blitting = blitting
        self.lines = [self.ax.plot(self.freq_domain, np.zeros(self.freq_domain.size), label=f"Ch {i+1}")[0] for i in range(num_channels)]
        
        self.ax.set_title(title)
        if self.blitting:
            self.ax.set_ylim(0, 2000) # Required for efficient blitting
        self.ax.grid(True)

    def update(self, data):
        if data is None: return self.lines
        for i in range(len(self.lines)):
            self.time_deques[i].extend(data[i])
        
        y_fft = np.abs(np.fft.rfft(np.array(self.time_deques), axis=1)) / self.num_points
        y_fft[:, 0] = 0 # DC offset removal
        y_fft[:, 1:] *= 2 
        
        for i, line in enumerate(self.lines):
            line.set_ydata(y_fft[i])
            
        if not self.blitting:
            self.ax.relim()
            self.ax.autoscale_view(scalex=True, scaley=True)
            
        return self.lines

    def update_title_axis(self, axis):
        base_title, _ = self.title.split(" : ")
        self.ax.set_title(f"{base_title} : {axis.upper()} Axis")


class DisplayManager():

    def __init__(self, data_generator, blitting: bool = True):
        
        
        # Create a 2x2 grid in ONE window
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.data_generator = data_generator

        # Initialize the sub-managers with specific axes
        self.plots = [
            TimeDomain(self.axes[0, 0], title="Raw Time Domain : X Axis", blitting=blitting),
            FrequencyDomain(self.axes[0, 1], title="Raw Frequency Domain : X Axis", blitting=blitting),
            TimeDomain(self.axes[1, 0], title="Filtered Time Domain : X Axis", blitting=blitting),
            FrequencyDomain(self.axes[1, 1], title="Filtered Frequency Domain : X Axis", blitting=blitting)
        ]
        
        self.fig.tight_layout()
        
        # ONE animation for all 4 plots
        self.anim = FuncAnimation(self.fig, self._main_update, frames=self.data_generator, 
                                  interval=50, blit=blitting, cache_frame_data=False)

    def _main_update(self, frame):
        if frame is None: return [line for p in self.plots for line in p.lines]
        
        raw_data, filt_data = frame # We expect the generator to yield a tuple
        
        # Update each plot logic
        all_lines = []
        all_lines.extend(self.plots[0].update(raw_data)) # update returns the updated lines and uses the data to update axis 
        all_lines.extend(self.plots[1].update(raw_data))
        all_lines.extend(self.plots[2].update(filt_data))
        all_lines.extend(self.plots[3].update(filt_data))
        
        return all_lines
    
    def change_title_axes(self, axis: Literal["x", "y", "z"]):
        
        for plot in self.plots:
            plot.update_title_axis(axis)
            
        self.fig.canvas.draw_idle() # to force a redraw dispite blitting
