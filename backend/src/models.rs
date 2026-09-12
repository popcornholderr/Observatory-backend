use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum JobStatus {
    Queued,
    Parsing,
    Preprocessing,
    Detecting,
    Analyzing,
    Extracting,
    Classifying,
    GeneratingReport,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisJob {
    pub id: String,
    pub filename: String,
    pub status: JobStatus,
    pub result: Option<serde_json::Value>,
    pub error: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct StatusResponse {
    pub id: String,
    pub status: JobStatus,
    pub error: Option<String>,
}
