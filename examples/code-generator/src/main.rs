/*
 * Code Generator AI Agent
 * Multi-language code synthesis, boilerplate automation, and refactoring assistance.
 *
 * Scale: 10K concurrent requests, 1M daily generations
 * Tech: Rust, Actix-Web, Claude 3.5 Sonnet, Redis, PostgreSQL
 */

use actix_web::{get, post, web, App, HttpResponse, HttpServer, Responder};
use prometheus::{Encoder, HistogramOpts, HistogramVec, IntCounterVec, Opts, Registry, TextEncoder};
use redis::AsyncCommands;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use anthropic::{Client as AnthropicClient, types::*};

// ============================================================================
// CONFIGURATION
// ============================================================================

#[derive(Clone)]
struct Config {
    port: u16,
    redis_url: String,
    claude_api_key: String,
    max_concurrent_requests: usize,
    code_generation_timeout_secs: u64,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            port: 8082,
            redis_url: std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://localhost:6379/2".to_string()),
            claude_api_key: std::env::var("CLAUDE_API_KEY")
                .unwrap_or_else(|_| "your-api-key-here".to_string()),
            max_concurrent_requests: 10000,
            code_generation_timeout_secs: 30,
        }
    }
}

// ============================================================================
// DATA MODELS
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
enum Language {
    Python,
    JavaScript,
    TypeScript,
    Rust,
    Go,
    Java,
    Cpp,
    CSharp,
    Ruby,
    Swift,
    Kotlin,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum GenerationType {
    Function,
    Class,
    Module,
    Test,
    Boilerplate,
    Refactor,
    Documentation,
    Api,
}

#[derive(Debug, Deserialize)]
struct CodeGenerationRequest {
    request_id: String,
    language: Language,
    generation_type: GenerationType,
    description: String,
    context: Option<String>,
    existing_code: Option<String>,
    requirements: Option<Vec<String>>,
    style_guide: Option<String>,
}

#[derive(Debug, Serialize)]
struct CodeGenerationResponse {
    request_id: String,
    generated_code: String,
    language: String,
    explanation: String,
    test_cases: Option<Vec<String>>,
    dependencies: Vec<String>,
    security_notes: Vec<String>,
    performance_notes: Vec<String>,
    processing_time_ms: u128,
}

#[derive(Debug, Deserialize)]
struct RefactorRequest {
    request_id: String,
    language: Language,
    original_code: String,
    refactor_goals: Vec<String>,
}

#[derive(Debug, Serialize)]
struct RefactorResponse {
    request_id: String,
    refactored_code: String,
    improvements: Vec<String>,
    complexity_reduction: String,
    processing_time_ms: u128,
}

#[derive(Debug, Serialize)]
struct HealthResponse {
    status: String,
    version: String,
    uptime_seconds: u64,
    active_requests: usize,
}

// ============================================================================
// APPLICATION STATE
// ============================================================================

struct AppState {
    config: Config,
    redis_client: Arc<RwLock<redis::aio::Connection>>,
    claude_client: AnthropicClient,
    metrics: Arc<Metrics>,
    start_time: Instant,
}

struct Metrics {
    registry: Registry,
    request_counter: IntCounterVec,
    generation_duration: HistogramVec,
    active_requests: prometheus::IntGauge,
}

impl Metrics {
    fn new() -> Self {
        let registry = Registry::new();

        let request_counter = IntCounterVec::new(
            Opts::new("code_generator_requests_total", "Total code generation requests"),
            &["language", "type", "status"],
        )
        .unwrap();

        let generation_duration = HistogramVec::new(
            HistogramOpts::new(
                "code_generator_duration_seconds",
                "Code generation duration",
            ),
            &["language", "type"],
        )
        .unwrap();

        let active_requests = prometheus::IntGauge::new(
            "code_generator_active_requests",
            "Active code generation requests",
        )
        .unwrap();

        registry.register(Box::new(request_counter.clone())).unwrap();
        registry.register(Box::new(generation_duration.clone())).unwrap();
        registry.register(Box::new(active_requests.clone())).unwrap();

        Metrics {
            registry,
            request_counter,
            generation_duration,
            active_requests,
        }
    }
}

// ============================================================================
// SERVICES
// ============================================================================

struct CodeGeneratorService {
    claude_client: AnthropicClient,
}

impl CodeGeneratorService {
    fn new(api_key: &str) -> Self {
        CodeGeneratorService {
            claude_client: AnthropicClient::new(api_key),
        }
    }

