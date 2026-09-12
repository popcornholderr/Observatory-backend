use crate::state::AppState;
use crate::models::JobStatus;
use std::process::Command;
use std::env;

pub async fn run_analysis_task(state: AppState, job_id: String, filepath: String) {
    state.update_status(&job_id, JobStatus::Parsing).await;
    
    let python_bin = env::var("PYTHON_BIN").unwrap_or_else(|_| "python".into());
    let script_dir = env::var("PYTHON_SCRIPT_DIR").unwrap_or_else(|_| "../python-analysis".into());
    let results_dir = env::var("RESULTS_DIR").unwrap_or_else(|_| "../data/results".into());
    
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;
    state.update_status(&job_id, JobStatus::Preprocessing).await;
    
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;
    state.update_status(&job_id, JobStatus::Detecting).await;
    
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;
    state.update_status(&job_id, JobStatus::Analyzing).await;
    
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;
    state.update_status(&job_id, JobStatus::Extracting).await;
    
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;
    state.update_status(&job_id, JobStatus::Classifying).await;
    
    let output = Command::new(&python_bin)
        .current_dir(&script_dir)
        .arg("app.py")
        .arg("--input")
        .arg(format!("../{}", filepath)) // since CWD is script_dir, adjusting relative path
        .arg("--output-dir")
        .arg(&results_dir)
        .arg("--job-id")
        .arg(&job_id)
        .output();
        
    match output {
        Ok(out) => {
            if out.status.success() {
                let stdout = String::from_utf8_lossy(&out.stdout);
                
                let mut last_json: Option<serde_json::Value> = None;
                for line in stdout.lines() {
                    if let Ok(v) = serde_json::from_str(line) {
                        last_json = Some(v);
                    }
                }
                
                if let Some(json_val) = last_json {
                    if let Some(result_file) = json_val.get("result_file").and_then(|v| v.as_str()) {
                        state.update_status(&job_id, JobStatus::GeneratingReport).await;
                        
                        tokio::time::sleep(std::time::Duration::from_millis(500)).await;
                        
                        // the result_file is likely relative to the script dir, so we adjust
                        let actual_result_file = format!("{}/{}", script_dir, result_file);
                        
                        if let Ok(result_content) = tokio::fs::read_to_string(&actual_result_file).await {
                            if let Ok(result_json) = serde_json::from_str(&result_content) {
                                state.set_result(&job_id, result_json).await;
                            } else {
                                state.set_error(&job_id, "Invalid result JSON format".into()).await;
                            }
                        } else {
                            state.set_error(&job_id, format!("Could not read result file: {}", actual_result_file)).await;
                        }
                    } else if let Some(err) = json_val.get("error").and_then(|v| v.as_str()) {
                        state.set_error(&job_id, err.to_string()).await;
                    } else {
                        state.set_error(&job_id, "Python script returned success but no result_file".into()).await;
                    }
                } else {
                    state.set_error(&job_id, "Failed to parse Python output".into()).await;
                }
                
            } else {
                let stderr = String::from_utf8_lossy(&out.stderr);
                state.set_error(&job_id, format!("Python execution failed: {}", stderr)).await;
            }
        },
        Err(e) => {
            state.set_error(&job_id, format!("Failed to spawn Python process: {}", e)).await;
        }
    }
}
