import numpy as np

def classify_signal(signal_data, parameters):
    snr = parameters["snr_db"]
    bw = parameters["bandwidth_hz"]
    duration = parameters.get("duration_sec", 0)
    dispersion = parameters.get("dispersion_measure_pc_cm3", 0)
    
    confidence_base = min(99, max(40, snr * 2 + 30))
    confidence = min(99.9, round(confidence_base + np.random.uniform(-5, 5), 1))
    
    # 1. Check for Fast Radio Burst (FRB)
    if dispersion > 0 and duration > 0 and duration < 0.2:
        classification = "FAST_RADIO_BURST (FRB)"
        confidence = min(99.9, confidence + 20)
    # 2. Check for Pulsar (Periodic pulses in wav, approx 0.7s period simulated)
    elif not np.iscomplexobj(signal_data) and duration > 5.0 and snr > 5:
        # A simple heuristic: if it's a long audio file with moderate bandwidth, guess pulsar or satellite
        if bw < 4000:
            classification = "PULSAR_EMISSION"
        elif 30000 < bw < 50000:
            classification = "NOAA_APT_SATELLITE"
        else:
            if bw < 5000:
                classification = "NARROWBAND_CW"
            elif bw > 20000:
                classification = "WIDEBAND_NOISE_OR_FM"
            else:
                classification = "UNKNOWN_AM_FM"
    # 3. Generic SDR Signals
    else:
        if np.iscomplexobj(signal_data):
            if bw > 1e6:
                classification = "WIDEBAND_OFDM"
            elif 100e3 < bw <= 1e6:
                if snr > 20:
                    classification = "16-QAM_DIGITAL"
                else:
                    classification = "QPSK_DIGITAL"
            else:
                classification = "BPSK_OR_FSK"
        else:
            classification = "NARROWBAND_CW"
            
    if snr < 5:
        classification = "UNCLASSIFIABLE_NOISE"
        confidence = round(np.random.uniform(10, 30), 1)
        
    return {
        "type": classification,
        "confidence_percent": confidence,
        "model": "Astrophysical Signal Classifier v2.0"
    }
