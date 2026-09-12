import os
import numpy as np
import scipy.io.wavfile as wavfile

def load_signal(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.wav':
        sample_rate, data = wavfile.read(file_path)
        
        if data.dtype != np.float32:
            data = data.astype(np.float32)
            if np.max(np.abs(data)) > 0:
                data = data / np.max(np.abs(data))
                
        is_iq = False
        channels = 1
        if len(data.shape) > 1:
            channels = data.shape[1]
            if channels == 2:
                is_iq = True
                data = data[:, 0] + 1j * data[:, 1]
            else:
                data = data[:, 0]
                
        metadata = {
            "format": "wav",
            "sample_rate": int(sample_rate),
            "channels": channels,
            "sample_count": len(data),
            "duration_seconds": round(len(data) / sample_rate, 4),
            "data_type": "float32" if not is_iq else "complex64",
            "is_iq": is_iq
        }
        return data, metadata
        
    elif ext == '.iq':
        # Auto-detect format by checking for NaNs, Infs, or unreasonable values in float32 interpretation
        raw_data = np.fromfile(file_path, dtype=np.float32)
        is_float32 = not (np.any(np.isnan(raw_data)) or np.any(np.isinf(raw_data)) or np.max(np.abs(raw_data)) > 1e10)
        
        if not is_float32:
            # Try int16 (e.g. HackRF)
            raw_data_int16 = np.fromfile(file_path, dtype=np.int16)
            # RTL-SDR uint8 files typically have values around 127
            raw_data_uint8 = np.fromfile(file_path, dtype=np.uint8)
            
            # If standard deviation of uint8 is reasonable, it might be RTL-SDR
            if np.std(raw_data_uint8) < 50 and 100 < np.mean(raw_data_uint8) < 155:
                raw_data = (raw_data_uint8.astype(np.float32) - 127.5) / 128.0
            else:
                raw_data = raw_data_int16.astype(np.float32) / 32768.0

        if len(raw_data) % 2 != 0:
            raw_data = raw_data[:-1]
        
        i_data = raw_data[0::2]
        q_data = raw_data[1::2]
        complex_data = i_data + 1j * q_data
        
        # Normalize to prevent overflow in downstream processes
        max_val = np.max(np.abs(complex_data))
        if max_val > 0 and max_val > 2.0:
            complex_data = complex_data / max_val
        
        sample_rate = 2e6
        
        metadata = {
            "format": "iq",
            "sample_rate": int(sample_rate),
            "channels": 2,
            "sample_count": len(complex_data),
            "duration_seconds": round(len(complex_data) / sample_rate, 4),
            "data_type": "complex64",
            "is_iq": True
        }
        return complex_data, metadata
        
    else:
        raise ValueError(f"Unsupported file format: {ext}")
