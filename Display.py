import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from collections import deque
import numpy as np





class DynamicDisplay():

    def __init__(self, data_generator, x_axis = None):
        """

        :param data_generator: A data generator
        :param x_axis: If the x-axis is none will use regular time intervals, if specified (usually for fft displays) it will be used
        """
        pass

class TimeDomain(DynamicDisplay):

    def __init__(self, data_generator, sample_rate: int = 1000, num_channels: int = 2, time_window: float = 1.0, blited: bool = False,
                  title: str = "Time Domain", 
                  x_axis_label: str = "Time (s)",
                  y_axis_label: str = "Amplitude (pT)",
                ):

        self.data_generator = data_generator
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.blitted = blited
        self.title = title
        self.x_axis_label = x_axis_label
        self.y_axis_label = y_axis_label

        self.num_points = int(sample_rate * time_window) # this is the number of points that will be on the graph at one time
        self.deque_list: list[deque] = [deque(np.zeros(self.num_points), maxlen=self.num_points) for _ in range(num_channels)] # create deques for each line

        self.lines: list[plt.Line2D] = [] # type: ignore contains all the lines on the graph


        # Create the figure

        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        
        # Create time array ending at 0 (relative time). arange ensures correct dt spacing.
        t = np.arange(-self.num_points + 1, 1) / self.sample_rate
        
        # Create lines for each channel
        for i in range(self.num_channels):
            line, = self.ax.plot(t, np.zeros(self.num_points), label=f"Channel {i+1}")
            self.lines.append(line)
        
        self.ax.legend()
        
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.x_axis_label)
        self.ax.set_ylabel(self.y_axis_label)
        self.ax.grid(True)

        if blited:
            self.ax.set_ylim(-8000, 8000) # Set fixed limits for blitting
            self.anim = FuncAnimation(self.fig, self._update_graph, frames=self.data_generator, 
                                  interval=50, blit=True, cache_frame_data=False)

        else:
             self.anim = FuncAnimation(self.fig, self._update_graph, frames=self.data_generator, 
                                  interval=50, blit=False, cache_frame_data=False)


    def _update_graph(self, frame):
        """
        This function is repeatedly called by FuncAnimation to update the graph.
        This should update the y values of each line in the graph.
        
        :param frame: data from data_generator
        """
        if frame is None: return self.lines

        data = np.array(frame)

        # update deque buffers
        for i in range(self.num_channels):
            self.deque_list[i].extend(data[i])
        

        # set basline to make comparisons
        ymin = float('inf')
        ymax = float('-inf')

        # update lines 
        for i in range(self.num_channels):
            new_y = np.array(self.deque_list[i])
            self.lines[i].set_ydata(new_y)
        
            # update min/ max
            ymin = min(ymin, np.min(new_y))
            ymax = max(ymax, np.max(new_y))
        
        if not self.blitted: # no autoscale if blitting
            if ymin == float('inf'): ymin = 0
            if ymax == float('-inf'): ymax = 1
            
            margin = (ymax - ymin) * 0.1 if ymax != ymin else 1.0 #if signal is zero then axis would become 0 so we account for this
            self.ax.set_ylim(ymin - margin, ymax + margin)

        return self.lines



class FrequencyDomain(DynamicDisplay):

    def __init__(self, data_generator, sample_rate: int = 1000, num_channels: int = 2, time_window: float = 5.0, blited: bool = False,
                  title: str = "Frequency Domain", 
                  x_axis_label: str = "Frequency (Hz)",
                  y_axis_label: str = "Amplitude (pT)",
                ):
        
        self.data_generator = data_generator
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.blitted = blited
        self.title = title
        self.x_axis_label = x_axis_label
        self.y_axis_label = y_axis_label
        self.num_points = int(sample_rate * time_window)
        self.freq_domain = np.fft.rfftfreq(self.num_points, 1/self.sample_rate) # axis for frequency domain graph, return 0 to nquist, no negative freqs


        self.time_deques: list[deque] = [deque(np.zeros(self.num_points), maxlen=self.num_points) for _ in range(num_channels)] # create deques to hold the history to calc fft                              

        self.lines: list[plt.Line2D] = [] # type: ignore contains all the lines on the graph


        # Create the figure
    
        self.fig, self.ax = plt.subplots(figsize=(10, 6))

        self.lines = []

        for i in range(self.num_channels):
            line, = self.ax.plot(self.freq_domain, np.zeros(self.freq_domain.size), label=f"Channel {i+1}")
            self.lines.append(line)
        
        self.ax.legend()
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.x_axis_label)
        self.ax.set_ylabel(self.y_axis_label)
        self.ax.grid(True)

        if blited:
            self.ax.set_ylim(0, 2000) # Set fixed limits for blitting

            self.anim = FuncAnimation(self.fig, self._update_graph, frames=self.data_generator, 
                                    interval=50, blit=True, cache_frame_data=False)
        else:
            self.anim = FuncAnimation(self.fig, self._update_graph, frames=self.data_generator, 
                                    interval=50, blit=False, cache_frame_data=False)
 
    def _update_graph(self, frame):
        if frame is None: return self.lines

        data = np.array(frame)

        # extend time deques with new history
        for i in range(self.num_channels):
            self.time_deques[i].extend(data[i])
        

        # perform fft
        y_fft = np.abs(np.fft.rfft(np.array(self.time_deques), axis=1)) / self.num_points
        
        # zero the dc component
        y_fft[:, 0] = 0
        
        y_fft[:, 1:] *= 2 # Double the amplitude for non-DC components to account for negative values
        if self.num_points % 2 == 0:
            y_fft[:, -1] /= 2 # Correct Nyquist component if even as wont have conjugate pair

        ymin = 0
        ymax = 0 # y is always postives therefore 0 is low enough to compare with to find max

        # update deque bufs
        for i in range(self.num_channels):

            # update lines
            self.lines[i].set_ydata(y_fft[i])

            # find max
            ymax = max(ymax, np.max(y_fft[i]))

        if not self.blitted: # no autoscale if blitting
            margin = (ymax - ymin) * 0.1 if ymax != ymin else 1.0
            self.ax.set_ylim(ymin, ymax + margin)


        return self.lines
