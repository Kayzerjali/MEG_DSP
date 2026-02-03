import numpy as np
from scipy import signal
from sklearn.decomposition import PCA as skPCA, IncrementalPCA as skIncrementalPCA
import threading




class Filter():

    def process_chunk(self, data):
        raise NotImplementedError

    def filter(self, data_generator):
        for data in data_generator:
            if data is None:
                yield None
                continue
            yield self.process_chunk(data)
    

class BandPass(Filter):

    def __init__(self, sample_freq : int = 1000, lowcut : int = 50, highcut : int = 250, num_channels : int = 2, order : int = 5):

        self.numer = None
        self.denom = None
        self.sos = None
        self.lock = threading.Lock()
        self.num_channels = num_channels

        self.sample_freq = sample_freq
        self.calc_filt_coeffs(lowcut, highcut, order) # populates numer and denom

        zi_init = signal.sosfilt_zi(self.sos) # calculates the inital state of filter

        # Reshape zi to (n_sections, n_channels, 2) for compatibility with (n_channels, n_samples) data
        self.zi_init = np.repeat(zi_init[:, np.newaxis, :], num_channels, axis=1)
        self.zi = self.zi_init.copy()

    def reset_state(self):
        self.zi = self.zi_init.copy()


    def calc_filt_coeffs(self, lowcut : int, highcut : int, order : int = 5):
        """
        Populates the self.sos variables with the filter coefficients

        """
        self.sos = signal.butter(order, [lowcut, highcut], btype='band', fs = self.sample_freq, output='sos') # passing fs as param mean dont have to normalise frequs


    def process_chunk(self, data):
        # Apply filter along the last axis (time), maintaining state in self.zi
        with self.lock:
            filtered_data, self.zi = signal.sosfilt(self.sos, data, axis=-1, zi=self.zi)
        return filtered_data


    def change_filt_coeffs(self, lowcut : int, highcut : int, order : int = 5):
        with self.lock:
            self.calc_filt_coeffs(lowcut, highcut, order) # updates self.sos which is used in sosfilt()
            
            # Recalculate zi_init because order (and thus number of sections) might have changed
            zi_init = signal.sosfilt_zi(self.sos)
            self.zi_init = np.repeat(zi_init[:, np.newaxis, :], self.num_channels, axis=1)
            self.reset_state()
        print(f"Filter characteristics changed to lowcut: {lowcut}, highcut: {highcut}, order: {order}")





class PCA(Filter):

    def __init__(self, n_components: int = 2):

        self.n_components = n_components
        self.pca = skPCA(n_components=n_components)

    def process_chunk(self, data):
        """
        Applies PCA to remove the first principal component (assumed to be common-mode noise)
        and reconstructs the signals back to the original sensor space.
        Output has the same number of channels as input.
        """
        data = np.array(data).T # PCA function require (samples, channels)
        components = self.pca.fit_transform(data)
        components[:, 0] = 0 #set the PC1, the common mode noise to zero
        data_filt = self.pca.inverse_transform(components)
        return data_filt.T


class IncrementalPCA(Filter):

    def __init__(self, n_components: int = 2):
        self.n_components = n_components
        self.ipca = skIncrementalPCA(n_components=n_components)

    def process_chunk(self, data):
        data = np.array(data).T # PCA function require (samples, channels)
        self.ipca.partial_fit(data) # Update model incrementally
        components = self.ipca.transform(data)
        components[:, 0] = 0 # set the PC1, the common mode noise to zero
        data_filt = self.ipca.inverse_transform(components)
        return data_filt.T

class Differential(Filter):
    def __init__(self):
        pass

    def process_chunk(self, data):
        data = np.array(data)
        # Calculate differential signals between adjacent channels
        diff_data = np.diff(data, axis=0)
        return diff_data
        

class FilterManager():
    """
    Transforms a raw data stream by applying a series of filters. Calling transform() returns a generator that yields tuples of (raw_data, filtered_data).
    Must first set the raw stream using add_raw_stream() and add filters using add_filter().
    """
    def __init__(self):
        self.raw_stream = None
        self.filters: dict[str, Filter] = {}
        self.lock = threading.Lock()
    
    def add_raw_stream(self, raw_stream):
        self.raw_stream = raw_stream
    
    def add_filter(self, filter_name: str, filter_obj: Filter):
        with self.lock:
            self.filters[filter_name] = filter_obj
    
    def remove_filter(self, filter_name: str):
        with self.lock:
            if filter_name in self.filters:
                del self.filters[filter_name]
    
    def list_filters(self) -> list[str]:
        with self.lock:
            return list(self.filters.keys())

    def transform(self):
        """
        Returns 2 streams, the first of raw data, the second of filtered data.
        
        """
        if self.raw_stream is None:
            raise ValueError("Raw stream not set. Use add_raw_stream() to set it before transforming.")

        # Iterate over the raw stream directly
        for raw_data in self.raw_stream:
            if raw_data is None:
                yield None
                continue
            
            filtered_data = raw_data
            
            # Get a snapshot of current filters safely
            with self.lock:
                current_filters = list(self.filters.values())
            
            # Apply each filter sequentially to this chunk of data
            for filt in current_filters:
                filtered_data = filt.process_chunk(filtered_data)
            
            yield (raw_data, filtered_data)
        