import argparse
import json
import os
import sys
import traceback

def main():
    parser = argparse.ArgumentParser(description="Space Radio Signal Analysis Machine")
    parser.add_argument("--input", required=True, help="Input file path (.wav or .iq)")
    parser.add_argument("--output-dir", required=True, help="Directory to save output files")
    parser.add_argument("--job-id", required=True, help="Job ID for this analysis")

    args = parser.parse_args()

    input_file = args.input
    output_dir = args.output_dir
    job_id = args.job_id

    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(input_file):
        print(json.dumps({"error": f"Input file not found: {input_file}"}))
        sys.exit(1)
        
    try:
        from analysis.pipeline import run_pipeline
        result = run_pipeline(input_file, output_dir, job_id)
        
        result_file = os.path.join(output_dir, f"{job_id}_result.json")
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=4)
            
        print(json.dumps({"status": "success", "result_file": result_file}))
    except Exception as e:
        error_info = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_info))
        sys.exit(1)

if __name__ == "__main__":
    main()
