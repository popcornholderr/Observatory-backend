use axum::{
    routing::{get, post},
    Router,
};
use crate::state::AppState;
use crate::handlers::{
    health_check,
    upload_file,
    get_status,
    get_results,
    export_json,
    export_csv,
};

pub fn api_routes(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health_check))
        .route("/analysis/upload", post(upload_file))
        .route("/analysis/:id/status", get(get_status))
        .route("/analysis/:id/results", get(get_results))
        .route("/analysis/:id/export/json", get(export_json))
        .route("/analysis/:id/export/csv", get(export_csv))
        .with_state(state)
}
