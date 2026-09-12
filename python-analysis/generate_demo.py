import os
import numpy as np
import scipy.io.wavfile as wavfile

def generate_deep_space_sample(out_path):
    sample_rate = 48000
    duration = 5.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    noise = np.random.normal(0, 0.1, len(t))
    
    freq = 5000 + 100 * np.sin(2 * np.pi * 0.1 * t)
    signal = 0.5 * np.sin(2 * np.pi * freq * t)
    
    envelope = np.exp(-((t - 2.5) ** 2) / 0.5)
    
    combined = noise + signal * envelope
    combined = np.clip(combined, -1.0, 1.0)
    
    wavfile.write(out_path, sample_rate, combined.astype(np.float32))

def generate_digital_iq(out_path):
    sample_rate = 1e6
    duration = 0.1
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    symbol_rate = 50e3
    num_symbols = int(duration * symbol_rate)
    symbols = np.random.choice([1+1j, 1-1j, -1+1j, -1-1j], num_symbols)
    
    samples_per_symbol = int(sample_rate / symbol_rate)
    iq_signal = np.repeat(symbols, samples_per_symbol)
    
    noise = np.random.normal(0, 0.2, len(iq_signal)) + 1j * np.random.normal(0, 0.2, len(iq_signal))
    iq_signal = iq_signal + noise
    
    interleaved = np.empty((iq_signal.size * 2,), dtype=np.float32)
    interleaved[0::2] = np.real(iq_signal)
    interleaved[1::2] = np.imag(iq_signal)
    
    interleaved.tofile(out_path)

def generate_pulsar(out_path):
    sample_rate = 48000
    duration = 10.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    noise = np.random.normal(0, 0.15, len(t))
    
    # Pulsar period approx 0.714 seconds (like Vela pulsar)
    period = 0.714
    pulse_width = 0.05
    
    pulse_train = np.zeros_like(t)
    for i in range(int(duration / period) + 1):
        center_time = i * period
        pulse_train += np.exp(-((t - center_time) ** 2) / (2 * (pulse_width/2)**2))
        
    signal = 0.6 * pulse_train * np.sin(2 * np.pi * 1500 * t)
    combined = noise + signal
    combined = np.clip(combined, -1.0, 1.0)
    wavfile.write(out_path, sample_rate, combined.astype(np.float32))

def generate_frb(out_path):
    import scipy.signal as signal
    sample_rate = 2e6
    duration = 0.5
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    noise = np.random.normal(0, 0.1, len(t)) + 1j * np.random.normal(0, 0.1, len(t))
    
    # FRB dispersion: high frequencies arrive first, low frequencies later.
    # We simulate a chirp that goes from 500kHz down to -500kHz very quickly.
    # The sweep duration is ~50ms
    frb_start = 0.2
    frb_duration = 0.05
    
    chirp_t = t[(t >= frb_start) & (t < frb_start + frb_duration)] - frb_start
    chirp_signal = signal.chirp(chirp_t, f0=500e3, t1=frb_duration, f1=-500e3, method='quadratic')
    
    # Gaussian envelope
    envelope = np.exp(-((chirp_t - frb_duration/2) ** 2) / (2 * (frb_duration/4)**2))
    
    iq_signal = np.copy(noise)
    start_idx = int(frb_start * sample_rate)
    end_idx = start_idx + len(chirp_signal)
    
    iq_signal[start_idx:end_idx] += 0.8 * chirp_signal * envelope
    
    interleaved = np.empty((iq_signal.size * 2,), dtype=np.float32)
    interleaved[0::2] = np.real(iq_signal)
    interleaved[1::2] = np.imag(iq_signal)
    interleaved.tofile(out_path)

if __name__ == "__main__":
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
    os.makedirs(demo_dir, exist_ok=True)
    
    generate_deep_space_sample(os.path.join(demo_dir, "deep_space.wav"))
    generate_digital_iq(os.path.join(demo_dir, "digital_qpsk.iq"))
    generate_pulsar(os.path.join(demo_dir, "pulsar_b0329.wav"))
    generate_frb(os.path.join(demo_dir, "frb_chime.iq"))
    
    print(f"Demo files generated in {demo_dir}")
