# ToolBrain Tracing 🧠🔍

**ToolBrain Tracing** is a powerful observability and analytics platform for AI agents. Track, analyze, and optimize your agent's behavior with comprehensive tracing, feedback collection, and natural language query capabilities.

## ✨ Key Features

- **📊 Track & Visualize Agent Behavior**: Capture and explore agent workflows in a standardized OTLP (OpenTelemetry Protocol) format
- **🔄 Framework-Agnostic**: Works with any AI agent framework - includes smolagents integration example, with docs for building custom converters
- **💾 Dual Backend Support**: SQLite for development, PostgreSQL for production
- **🤖 AI-Powered Analytics**: Ask questions about your traces in natural language via LibrarianAgent (multi-provider LLM support)
- **🖥️ Admin UI + Frontend Placeholder**: Streamlit-based admin UI today, with a `web/` directory reserved for a future React frontend
- **🐳 Docker-Ready**: Full Docker Compose setup for one-command deployment
- **🔌 REST API**: Clean FastAPI endpoints at `/api/v1` for easy integration

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│  Your AI Agent  │─────▶│  TraceStore API  │─────▶│  PostgreSQL │
│   (smolagents,  │      │    (FastAPI)     │      │   / SQLite  │
│    or custom)   │      └──────────────────┘      └─────────────┘
└─────────────────┘              │
                                 ▼
                       ┌──────────────────┐
                       │  Admin Panel UI  │
                       │                  │
                       └──────────────────┘
```

- **Your AI Agent:** Any agent framework. Uses the TraceClient SDK to send data.
- **TraceStore API:** The central FastAPI server. Ingests, stores, and serves trace data.
- **Database:** The persistence layer (PostgreSQL or SQLite).
- **Admin Panel UI:** A client (Streamlit/React) that consumes the TraceStore API.

**Tech Stack:**
- **Backend**: FastAPI, SQLAlchemy 2.0, Pydantic V2
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: React (Admin UI)
- **Deployment**: Docker Compose
- **AI Integration**: LibrarianAgent with multi-provider LLM support

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.8+ (for local development)
- PostgreSQL 15+ (if running without Docker)

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/ToolBrain/toolbrain-tracing.git
   cd toolbrain-tracing
   ```

2. **Start the services**
   ```bash
   # Install the CLI tool
   pip install -e .
   
   # Start PostgreSQL + API server
   toolbrain-trace up
   ```

3. **Access the services**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Streamlit UI: Run separately with `streamlit run src/examples/app.py`
   - If needed: `pip install streamlit pandas`

4. **Seed sample data** (optional)
   ```bash
   cd src/examples
   python seed_tracestore_samples.py --backend postgresql --db-url "postgresql://traceuser:tracepass@localhost:5432/tracedb"
   ```

### Option 2: Local Development

1. **Create and activate a virtual environment**
    ```bash
    python -m venv .venv
    # Windows (PowerShell)
    .\.venv\Scripts\Activate.ps1
    # macOS/Linux
    source .venv/bin/activate
    ```

2. **Install dependencies**
    ```bash
    pip install -e .
    # Optional extras
    # pip install -e .[ai,dev]
    ```

3. **Run the API server** (SQLite mode)
    ```bash
    toolbrain-trace init-db
    toolbrain-trace start
    ```

4. **Run the Streamlit UI**
   ```bash
   cd src/examples
   streamlit run app.py
   ```

## 📖 Usage

### CLI Commands

```bash
# Start Docker services
toolbrain-trace up

# Start with rebuild (after code changes)
toolbrain-trace up --build

# Stop services
toolbrain-trace down

# Manual Docker rebuild (if changes aren't picked up)
docker compose -f docker/docker-compose.yml build --no-cache
```

### API Endpoints

**Traces**
- `POST /api/v1/traces` - Create a new trace
- `GET /api/v1/traces` - List all traces
- `GET /api/v1/traces/{trace_id}` - Get trace details
- `POST /api/v1/traces/{trace_id}/feedback` - Add feedback to a trace

**Analytics**
- `GET /api/v1/stats` - Get overall statistics
- `GET /api/v1/analytics/tool_usage` - Get tool usage analytics

**Natural Language Queries**
- `POST /api/v1/natural_language_query` - Query traces with natural language
    - Requires LLM configuration via env vars (for example: `LLM_PROVIDER`, `LLM_API_KEY`)

**Example API Usage:**

```python
import requests

# Create a trace
response = requests.post("http://localhost:8000/api/v1/traces", json={
    "trace_id": "trace-001",
    "spans": [
        {
            "span_id": "span-001",
            "trace_id": "trace-001",
            "name": "User Request",
            "start_time": "2024-01-01T10:00:00Z",
            "end_time": "2024-01-01T10:00:05Z",
            "attributes": {
                "toolbrain.span.type": "user_request",
                "toolbrain.content.new_content": "What's the stock price of NVIDIA?"
            }
        }
    ]
})

# Add feedback
requests.post("http://localhost:8000/api/v1/traces/trace-001/feedback", json={
    "rating": 5,
    "tags": ["accurate", "fast"],
    "comment": "Great response!",
    "metadata": {
        "outcome": "success",
        "efficiency_score": 0.95
    }
})
```

### Streamlit UI

The admin UI provides:
- **Trace Browser**: View all traces with filters
- **Trace Details**: Expandable span tree visualization
- **Feedback Form**: Rate and tag traces
- **Analytics Dashboard**: Stats, tool usage charts

