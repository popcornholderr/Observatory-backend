import numpy as np
import scipy.signal as signal

def extract_parameters(signal_data, sample_rate, detection):
    if detection["signal_present"]:
        active_signal = signal_data[detection["start_idx"]:detection["end_idx"]]
    else:
        active_signal = signal_data
        
    if len(active_signal) == 0:
        active_signal = signal_data
        
    if np.iscomplexobj(active_signal):
        power_linear = np.mean(np.abs(active_signal)**2)
    else:
        power_linear = np.mean(active_signal**2)
        
    power_db = 10 * np.log10(power_linear) if power_linear > 0 else -100
    
    noise_power_linear = 0
    if detection["signal_present"] and detection["start_idx"] > int(sample_rate * 0.05):
        noise_segment = signal_data[0:detection["start_idx"]]
        if np.iscomplexobj(noise_segment):
            noise_power_linear = np.mean(np.abs(noise_segment)**2)
        else:
            noise_power_linear = np.mean(noise_segment**2)
    
    if noise_power_linear <= 0:
        if np.iscomplexobj(signal_data):
            all_power = np.abs(signal_data)**2
        else:
            all_power = signal_data**2
        noise_power_linear = np.percentile(all_power, 10)
        
    if noise_power_linear > 0 and power_linear > 0:
        snr_db = 10 * np.log10(power_linear / noise_power_linear)
    else:
        snr_db = 0.0
        
    f, Pxx = signal.welch(
        active_signal, 
        fs=sample_rate, 
        nperseg=min(1024, len(active_signal)),
        return_onesided=not np.iscomplexobj(active_signal)
    )
    
    if np.iscomplexobj(active_signal):
        f = np.fft.fftshift(f)
        Pxx = np.fft.fftshift(Pxx)
    
    peak_idx = np.argmax(Pxx)
    center_freq = f[peak_idx]
    
    total_power = np.sum(Pxx)
    cum_power = np.cumsum(Pxx)
    
    # 99% Occupied Bandwidth
    try:
        lower_idx = np.where(cum_power >= 0.005 * total_power)[0][0]
        upper_idx = np.where(cum_power >= 0.995 * total_power)[0][0]
        bandwidth = abs(f[upper_idx] - f[lower_idx])
    except IndexError:
        bandwidth = 0.0
    
    # Advanced Metrics
    rms_amplitude = np.sqrt(power_linear)
    peak_amplitude = np.max(np.abs(active_signal))
    papr = 10 * np.log10((peak_amplitude**2) / (rms_amplitude**2)) if rms_amplitude > 0 else 0.0
    nyquist_frequency = sample_rate / 2.0
    noise_floor_db = 10 * np.log10(noise_power_linear) if noise_power_linear > 0 else -100.0
    cfo = float(center_freq)
    
    # SFDR, THD, SINAD approximations
    window = max(1, len(Pxx) // 100)
    Pxx_no_fund = np.copy(Pxx)
    Pxx_no_fund[max(0, peak_idx-window):min(len(Pxx), peak_idx+window)] = 0
    spurious_peak = np.max(Pxx_no_fund) if len(Pxx_no_fund) > 0 else 1e-12
    peak_power_spectral = Pxx[peak_idx]
    
    sfdr = 10 * np.log10(peak_power_spectral / spurious_peak) if spurious_peak > 0 else 0.0
    dist_power = np.sum(Pxx_no_fund)
    thd = 10 * np.log10(dist_power / peak_power_spectral) if peak_power_spectral > 0 and dist_power > 0 else -100.0
    sinad = 10 * np.log10(power_linear / (noise_power_linear + dist_power)) if (noise_power_linear + dist_power) > 0 else 0.0
    
    # EVM for complex signals (Assuming QPSK normalization)
    evm = 0.0
    if np.iscomplexobj(active_signal) and rms_amplitude > 0:
        subset = (active_signal[:2000] / rms_amplitude)
        ideal_pts = np.array([1+1j, 1-1j, -1+1j, -1-1j]) / np.sqrt(2)
        errors = [np.min(np.abs(pt - ideal_pts)) for pt in subset]
        evm = np.sqrt(np.mean(np.array(errors)**2)) * 100.0

    # Aliasing & Anomaly Detection
    edge_energy = np.mean(Pxx[:3]) + np.mean(Pxx[-3:])
    avg_energy = np.mean(Pxx)
    aliasing_detected = bool(edge_energy > avg_energy * 5)
    anomaly_detected = bool(papr > 25.0 or sfdr < 5.0)

    # Signal Quality Score (0-100)
    sq_score = 100.0
    if snr_db < 10: sq_score -= (10 - snr_db) * 5
    if evm > 20: sq_score -= (evm - 20)
    if aliasing_detected: sq_score -= 20
    if anomaly_detected: sq_score -= 20
    signal_quality = max(0.0, min(100.0, sq_score))

    # Heuristic for Fast Radio Burst (FRB) Dispersion Measure
    dispersion_measure = 0.0
    if detection["signal_present"] and detection["active_duration_sec"] > 0 and detection["active_duration_sec"] < 0.2 and bandwidth > sample_rate * 0.1:
        dispersion_measure = round(350.0 + (bandwidth / sample_rate) * 100, 2)

    return {
        "center_frequency_hz": float(center_freq),
        "peak_frequency_hz": float(center_freq),
        "bandwidth_hz": float(bandwidth),
        "nyquist_frequency_hz": float(nyquist_frequency),
        "power_db": round(float(power_db), 2),
        "snr_db": round(float(snr_db), 2),
        "noise_floor_db": round(float(noise_floor_db), 2),
        "rms_amplitude": round(float(rms_amplitude), 4),
        "peak_amplitude": round(float(peak_amplitude), 4),
        "papr_db": round(float(papr), 2),
        "cfo_hz": round(float(cfo), 2),
        "sfdr_db": round(float(sfdr), 2),
        "thd_db": round(float(thd), 2),
        "sinad_db": round(float(sinad), 2),
        "evm_percent": round(float(evm), 2) if np.iscomplexobj(active_signal) else None,
        "aliasing_detected": aliasing_detected,
        "anomaly_detected": anomaly_detected,
        "signal_quality_percent": round(float(signal_quality), 1),
        "duration_sec": detection["active_duration_sec"],
        "dispersion_measure_pc_cm3": dispersion_measure
    }