    async fn generate_code(&self, request: &CodeGenerationRequest) -> Result<CodeGenerationResponse, String> {
        let start_time = Instant::now();

        // Build prompt for Claude
        let prompt = self.build_generation_prompt(request);

        // Call Claude API
        let response = self.call_claude(&prompt).await?;

        // Parse response
        let (code, explanation, deps, security, performance) = self.parse_claude_response(&response);

        // Generate test cases if applicable
        let test_cases = if matches!(request.generation_type, GenerationType::Function | GenerationType::Class) {
            Some(self.generate_tests(&code, &request.language).await.ok().flatten().unwrap_or_default())
        } else {
            None
        };

        let processing_time_ms = start_time.elapsed().as_millis();

        Ok(CodeGenerationResponse {
            request_id: request.request_id.clone(),
            generated_code: code,
            language: format!("{:?}", request.language),
            explanation,
            test_cases,
            dependencies: deps,
            security_notes: security,
            performance_notes: performance,
            processing_time_ms,
        })
    }

    async fn refactor_code(&self, request: &RefactorRequest) -> Result<RefactorResponse, String> {
        let start_time = Instant::now();

        let prompt = format!(
            r#"Refactor this {} code according to these goals: {:?}

ORIGINAL CODE:
```
{}
```

Provide:
1. Refactored code with best practices
2. List of improvements made
3. Complexity reduction analysis

Respond with JSON:
{{
  "refactored_code": "...",
  "improvements": ["..."],
  "complexity_reduction": "..."
}}
"#,
            format!("{:?}", request.language),
            request.refactor_goals,
            request.original_code
        );

        let response = self.call_claude(&prompt).await?;

        // Parse JSON response (simplified for example)
        let refactored_code = response.clone();
        let improvements = vec!["Improved readability".to_string(), "Reduced complexity".to_string()];
        let complexity_reduction = "Reduced cyclomatic complexity from 15 to 8".to_string();

        let processing_time_ms = start_time.elapsed().as_millis();

        Ok(RefactorResponse {
            request_id: request.request_id.clone(),
            refactored_code,
            improvements,
            complexity_reduction,
            processing_time_ms,
        })
    }

    fn build_generation_prompt(&self, request: &CodeGenerationRequest) -> String {
        let lang = format!("{:?}", request.language);
        let gen_type = format!("{:?}", request.generation_type);

        let context_section = request
            .context
            .as_ref()
            .map(|c| format!("\nCONTEXT:\n{}\n", c))
            .unwrap_or_default();

        let existing_code_section = request
            .existing_code
            .as_ref()
            .map(|c| format!("\nEXISTING CODE:\n```\n{}\n```\n", c))
            .unwrap_or_default();

        let requirements_section = request
            .requirements
            .as_ref()
            .map(|r| format!("\nREQUIREMENTS:\n{}\n", r.join("\n- ")))
            .unwrap_or_default();

        format!(
            r#"Generate production-quality {} code for: {}

TYPE: {}
DESCRIPTION: {}
{}{}{}

Provide:
1. Clean, idiomatic code with comprehensive documentation
2. Error handling for all edge cases
3. Type hints/annotations where applicable
4. Security considerations
5. Performance optimizations
6. Required dependencies

Respond with:
- CODE: The complete implementation
- EXPLANATION: Brief explanation of the approach
- DEPENDENCIES: Required packages/libraries
- SECURITY: Security considerations
- PERFORMANCE: Performance notes

Focus on: correctness, readability, maintainability, and production-readiness.
"#,
            lang,
            request.description,
            gen_type,
            request.description,
            context_section,
            existing_code_section,
            requirements_section
        )
    }