Dependencies for the UI:

```bash
pip install streamlit pandas
```

## 🔌 Integration with Your Agent

### Using the TraceStore Client

```python
from toolbrain_tracing.sdk.client import TraceClient

client = TraceClient(base_url="http://localhost:8000")

# Submit a trace
client.log_trace({
    "trace_id": "my-trace-001",
    "spans": [...],  # Your OTLP spans
    "feedback": {}
})

# Query traces
traces = client.list_traces()
```

### Building a Custom Converter

ToolBrain uses the **ToolBrain OTLP (OpenTelemetry Protocol) format** - a delta-based trace schema with parent_id chains for conversation reconstruction.

See [docs/Converter.md](docs/Converter.md) for:
- OTLP schema explanation (parent_id, new_content, delta-based design)
- Step-by-step conversion recipe
- Python template code with examples

**Quick Example:**

```python
import uuid

from toolbrain_tracing.core.schema import ToolBrainAttributes, SpanType

def convert_my_agent_to_otlp(agent_data):
    spans = []
    parent_id = None
    for step in agent_data.steps:
        spans.append({
            "span_id": str(uuid.uuid4()),
            "parent_id": parent_id,  # Chain spans together
            "name": step.action,
            "attributes": {
                ToolBrainAttributes.SPAN_TYPE: SpanType.LLM_INFERENCE,
                ToolBrainAttributes.LLM_NEW_CONTENT: step.output,  # Delta content only
                ToolBrainAttributes.TOOL_NAME: step.tool_name,
            }
        })
        parent_id = spans[-1]["span_id"]
    return {"trace_id": agent_data.id, "spans": spans}
```

## 📁 Project Structure

```
toolbrain-tracing/
├── src/
│   ├── toolbrain_tracing/          # Main package
│   │   ├── api/v1/                 # FastAPI REST endpoints
│   │   ├── core/                   # TraceStore, schema, agent logic
│   │   ├── db/                     # Database session management
│   │   ├── sdk/                    # Client SDK
│   │   ├── static/                 # Frontend assets
│   │   ├── cli.py                  # CLI commands
│   │   ├── config.py               # Settings management
│   │   └── main.py                 # FastAPI app entry
│   └── examples/                   # Example implementations
│       ├── app.py                  # Streamlit admin UI
│       └── seed_tracestore_samples.py  # Sample data seeder
├── data/                           # Sample OTLP traces
│   └── ToolBrain OTLP Trace Samples/
├── docker/                         # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── README.md
├── docs/                           # Documentation
│   └── Converter.md
├── web/                            # React frontend (future)
├── pyproject.toml                  # Project metadata
└── README.md
```

## 🛠️ Development

### Running Tests

No automated test suite is included yet.

### Seeding Sample Data

```bash
cd src/examples

# SQLite (development)
python seed_tracestore_samples.py --backend sqlite

# PostgreSQL (Docker)
python seed_tracestore_samples.py \
    --backend postgresql \
    --db-url "postgresql://traceuser:tracepass@localhost:5432/tracedb" \
    --samples-dir "../../data/ToolBrain OTLP Trace Samples"
```

### Database Migrations

No migration tooling is included yet. For schema changes:

1. Update models in `src/toolbrain_tracing/db/base.py`
2. Recreate the database:
    - **SQLite (local):** delete `toolbrain_traces.db`, then run `toolbrain-trace init-db`
    - **PostgreSQL (Docker):** `docker compose -f docker/docker-compose.yml down -v` then `toolbrain-trace up`

### Working with JSONB Queries (PostgreSQL)

When querying JSONB fields:

```python
from sqlalchemy import func, cast
from sqlalchemy.dialects.postgresql import JSONB

# Extract text from JSONB
span_type = func.jsonb_extract_path_text(Span.attributes, "toolbrain.span.type")

# Cast for complex queries
rating = func.jsonb_extract_path_text(cast(Trace.feedback, JSONB), "rating")
```

## 📚 Documentation

- **[Building Your Own Trace Converter](docs/Converter.md)** - Complete guide for integrating custom agent frameworks
- **[Sample OTLP Traces](data/ToolBrain%20OTLP%20Trace%20Samples)** - Example trace files
- **[API Documentation](http://localhost:8000/docs)** - Interactive OpenAPI docs (when server is running)
- **[Docker Setup Guide](docker/README.md)** - Docker-specific instructions

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m 'Add amazing feature'`
5. Push to your fork: `git push origin feature/amazing-feature`
6. Open a Pull Request

**Development Guidelines:**
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation as needed
- Ensure Docker builds pass

## 🐛 Troubleshooting

### Docker changes not reflected

If code changes aren't picked up after `toolbrain-trace up --build`:

```bash
toolbrain-trace down
docker compose -f docker/docker-compose.yml build --no-cache
toolbrain-trace up
```

### PostgreSQL connection errors

Ensure PostgreSQL is running and check connection string in `src/toolbrain_tracing/config.py`:

```python
DATABASE_URL = "postgresql://traceuser:tracepass@localhost:5432/tracedb"
```

### Tool usage analytics showing incorrect data

After updating `store.py`, rebuild Docker containers to apply JSONB query fixes.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Database powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- UI with [Streamlit](https://streamlit.io/)
- Inspired by [OpenTelemetry](https://opentelemetry.io/) standards

---

**Made with ❤️ for the AI agent community**

For questions or support, please open an issue on GitHub.
