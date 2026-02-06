import numpy as np
from scipy import signal
from sklearn.decomposition import PCA as skPCA, IncrementalPCA as skIncrementalPCA, KernelPCA as skKernelPCA, SparsePCA as skSparsePCA
import threading
from typing import Literal
import sys



class Filter():
    """
    Any implementation of Filter must implement the following method, process_chunk.
    To add a filter to the pipeline, register it in the container with container.register_filter("filter_name", lambda: FilterClass()).
    The filter can then be added to the filter manager with the command 'add_filt filter_name' in the CLI. This allows for dynamic addition and removal of filters during runtime.
    
    """

    def process_chunk(self, data: np.ndarray) -> np.ndarray:
        """
        Process a chunk of data by applying the filter.
        :param data: The data must be a 2D numpy array of shape (num_channels, num_samples)
        :return: Filtered data of the same shape
        """
        raise NotImplementedError("process_chunk method not implemented, base class has been invoked")

    
class BandPass(Filter):
    """
    Class for a bandpass filter implementation using second-order sections (SOS) for numerical stability.
    
    :param sample_freq: sample frequency of the data to be filtered, used to calculate the filter coefficients. This should match the sample rate of the data source. Default is 1000 Hz.
    :type sample_freq: int
    :param lowcut: low cutoff frequency of the bandpass filter. Default is 5 Hz.
    :type lowcut: int
    :param highcut: high cutoff frequency of the bandpass filter. Default is 40 Hz.
    :type highcut: int
    :param order: order of the filter. Higher order provides sharper cutoffs but may be more computationally expensive and induces phase distortions. Default is 5.
    :type order: int
    """

    def __init__(self, sample_freq : int = 1000, lowcut : int = 5, highcut : int = 40, num_channels : int = 2, order : int = 5):

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
            
            # Recalculate zi_init because order (and number of sections) might have changed
            zi_init = signal.sosfilt_zi(self.sos)
            self.zi_init = np.repeat(zi_init[:, np.newaxis, :], self.num_channels, axis=1)
            self.reset_state()
        print(f"Filter characteristics changed to lowcut: {lowcut}, highcut: {highcut}, order: {order}")

class Notch(Filter):
    """
    A notch filter implementation using second-order sections (SOS) for numerical stability.
    Designed to remove powerline interference 50Hz.

    :param sample_freq: sample frequency of the data to be filtered, used to calculate the filter coefficients. This should match the sample rate of the data source. Default is 1000 Hz.
    :type sample_freq: int
    :param notch_freq: frequency of the notch filter. Default is 50 Hz.
    :type notch_freq: int
    :param quality_factor: quality factor of the notch filter, which determines the width of the notch. Higher values result in a narrower notch. Bandwidth = notch_freq / quality_factor. Default is Q = 20.
    :type quality_factor: int
    """

    def __init__(self, sample_freq: int = 1000, notch_freq: int = 50, quality_factor: int = 20, num_channels: int = 2):
        self.sample_freq = sample_freq
        self.notch_freq = notch_freq
        self.quality_factor = quality_factor
        self.num_channels = num_channels
        self.lock = threading.Lock()

        b, a = signal.iirnotch(notch_freq, quality_factor, fs=sample_freq)
        self.sos = signal.tf2sos(b, a)
        zi_init = signal.sosfilt_zi(self.sos)

        self.zi_init = np.repeat(zi_init[:, np.newaxis, :], num_channels, axis=1)
        self.zi = self.zi_init.copy()

    def reset_state(self):
        self.zi = self.zi_init.copy()

    def process_chunk(self, data):
        with self.lock:
            filtered_data, self.zi = signal.sosfilt(self.sos, data, axis=-1, zi=self.zi)
        return filtered_data

    def change_notch_params(self, notch_freq: int, quality_factor: int):
        with self.lock:
            self.notch_freq = notch_freq
            self.quality_factor = quality_factor
            b, a = signal.iirnotch(notch_freq, quality_factor, fs=self.sample_freq)
            self.sos = signal.tf2sos(b, a) # returns a second-order-sections representation from transfer function

            zi_init = signal.sosfilt_zi(self.sos)
            self.zi_init = np.repeat(zi_init[:, np.newaxis, :], self.num_channels, axis=1)
            self.reset_state()
        print(f"Notch filter parameters changed to notch_freq: {notch_freq}, quality_factor: {quality_factor}")



class PCA(Filter):
    """
    Applies PCA to remove the first principal component (assumed to be common-mode noise)
    and reconstructs the signals back to the original sensor space.
    Output has the same number of channels as input.
    
    """

    def __init__(self, n_components: int = 2):

        self.n_components = n_components
        self.pca = skPCA(n_components=n_components)

    def process_chunk(self, data):

        data_t = np.array(data).T # Transpose to (samples, channels) for PCA
        
        if data.shape[0] < self.n_components: # not enough channels to perform PCA
            return data # Return original data (channels, samples)
            
        components = self.pca.fit_transform(data_t)
        components[:, 0] = 0 #set the PC1, the common mode noise to zero
        data_filt = self.pca.inverse_transform(components)
        return data_filt.T



