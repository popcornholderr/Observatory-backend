use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use crate::models::{AnalysisJob, JobStatus};

pub struct AppStateInner {
    pub jobs: HashMap<String, AnalysisJob>,
}

#[derive(Clone)]
pub struct AppState {
    pub inner: Arc<RwLock<AppStateInner>>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(RwLock::new(AppStateInner {
                jobs: HashMap::new(),
            })),
        }
    }

    pub async fn add_job(&self, id: String, filename: String) {
        let mut inner = self.inner.write().await;
        inner.jobs.insert(id.clone(), AnalysisJob {
            id,
            filename,
            status: JobStatus::Queued,
            result: None,
            error: None,
        });
    }

    pub async fn get_job(&self, id: &str) -> Option<AnalysisJob> {
        let inner = self.inner.read().await;
        inner.jobs.get(id).cloned()
    }
    
    pub async fn update_status(&self, id: &str, status: JobStatus) {
        let mut inner = self.inner.write().await;
        if let Some(job) = inner.jobs.get_mut(id) {
            job.status = status;
        }
    }
    
    pub async fn set_result(&self, id: &str, result: serde_json::Value) {
        let mut inner = self.inner.write().await;
        if let Some(job) = inner.jobs.get_mut(id) {
            job.status = JobStatus::Completed;
            job.result = Some(result);
        }
    }
    
    pub async fn set_error(&self, id: &str, error: String) {
        let mut inner = self.inner.write().await;
        if let Some(job) = inner.jobs.get_mut(id) {
            job.status = JobStatus::Failed;
            job.error = Some(error);
        }
    }
}
