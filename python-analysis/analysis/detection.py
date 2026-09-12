import numpy as np

def detect_signal(signal_data, sample_rate):
    window_size = int(sample_rate * 0.01)
    if window_size == 0:
        window_size = 1
        
    if np.iscomplexobj(signal_data):
        power = np.abs(signal_data)**2
    else:
        power = signal_data**2
        
    kernel = np.ones(window_size) / window_size
    smoothed_power = np.convolve(power, kernel, mode='same')
    
    # Use 5th percentile for noise floor to handle continuous signals better
    noise_floor = np.percentile(smoothed_power, 5)
    
    # Avoid zero division
    if noise_floor < 1e-12:
        noise_floor = 1e-12
        
    threshold = noise_floor * 3.0
    
    active_regions = smoothed_power > threshold
    
    # If the signal is very continuous, max power might not exceed 3 * 5th percentile
    # In that case, we can assume the whole file is active if absolute power is high enough
    if np.max(smoothed_power) < threshold and np.mean(smoothed_power) > 1e-6:
        active_regions = np.ones_like(active_regions, dtype=bool)

    indices = np.where(active_regions)[0]
    
    if len(indices) > int(sample_rate * 0.001): # At least 1ms of signal
        start_idx = int(indices[0])
        end_idx = int(indices[-1])
        
        start_time = start_idx / sample_rate
        end_time = end_idx / sample_rate
        duration = end_time - start_time
        
        return {
            "signal_present": True,
            "start_time_sec": round(start_time, 4),
            "end_time_sec": round(end_time, 4),
            "active_duration_sec": round(duration, 4),
            "start_idx": start_idx,
            "end_idx": end_idx
        }
    else:
        return {
            "signal_present": False,
            "start_time_sec": 0.0,
            "end_time_sec": 0.0,
            "active_duration_sec": 0.0,
            "start_idx": 0,
            "end_idx": len(signal_data)
        }