class IncrementalPCA(Filter):
    """
    IPCA differs from standard PCA in that it can be updated incrementally with new data batches using the partial_fit method.
    This allows it to adapt to changes in the signal characteristics over time, which is useful for data streams.
    Standard PCA is a batch method that fits the model to the entire dataset at once and does not update with new data.
    
    
    """

    def __init__(self, n_components: int = 2):
        self.n_components = n_components
        self.ipca = skIncrementalPCA(n_components=n_components)

    def process_chunk(self, data):
        data_t = np.array(data).T # Transpose to (samples, channels) for PCA
        
        if data.shape[0] < self.n_components:
            return data # Return original data (channels, samples)

        try:
            self.ipca.partial_fit(data_t) # Update model incrementally
        except ValueError:

            # Handle case where input dimensions change (e.g. upstream filter change)
            self.ipca = skIncrementalPCA(n_components=self.n_components)
            self.ipca.partial_fit(data_t)
            
        components = self.ipca.transform(data_t)
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
        
class KPCA(Filter):
    """
    Kernel PCA (KPCA) implementation. Computer will crash if not powerful enough. KPCA is a non-linear extension of PCA that uses kernel methods to capture non-linear relationships in the data.
    It maps the input data into a higher-dimensional feature space using a kernel function and then performs PCA in that space.
    This allows KPCA to capture more complex structures in the data compared to standard PCA, which is limited to linear relationships.

    :param kernal: The kernel function to use in KPCA. Choices include 'linear', 'poly', 'rbf', 'sigmoid', 'cosine', and 'precomputed'.
    Default is 'rbf' (radial basis function), which is a popular choice for capturing non-linear relationships. Choose the kernel based on the expected structure of the data.
    

    """
    def __init__(self, n_components: int = 2, kernel: Literal['linear', 'poly', 'rbf', 'sigmoid', 'cosine', 'precomputed'] = "rbf"):
        self.n_components = n_components
        self.kpca = skKernelPCA(n_components=n_components, kernel=kernel, fit_inverse_transform=True)

    def process_chunk(self, data):
   
        data_t = np.array(data).T # Transpose to (samples, channels)
        n_samples, n_features = data_t.shape
        
        # Ensure sufficient dimensions
        if n_samples < self.n_components or n_features < self.n_components:
            return data

        # Check for constant signal (zero variance) to avoid singular matrix errors
        if np.all(np.var(data_t, axis=0) < 1e-12):
            return data

        components = self.kpca.fit_transform(data_t)
        
        if components.shape[1] > 0:
            components[:, 0] = 0 # Remove first component (assumed noise)
        
        data_filt = self.kpca.inverse_transform(components)
        return data_filt.T
        
   

class SPCA(Filter):
    """
    Sparse PCA (SPCA) implementation.
    
    Difference:
    Standard PCA produces principal components that are linear combinations of all input variables 
    (dense loadings). SPCA adds a sparsity constraint (L1 penalty), forcing many loadings to be zero.
    
    When to use:
    Use when you want interpretability or when you believe the noise/signal is localized to a 
    subset of sensors rather than spread across all of them. It helps in isolating sources.
    
    Unique feature:
    Produces "sparse" components where each component involves only a few original sensors. 
    Computationally more expensive than standard PCA.
    """

    def __init__(self, n_components: int = 2, alpha: float = 1.0):
        self.n_components = n_components
        self.spca = skSparsePCA(n_components=n_components, alpha=alpha)

    def process_chunk(self, data):
        data_t = np.array(data).T # Transpose to (samples, channels)
        
        if data.shape[0] < self.n_components:
            return data

        components = self.spca.fit_transform(data_t)
        components[:, 0] = 0 # Remove first component
        
        # Reconstruct: X_hat = T @ V + mean
        data_filt = np.dot(components, self.spca.components_) + self.spca.mean_
        return data_filt.T


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
            if filter_name == "all":
                self.filters = {}
                return
            
            if filter_name not in self.filters:
                print(f"Filter '{filter_name}' not found.")
                return
            
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
            
            if len(self.filters) == 0:
                yield (raw_data, raw_data)
                continue

            filtered_data = raw_data
            
            # Get a snapshot of current filters safely
            with self.lock:
                current_filters = list(self.filters.values())
            
            # Apply each filter sequentially to this chunk of data
            for filt in current_filters:
                filtered_data = filt.process_chunk(filtered_data)
            
            yield (raw_data, filtered_data)
        