    async fn call_claude(&self, prompt: &str) -> Result<String, String> {
        // Simplified Claude API call - in production, use full anthropic-sdk-rust
        // This is a mock for demonstration
        Ok(format!(
            r#"```python
def example_function(x: int, y: int) -> int:
    """
    Example generated function.

    Args:
        x: First integer
        y: Second integer

    Returns:
        Sum of x and y
    """
    if not isinstance(x, int) or not isinstance(y, int):
        raise TypeError("Both arguments must be integers")
    return x + y
```

EXPLANATION: This is a simple function that adds two integers with type checking.

DEPENDENCIES:
- None (uses stdlib only)

SECURITY:
- Input validation to prevent type confusion
- No external dependencies reduce attack surface

PERFORMANCE:
- O(1) time complexity
- Minimal memory footprint
"#
        ))
    }

    async fn generate_tests(&self, code: &str, language: &Language) -> Result<Option<Vec<String>>, String> {
        // Mock test generation
        Ok(Some(vec![
            "test_basic_functionality()".to_string(),
            "test_edge_cases()".to_string(),
            "test_error_handling()".to_string(),
        ]))
    }

    fn parse_claude_response(&self, response: &str) -> (String, String, Vec<String>, Vec<String>, Vec<String>) {
        // Simplified parsing - in production, use proper parsing
        let code = response
            .lines()
            .skip_while(|l| !l.contains("```"))
            .skip(1)
            .take_while(|l| !l.contains("```"))
            .collect::<Vec<&str>>()
            .join("\n");

        let explanation = "Generated code with best practices".to_string();
        let deps = vec![];
        let security = vec!["Input validation implemented".to_string()];
        let performance = vec!["Optimized for O(1) complexity".to_string()];

        (code, explanation, deps, security, performance)
    }
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

#[get("/health")]
async fn health_check(data: web::Data<Arc<AppState>>) -> impl Responder {
    let uptime = data.start_time.elapsed().as_secs();
    let active = data.metrics.active_requests.get() as usize;

    HttpResponse::Ok().json(HealthResponse {
        status: "healthy".to_string(),
        version: "1.0.0".to_string(),
        uptime_seconds: uptime,
        active_requests: active,
    })
}

#[post("/api/v1/generate")]
async fn generate_code(
    request: web::Json<CodeGenerationRequest>,
    data: web::Data<Arc<AppState>>,
) -> impl Responder {
    data.metrics.active_requests.inc();
    let lang = format!("{:?}", request.language);
    let gen_type = format!("{:?}", request.generation_type);

    let timer = data
        .metrics
        .generation_duration
        .with_label_values(&[&lang, &gen_type])
        .start_timer();

    let service = CodeGeneratorService::new(&data.config.claude_api_key);

    match service.generate_code(&request).await {
        Ok(response) => {
            data.metrics
                .request_counter
                .with_label_values(&[&lang, &gen_type, "success"])
                .inc();
            timer.observe_duration();
            data.metrics.active_requests.dec();
            HttpResponse::Ok().json(response)
        }
        Err(e) => {
            data.metrics
                .request_counter
                .with_label_values(&[&lang, &gen_type, "error"])
                .inc();
            timer.observe_duration();
            data.metrics.active_requests.dec();
            HttpResponse::InternalServerError().json(serde_json::json!({
                "error": e
            }))
        }
    }
}

#[post("/api/v1/refactor")]
async fn refactor_code(
    request: web::Json<RefactorRequest>,
    data: web::Data<Arc<AppState>>,
) -> impl Responder {
    let service = CodeGeneratorService::new(&data.config.claude_api_key);

    match service.refactor_code(&request).await {
        Ok(response) => HttpResponse::Ok().json(response),
        Err(e) => HttpResponse::InternalServerError().json(serde_json::json!({
            "error": e
        })),
    }
}

#[get("/metrics")]
async fn metrics(data: web::Data<Arc<AppState>>) -> impl Responder {
    let encoder = TextEncoder::new();
    let metric_families = data.metrics.registry.gather();
    let mut buffer = vec![];
    encoder.encode(&metric_families, &mut buffer).unwrap();

    HttpResponse::Ok()
        .content_type("text/plain; version=0.0.4")
        .body(buffer)
}

// ============================================================================
// MAIN
// ============================================================================

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));

    let config = Config::default();
    let port = config.port;

    // Initialize Redis connection
    let redis_client = redis::Client::open(config.redis_url.clone()).unwrap();
    let redis_conn = redis_client.get_async_connection().await.unwrap();

    // Initialize Claude client (mock for demo)
    let claude_client = AnthropicClient::new(&config.claude_api_key);

    // Initialize metrics
    let metrics = Arc::new(Metrics::new());

    // Create application state
    let app_state = Arc::new(AppState {
        config: config.clone(),
        redis_client: Arc::new(RwLock::new(redis_conn)),
        claude_client,
        metrics,
        start_time: Instant::now(),
    });

    log::info!("Starting Code Generator agent on port {}", port);

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(app_state.clone()))
            .service(health_check)
            .service(generate_code)
            .service(refactor_code)
            .service(metrics)
    })
    .workers(8)
    .bind(("0.0.0.0", port))?
    .run()
    .await
}
