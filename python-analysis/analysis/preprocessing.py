import numpy as np

def preprocess_signal(signal_data):
    if np.max(np.abs(signal_data)) > 0:
        normalized = signal_data / np.max(np.abs(signal_data))
    else:
        normalized = signal_data
        
    normalized = normalized - np.mean(normalized)
    
    return normalized
