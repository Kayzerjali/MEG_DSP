import nidaqmx
from nidaqmx.constants import AcquisitionType
from typing import Literal
import numpy as np
import time
import threading
import queue

import Filter



class DataSource():

    def get_data(self, num_samples: int):
        pass
    def get_num_channels(self):
        pass
    
    def data_stream(self):
        pass
    def close(self):
        pass

class MockText(DataSource):

    def __init__(self, filename: str):
        self.filename = filename


    def get_data(self, num_samples: int):

        return super().get_data(num_samples)
    
    def get_num_channels(self):
        return super().get_num_channels()
    
    def data_stream(self):
        return super().data_stream()
    
class MockSignal(DataSource):

    def __init__(self, sample_rate: int = 1000, frequencies: list = [10, 50, 2, 5, 100, 75], num_channels: int = 2):
        self.sample_rate = sample_rate
        self.frequencies = frequencies
        self.num_channels = num_channels
        self.current_time = 0
        self.dc_offsets = np.random.uniform(-500, 500, (num_channels, 1))

    def get_data(self, num_samples: int):
        t = np.arange(num_samples) / self.sample_rate + self.current_time
        self.current_time += num_samples / self.sample_rate
        
        val = np.zeros(num_samples)

        for freq in self.frequencies:
            val += np.sin(2 * np.pi * freq * t) * 1000
        
        data = np.tile(val, (self.num_channels, 1))
        noise = np.random.normal(0, 3, (self.num_channels, num_samples))
            
        return data + noise*500 + self.dc_offsets

    def get_num_channels(self):
        return self.num_channels

    def data_stream(self, num_samples_per_read: int = 100):
        while True:
            yield self.get_data(num_samples_per_read)
            time.sleep(num_samples_per_read / self.sample_rate)


class NIDAQ(DataSource):

    def __init__(self, sample_rate : int = 1000, axis : Literal["x", "y", "z"] = "x"):
        
        self.task = nidaqmx.Task()
        self.sample_rate = sample_rate
        self.set_axis(axis) # set_axis initialises the self.task variable with the correct channels and sample rate
        
    
    def set_axis(self, axis : Literal["x", "y", "z"]):
        """
        Sets the self.channels variable according to which axis is chosen. If self.task exists, function will close it and reinitalise self.task with new axis.
    
        :param axis: The axis which the sensor measures from.
        :type axis: Literal["x", "y", "z"]
        """
        # can be called while task is running so have to close current task and reinitalise with new axis
        if self.task:
            self.task.close()

        self.task = nidaqmx.Task()
        if axis == "x":
            self.channels = ["Dev1/ai0", "Dev1/ai3"]
        elif axis == "y":
            self.channels = ["Dev1/ai1", "Dev1/ai4"]
        elif axis == "z":
            self.channels = ["Dev1/ai2", "Dev1/ai5"]
        
        self.task.ai_channels.add_ai_voltage_chan(", ".join(self.channels))
        self.task.timing.cfg_samp_clk_timing(rate = self.sample_rate, sample_mode=AcquisitionType.CONTINUOUS)

    def get_data(self, num_samples: int = 1):
        """
        Returns data in the format data = [[ch1_vals] ,[ch2_vals]]. Data is in units of pT.
        
    
        :param num_samples: Description
        :type num_samples: int
        """
        data = self.task.read(num_samples)
        data = np.array(data)
        data = (data/2.7) * 1000 # voltage to pT conversion (assuming 2.7 V/nT)

        if data.ndim == 1: # one sample per channel and data in form data = [ch1_val, ch2_val]
            data = data.reshape(2, 1)

        return data

    def get_num_channels(self):
        return len(self.channels)

    def stream(self, num_samples_per_read: int = 100): 
        """
        Creates a generator object yielding data. This can be assigned to a variable. 
        
        :param num_samples_per_read: 
        """
        while True:
            data = self.get_data(num_samples_per_read)
            yield data

            
    def close(self):
        self.task.close()

class ThreadedGenerator:
    """
    Wraps a generator in a separate thread to prevent blocking the main UI thread.
    """
    def __init__(self, generator, max_queue_size=10):
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.generator = generator
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        for item in self.generator:
            self.queue.put(item) # Blocks if queue is full, keeping memory usage low
        self.queue.put(StopIteration)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            # Get data from queue without blocking. If empty, return None.
            item = self.queue.get_nowait()
            if item is StopIteration:
                raise StopIteration
            return item
        except queue.Empty:
            return None