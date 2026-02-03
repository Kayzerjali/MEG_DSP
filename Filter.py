import numpy as np
from scipy import signal
from sklearn.decomposition import PCA as skPCA, IncrementalPCA as skIncrementalPCA
import threading
import itertools




class Filter():

    def filter(self, data_generator):
        raise NotImplementedError
    

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



    def filter(self, data_generator):
        """
        Takes a data generator which uses yield to incrementally supply values and
        creates a generator of filtered values.

        :param data_generator: 
        """

        for data in data_generator:
            if data is None:
                yield None
                continue

            # Apply filter along the last axis (time), maintaining state in self.zi
            with self.lock:
                filtered_data, self.zi = signal.sosfilt(self.sos, data, axis=-1, zi=self.zi)
            yield filtered_data


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

    def filter(self, data_generator):
        """
        Applies PCA to remove the first principal component (assumed to be common-mode noise)
        and reconstructs the signals back to the original sensor space.
        Output has the same number of channels as input.
        """
        
        for data in data_generator:
            if data is None:
                yield None
                continue

            data = np.array(data).T # PCA function require (samples, channels)

            # Get components from PCA
            components = self.pca.fit_transform(data) # consider use of IncrementalPCA if issues
            components[:, 0] = 0 #set the PC1, the common mode noise to zero, takes first column of every row i.e. PC1

            # reconstruct signal in pT
            data_filt = self.pca.inverse_transform(components)

            yield data_filt.T # transpose to original format


class IncrementalPCA(Filter):

    def __init__(self, n_components: int = 2):
        self.n_components = n_components
        self.ipca = skIncrementalPCA(n_components=n_components)

    def filter(self, data_generator):
        for data in data_generator:
            if data is None:
                yield None
                continue

            data = np.array(data).T # PCA function require (samples, channels)

            self.ipca.partial_fit(data) # Update model incrementally
            components = self.ipca.transform(data)
            components[:, 0] = 0 # set the PC1, the common mode noise to zero

            data_filt = self.ipca.inverse_transform(components)

            yield data_filt.T


class FilterManager():

    def __init__(self, raw_stream, filters: list[Filter]):
        self.raw_stream = raw_stream
        self.filters = filters
    
    def add_filter(self, filter: Filter):
        self.filters.append(filter)
    
    def remove_filter(self, filter: Filter):
        self.filters.remove(filter)

    def transform(self):
        """
        Returns 2 streams, the first of raw data, the second of filtered data.
        
        """
        unfiltered_stream, stream_to_filter = itertools.tee(self.raw_stream) # create 2 streams, one to keep one to filter

        for filt in self.filters:
            stream_to_filter = filt.filter(stream_to_filter)

        for raw, filt in zip(unfiltered_stream, stream_to_filter):
            yield (raw, filt)
        