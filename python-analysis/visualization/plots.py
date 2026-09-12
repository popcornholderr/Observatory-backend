import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def setup_theme():
    sns.set_theme(style="darkgrid", rc={
        "axes.facecolor": "#121212",
        "figure.facecolor": "#0a0a0a",
        "axes.edgecolor": "#333333",
        "axes.labelcolor": "#cccccc",
        "text.color": "#cccccc",
        "xtick.color": "#cccccc",
        "ytick.color": "#cccccc",
        "grid.color": "#222222",
        "lines.linewidth": 1.0,
        "font.family": "sans-serif"
    })

def generate_visualizations(signal_data, metadata, detection, output_dir, job_id):
    setup_theme()
    
    paths = {}
    sample_rate = metadata["sample_rate"]
    
    # 1. Waveform Plot
    plt.figure(figsize=(10, 4))
    
    max_pts = 500000
    if len(signal_data) > max_pts:
        step = len(signal_data) // max_pts
        plot_data = signal_data[::step]
        time_axis = np.linspace(0, len(signal_data)/sample_rate, len(plot_data))
    else:
        plot_data = signal_data
        time_axis = np.linspace(0, len(signal_data)/sample_rate, len(plot_data))
        
    if np.iscomplexobj(plot_data):
        sns.lineplot(x=time_axis, y=np.real(plot_data), color="#4da6ff", label="In-Phase (I)", alpha=0.8)
        sns.lineplot(x=time_axis, y=np.imag(plot_data), color="#ff9933", label="Quadrature (Q)", alpha=0.8)
    else:
        sns.lineplot(x=time_axis, y=plot_data, color="#4da6ff")
        
    if detection["signal_present"]:
        plt.axvspan(detection["start_time_sec"], detection["end_time_sec"], color="#ffcc00", alpha=0.15, label="Detected Activity")
        
    plt.title("Time Domain Waveform")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    wf_path = os.path.join(output_dir, f"{job_id}_waveform.png")
    plt.savefig(wf_path, dpi=120)
    plt.close()
    paths["waveform"] = f"{job_id}_waveform.png"
    
    # 2. FFT Spectrum
    plt.figure(figsize=(10, 4))
    
    n_fft = min(8192, len(signal_data))
    if np.iscomplexobj(signal_data):
        freqs = np.fft.fftshift(np.fft.fftfreq(n_fft, 1/sample_rate))
        fft_data = np.fft.fftshift(np.abs(np.fft.fft(signal_data[:n_fft])))
    else:
        freqs = np.fft.rfftfreq(n_fft, 1/sample_rate)
        fft_data = np.abs(np.fft.rfft(signal_data[:n_fft]))
        
    fft_db = 20 * np.log10(fft_data + 1e-12)
    sns.lineplot(x=freqs, y=fft_db, color="#ffcc00")
    plt.title("Frequency Spectrum (FFT)")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    plt.tight_layout()
    fft_path = os.path.join(output_dir, f"{job_id}_fft.png")
    plt.savefig(fft_path, dpi=120)
    plt.close()
    paths["fft"] = f"{job_id}_fft.png"
    
    # 3. Spectrogram
    plt.figure(figsize=(10, 5))
    if np.iscomplexobj(signal_data):
        plt.specgram(signal_data, NFFT=1024, Fs=sample_rate, cmap='magma', noverlap=512)
    else:
        plt.specgram(signal_data, NFFT=1024, Fs=sample_rate, cmap='magma', noverlap=512, sides='onesided')
        
    plt.title("Spectrogram / Waterfall")
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.colorbar(label="Intensity (dB)")
    plt.tight_layout()
    spec_path = os.path.join(output_dir, f"{job_id}_spectrogram.png")
    plt.savefig(spec_path, dpi=120)
    plt.close()
    paths["spectrogram"] = f"{job_id}_spectrogram.png"
    
    # 4. IQ Constellation (if complex)
    if np.iscomplexobj(signal_data):
        plt.figure(figsize=(5, 5))
        
        iq_plot_data = signal_data[::max(1, len(signal_data)//20000)]
        
        sns.scatterplot(x=np.real(iq_plot_data), y=np.imag(iq_plot_data), s=5, color="#ffcc00", alpha=0.3)
        plt.axhline(0, color="#555555", linestyle='--')
        plt.axvline(0, color="#555555", linestyle='--')
        plt.title("IQ Constellation")
        plt.xlabel("In-Phase (I)")
        plt.ylabel("Quadrature (Q)")
        
        # Determine plot limits based on max amplitude
        max_val = np.max(np.abs(iq_plot_data))
        if max_val == 0: max_val = 1.0
        plt.xlim(-max_val*1.2, max_val*1.2)
        plt.ylim(-max_val*1.2, max_val*1.2)
        
        plt.tight_layout()
        iq_path = os.path.join(output_dir, f"{job_id}_iq.png")
        plt.savefig(iq_path, dpi=120)
        plt.close()
        paths["iq"] = f"{job_id}_iq.png"
        
    return paths
