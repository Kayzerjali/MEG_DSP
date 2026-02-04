import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
from collections import deque
import numpy as np
from typing import Literal
import shutil






class DynamicDisplay():

    def __init__(self):
        """

        :param data_generator: A data generator
        :param x_axis: If the x-axis is none will use regular time intervals, if specified (usually for fft displays) it will be used
        """
        self.lines = []

    def update(self, data):
        raise NotImplementedError
    
    def update_title_axis(self, axis):
        raise NotImplementedError
       

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

    def __init__(self, ax, title="", num_points: int = 1000, blitting: bool = True):

        self.ax = ax
        self.title = title
        self.num_points = num_points
        self.blitting = blitting
        self.lines = [self.ax.plot(np.zeros(self.num_points), np.zeros(self.num_points), label="PCA")[0]]
        self.ax.set_title(title)

        if self.blitting:
            self.ax.set_xlim(-8000, 8000)
            self.ax.set_ylim(-8000, 8000)

        self.ax.grid(True)

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


class DisplayManager():
    """
    Takes a data generator which yields tuples of (raw_data, filtered_data) and displays them in a 2x2 grid of plots.
    Before calling start(), use add_master_stream() to set the data generator.

    """
    def __init__(self, blitting: bool = False):
        self.blitting = blitting
        self.data_generator = None
        
        # Recording state
        self.writer = None
        self.recording_state = "IDLE"
        self.recording_filename = "recording.mp4"
        
    def add_master_stream(self, data_generator):
        self.data_generator = data_generator
    
    def set_blitting(self, blitting: bool):
        self.blitting = blitting
        
    def start_recording(self, filename: str):
        self.recording_filename = filename
        self.recording_state = "START"
    
    def stop_recording(self):
        if self.recording_state == "RECORDING":
            self.recording_state = "STOP"

    def start(self):

        if self.data_generator is None:
            raise ValueError("Data generator not set. Use add_master_stream() to set it before starting the display.")
        
        # Create a 2x2 grid in ONE window
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))

        # Initialize the sub-managers with specific axes
        self.plots: list[DynamicDisplay] = [
            TimeDomain(self.axes[0, 0], title="Raw Time Domain : X Axis", blitting=self.blitting),
            FrequencyDomain(self.axes[0, 1], title="Raw Frequency Domain : X Axis", blitting=self.blitting),
            TimeDomain(self.axes[1, 0], title="Filtered Time Domain : X Axis", blitting=self.blitting),
            FrequencyDomain(self.axes[1, 1], title="Filtered Frequency Domain : X Axis", blitting=self.blitting)
        ]
        
        self.fig.tight_layout()
        
        # ONE animation for all 4 plots
        self.anim = FuncAnimation(self.fig, self._main_update, frames=self.data_generator, 
                                  interval=50, blit=self.blitting, cache_frame_data=False)



    def _main_update(self, frame):
        if frame is None: return [line for p in self.plots for line in p.lines]
        
        # Handle Recording State Machine
        if self.recording_state == "START":
            try:
                if self.recording_filename.endswith(".gif"):
                    self.writer = PillowWriter(fps=20)
                else:
                    if shutil.which("ffmpeg") is None:
                        raise FileNotFoundError("FFmpeg is not installed or not in PATH. Install FFmpeg or use .gif extension.")
                    self.writer = FFMpegWriter(fps=20)
                
                self.writer.setup(self.fig, self.recording_filename, dpi=100)
                self.recording_state = "RECORDING"
                print(f"Recording started: {self.recording_filename}")
            except Exception as e:
                print(f"Failed to start recording: {e}")
                self.recording_state = "IDLE"
        
        elif self.recording_state == "RECORDING":
            self.writer.grab_frame() # type: ignore # if in recording mode writer is initialized
        
        elif self.recording_state == "STOP":
            if self.writer:
                self.writer.finish()
                self.writer = None
                print(f"Recording saved: {self.recording_filename}")
            self.recording_state = "IDLE"



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