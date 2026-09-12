use axum::{
    extract::{State, Path, Multipart},
    response::{IntoResponse, Json},
    http::StatusCode,
};
use serde_json::json;
use uuid::Uuid;
use tokio::fs::File;
use tokio::io::AsyncWriteExt;
use crate::state::AppState;
use crate::models::StatusResponse;
use crate::analysis::run_analysis_task;

pub async fn health_check() -> impl IntoResponse {
    Json(json!({"status": "ok"}))
}

pub async fn upload_file(
    State(state): State<AppState>,
    mut multipart: Multipart,
) -> impl IntoResponse {
    let mut filename = String::new();
    let mut file_content = Vec::new();

    while let Some(field) = multipart.next_field().await.unwrap_or(None) {
        if let Some(name) = field.file_name() {
            filename = name.to_string();
            let data = field.bytes().await.unwrap();
            file_content.extend_from_slice(&data);
        }
    }

    if filename.is_empty() || file_content.is_empty() {
        return (StatusCode::BAD_REQUEST, Json(json!({"error": "No file uploaded"}))).into_response();
    }

    let job_id = Uuid::new_v4().to_string();
    let safe_filename = filename.replace("..", "").replace("/", "");
    let ext = std::path::Path::new(&safe_filename)
        .extension()
        .and_then(|s| s.to_str())
        .unwrap_or("");
        
    let saved_filename = format!("{}.{}", job_id, ext);
    let uploads_dir = std::env::var("UPLOADS_DIR").unwrap_or_else(|_| "../data/uploads".into());
    let filepath = format!("{}/{}", uploads_dir, saved_filename);

    if let Ok(mut file) = File::create(&filepath).await {
        let _ = file.write_all(&file_content).await;
    } else {
        return (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({"error": "Failed to save file"}))).into_response();
    }

    state.add_job(job_id.clone(), safe_filename.clone()).await;

    tokio::spawn(run_analysis_task(state.clone(), job_id.clone(), filepath));

    (StatusCode::ACCEPTED, Json(json!({"id": job_id, "message": "Analysis started"}))).into_response()
}

pub async fn get_status(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    if let Some(job) = state.get_job(&id).await {
        Json(StatusResponse {
            id: job.id,
            status: job.status,
            error: job.error,
        }).into_response()
    } else {
        (StatusCode::NOT_FOUND, Json(json!({"error": "Job not found"}))).into_response()
    }
}

pub async fn get_results(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    if let Some(job) = state.get_job(&id).await {
        if let Some(result) = job.result {
            Json(result).into_response()
        } else {
            (StatusCode::ACCEPTED, Json(json!({"message": "Result not ready", "status": job.status}))).into_response()
        }
    } else {
        (StatusCode::NOT_FOUND, Json(json!({"error": "Job not found"}))).into_response()
    }
}

pub async fn export_json(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    if let Some(job) = state.get_job(&id).await {
        if let Some(result) = job.result {
            (
                [(axum::http::header::CONTENT_TYPE, "application/json"),
                 (axum::http::header::CONTENT_DISPOSITION, &format!("attachment; filename=\"{}_analysis.json\"", id)[..])],
                Json(result).into_response().into_body()
            ).into_response()
        } else {
            (StatusCode::BAD_REQUEST, Json(json!({"error": "Result not ready"}))).into_response()
        }
    } else {
        (StatusCode::NOT_FOUND, Json(json!({"error": "Job not found"}))).into_response()
    }
}

pub async fn export_csv(
    State(_state): State<AppState>,
    Path(_id): Path<String>,
) -> impl IntoResponse {
    (StatusCode::NOT_IMPLEMENTED, Json(json!({"error": "CSV export not implemented yet"}))).into_response()
}
