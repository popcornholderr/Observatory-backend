import os
from .io import load_signal
from .preprocessing import preprocess_signal
from .detection import detect_signal
from .features import extract_parameters
from .classification import classify_signal
from visualization.plots import generate_visualizations

def run_pipeline(input_file, output_dir, job_id):
    # 02 PARSING
    signal_data, metadata = load_signal(input_file)
    
    # 03 PREPROCESSING
    cleaned_signal = preprocess_signal(signal_data)
    
    # 04 DETECTION
    detection_results = detect_signal(cleaned_signal, metadata['sample_rate'])
    
    # 05 ANALYSIS & 06 EXTRACTION
    parameters = extract_parameters(cleaned_signal, metadata['sample_rate'], detection_results)
    
    # 07 CLASSIFICATION
    classification = classify_signal(cleaned_signal, parameters)
    
    # VISUALIZATIONS
    viz_paths = generate_visualizations(cleaned_signal, metadata, detection_results, output_dir, job_id)
    
    return {
        "job_id": job_id,
        "metadata": metadata,
        "detection": detection_results,
        "parameters": parameters,
        "classification": classification,
        "visualizations": viz_paths
    }
