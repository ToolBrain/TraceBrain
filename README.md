# TraceBrain: An Open-Source Framework for Agentic Trace Management 🧠🚀

**TraceBrain** is an open-source platform for collecting, managing, and analyzing execution traces from LLM agents.

The system standardizes heterogeneous agent logs into a unified trace format, enabling consistent inspection, evaluation, and downstream analysis across different frameworks.

By organizing historical traces as structured artifacts, TraceBrain supports agent observability, human oversight, and iterative improvement of agent workflows.

## ✨ Key Features

### 📥 Ingestion Layer (Standardization)
- **Standardized Trace Format**: Capture agent workflows using a unified OTLP-based schema.
- **Framework-Agnostic Integration**: Lightweight SDK and converters support agents built with various frameworks (e.g., LangChain, SmolAgents) or custom implementations.
- **Delta-based Tracing**: Stores only incremental context updates (`new_content`) to reduce redundant prompt storage.

### 🛡️ Governance Layer (Human-in-the-loop)
- **Active Help Request**: Allows agents to escalate uncertain decisions to human experts during execution.
- **Command Center UI**: Visualize multi-step agent traces and enable expert inspection and feedback.
- **Semi-Automated Evaluation**: An AI Judge generates draft evaluations (e.g., `rating`, `confidence`, `error_type`, and `feedback`) that experts can review and finalize.

### 🧠 Cognitive Layer (Trace-driven Learning)
- **Experience Retrieval**: Agents can query past successful trajectories to guide reasoning via in-context learning.
- **Automated Curriculum Generation**: Using error classifications produced by the AI Judge, a Curator agent analyzes clustered failure traces and synthesizes targeted training tasks.
- **Semantic Trace Search**: Vector-based retrieval (via `pgvector`) for locating similar reasoning trajectories.

## 🏗️ Architecture

![System Architecture](images/system_architecture.jpg)

- **Your AI Agent:** Any agent framework. Uses the TraceClient SDK to send data.
- **TraceStore API:** The central FastAPI server. Ingests, stores, and serves trace data.
- **Database:** The persistence layer (PostgreSQL or SQLite).
- **Admin Panel UI:** A React client in `web/` that consumes the TraceStore API.

**Tech Stack:**
- **Backend**: FastAPI, SQLAlchemy 2.0, Pydantic V2
- **Database**: PostgreSQL (production), SQLite (development), pgvector (semantic search)
- **Frontend**: React (Vite + MUI) in `web/`
- **Deployment**: Docker Compose
- **AI Integration**: LibrarianAgent + AI Judge + Curriculum Curator with multi-provider LLM support
- **Embeddings**: sentence-transformers (local) or OpenAI/Gemini (cloud)

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.8+ (for local development)
- PostgreSQL 15+ (if running without Docker)

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/ToolBrain/TraceBrain.git
   cd TraceBrain
   ```

2. **Start the services**
   ```bash
   # Install the CLI tool
   pip install -e .
   
    # Start PostgreSQL + API server (multi-stage build bundles frontend)
   tracebrain-trace up
   ```

3. **Access the services**
    - Frontend UI: http://localhost:8000/
    - API: http://localhost:8000/api/v1/
    - API Docs: http://localhost:8000/docs

4. **Seed sample data** (optional)
   ```bash
    # Data is auto-seeded once on first start (Docker only).
    # If you want to re-seed, remove the volume then bring it up again:
    docker compose -f docker/docker-compose.yml down -v
    tracebrain-trace up
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
    # Optional local embeddings
    # pip install -e .[embeddings-local]
    ```

3. **Run the API server** (SQLite mode)
    ```bash
    tracebrain-trace init-db
    tracebrain-trace start
    ```

4. **Run the React frontend**
    ```bash
    cd web
    npm install
    npm run dev
    ```

## 📖 Usage

### CLI Commands

```bash
# Start Docker services
tracebrain-trace up

# Start with rebuild (after code changes)
tracebrain-trace up --build

# Stop services
tracebrain-trace down

# Manual Docker rebuild (if changes aren't picked up)
docker compose -f docker/docker-compose.yml build --no-cache
```

### API Endpoints

## Concepts

- **Trace**: A single execution attempt (an "experiment").
- **Episode**: A logical group of traces (attempts) aimed at solving a single user task.

**Traces**
- `POST /api/v1/traces` - Create a new trace
- `POST /api/v1/traces/init` - Initialize a trace before spans are available
- `GET /api/v1/traces` - List all traces
- `GET /api/v1/traces/{trace_id}` - Get trace details
- `POST /api/v1/traces/{trace_id}/feedback` - Add feedback to a trace

**Episodes**
- `GET /api/v1/episodes` - List all episodes along with their full traces
- `GET /api/v1/episodes/summary` - List episodes with aggregated metrics
- `GET /api/v1/episodes/{episode_id}` - Get episode details with trace summaries
- `GET /api/v1/episodes/{episode_id}/traces` - Get all full traces in an episode

**Analytics**
- `GET /api/v1/stats` - Get overall statistics
- `GET /api/v1/analytics/tool_usage` - Get tool usage analytics

**Natural Language Queries**
- `POST /api/v1/natural_language_query` - Query traces with natural language
    - Requires LLM configuration via env vars (for example: `LLM_PROVIDER`, `LLM_API_KEY`)
    - Supports `session_id` for chat memory and returns `suggestions`
- `GET /api/v1/librarian_sessions/{session_id}` - Load stored chat history

**AI Evaluation**
- `POST /api/v1/ai_evaluate/{trace_id}` - Evaluate a trace with a judge model
- `POST /api/v1/ops/batch_evaluate` - Run AI judge over recent traces missing `tracebrain.ai_evaluation`
- `POST /api/v1/traces` triggers background evaluation when no AI draft exists

**Operations**
- `DELETE /api/v1/ops/traces/cleanup` - Delete traces that match cleanup filters

**Semantic Search**
- `GET /api/v1/traces/search` - Find similar traces using vector similarity

**Governance Signals**
- `POST /api/v1/traces/{trace_id}/signal` - Update trace status/priority

**Curriculum**
- `POST /api/v1/curriculum/generate` - Generate tasks from failed/low-rated traces
- `GET /api/v1/curriculum` - List pending curriculum tasks
- `GET /api/v1/curriculum/export` - Export curriculum tasks as JSONL
- `DELETE /api/v1/curriculum/{task_id}` - Delete a curriculum task
- `DELETE /api/v1/curriculum` - Delete all curriculum tasks
- `PATCH /api/v1/curriculum/{task_id}/complete` - Mark a curriculum task as complete
- `PATCH /api/v1/curriculum/complete` - Mark all curriculum tasks as complete

**Exports**
- `GET /api/v1/export/traces` - Export raw OTLP traces as JSONL

**History**
- `GET /api/v1/history` - Retrieve history of viewed traces and episodes
- `POST /api/v1/history` - Add or update last time trace or episode was viewed
- `DELETE /api/v1/history` - Clear all traces and episodes in viewed history

**Settings**
- `GET /api/v1/settings` - Retrieve current TraceBrain settings
- `POST /api/v1/settings` - Update TraceBrain settings

### Trace Status and Needs Review

Trace status is stored in both the database column `status` and in
`attributes.tracebrain.trace.status` for UI and API consistency.

**Supported statuses:**

- `running` - Trace is in progress or not finalized.
- `completed` - Trace has been reviewed and finalized.
- `needs_review` - Trace requires human attention.
- `failed` - Trace is marked as failed.

**When `needs_review` is set:**

- **Agent Signal:** The agent calls `request_human_intervention` (Active Help Request).
- **AI Judgment:** `tracebrain.ai_evaluation.confidence` < 0.75, or
    `tracebrain.ai_evaluation.error_type` is one of:
    `logic_loop`, `hallucination`, `invalid_tool_usage`, `tool_execution_error`,
    `format_error`, `misinterpretation`, `context_overflow`.
- **System Error:** Any span has `otel.status_code` = `ERROR`.

### Configuration (LLM + Embeddings)

Core environment variables:

```bash
# LLM (Librarian, Judge, Curator)
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=your-key

# Embeddings (semantic search)
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

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
                "tracebrain.span.type": "user_request",
                "tracebrain.content.new_content": "What's the stock price of NVIDIA?"
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

### React Frontend

The admin UI provides:
- **Trace Browser**: View all traces with filters
- **Trace Details**: Expandable span tree visualization and compare related traces
- **Feedback Form**: Rate and tag traces
- **Analytics Dashboard**: Stats, tool usage charts
- **AI Librarian**: Session-aware chat with suggestions and history restore
- **AI Evaluation**: AI draft is auto-generated and experts verify or edit before finalizing
- **Governance Signal**: Mark traces with status and priority
- **Curriculum**: Generate and review training tasks

Frontend dev server (local development only):

```bash
cd web
npm install
npm run dev
```

### Embeddings and Semantic Search

Configure embeddings for vector search and experience retrieval:

```bash
# local (default)
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2

# cloud (OpenAI/Gemini)
EMBEDDING_PROVIDER=openai
EMBEDDING_API_KEY=your-key
EMBEDDING_MODEL=text-embedding-3-small

# optional for OpenAI-compatible endpoints
EMBEDDING_BASE_URL=https://your-endpoint/v1
```

## 🔌 Integration with Your Agent

### Using the TraceStore Client (read/query)

This section focuses on read/query operations. For logging traces, see the
`trace_scope` section below.

```python
import json

from tracebrain.sdk.client import TraceClient, TraceScope

client = TraceClient(base_url="http://localhost:8000")

# Query traces
traces = client.list_traces()

# Export traces as JSONL
jsonl_payload = client.export_traces(min_rating=4, limit=100)

# Parse JSONL into Python objects
trace_items = [json.loads(line) for line in jsonl_payload.splitlines() if line.strip()]

# Reconstruct messages or turns from OTLP
trace_data = client.get_trace("my-trace-001")

# to_messages: rebuilds chat message list (role/content) from spans
messages = TraceScope.to_messages(trace_data)
# Example: messages[:2] -> [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

# to_turns: groups messages into conversation turns for UI/analysis
turns = TraceScope.to_turns(trace_data)
# Example: turns[0] -> {"user": "...", "assistant": "..."}

# to_tracebrain_turns: returns TraceBrain-native turn objects with metadata
tracebrain_turns = TraceScope.to_tracebrain_turns(trace_data)
# Example: tracebrain_turns[0] -> {"turn_id": "...", "messages": [...], "span_ids": [...]} 
```

### Trace Init and trace_scope (recommended for all runs)

Use `trace_scope` for every agent run you plan to log. It pre-registers a trace
via `/api/v1/traces/init`, sets the trace ID in a context-local store (safe for
async and multi-thread usage), and uploads the trace when the scope exits. This
is required if your agent might call `request_human_intervention` (Active Help
Request) so the help signal is attached to the correct trace.

**Recommended: use `trace_scope` (auto init + auto log)**

```python
from tracebrain import TraceClient
from my_converters import convert_smolagent_to_otlp

client = TraceClient(base_url="http://localhost:8000")

with client.trace_scope(system_prompt="You are a helpful assistant") as trace:
    agent = MyAgent(system_prompt="You are a helpful assistant")
    agent.run("Summarize this report")

    otlp_trace = convert_smolagent_to_otlp(agent)
    trace["spans"] = otlp_trace.get("spans", [])
```

**Advanced: manual trace ID + manual log**

```python
from tracebrain import TraceClient
from tracebrain.sdk.trace_context import set_trace_id, get_trace_id
from my_converters import convert_smolagent_to_otlp

client = TraceClient(base_url="http://localhost:8000")
set_trace_id("trace_123")

agent = MyAgent(system_prompt="You are a helpful assistant")
agent.run("Summarize this report")

otlp_trace = convert_smolagent_to_otlp(agent)
otlp_trace["trace_id"] = get_trace_id() or "trace_123"
client.log_trace(otlp_trace)
```

### Agent Tools (Experience Retrieval + Active Help Request)

When to use:

- Use `search_past_experiences` to fetch high-quality, previously successful traces for similar tasks.
- Use `search_similar_traces` when you need semantic similarity over trace content.
- Use `request_human_intervention` when the agent is blocked, uncertain, or needs clarification.

```python
from tracebrain.sdk import (
    search_past_experiences,
    search_similar_traces,
    request_human_intervention,
)

# Retrieve prior successful experiences
experiences = search_past_experiences("resolve a tool error", min_rating=4, limit=3)

# Semantic search over traces
similar = search_similar_traces("multi-step planning", min_rating=4, limit=3)

# Escalate to human when the agent is blocked
help_request = request_human_intervention("User request is ambiguous, need clarification")
```

### Building a Custom Converter

TraceBrain uses the **TraceBrain OTLP (OpenTelemetry Protocol) format** - a delta-based trace schema with parent_id chains for conversation reconstruction.

See [docs/Converter.md](docs/Converter.md) for:
- OTLP schema explanation (parent_id, new_content, delta-based design)
- Step-by-step conversion recipe
- Python template code with examples

**Quick Example:**

```python
import uuid

from tracebrain.core.schema import TraceBrainAttributes, SpanType

def convert_my_agent_to_otlp(agent_data):
    spans = []
    parent_id = None
    for step in agent_data.steps:
        spans.append({
            "span_id": str(uuid.uuid4()),
            "parent_id": parent_id,  # Chain spans together
            "name": step.action,
            "attributes": {
                TraceBrainAttributes.SPAN_TYPE: SpanType.LLM_INFERENCE,
                TraceBrainAttributes.LLM_NEW_CONTENT: step.output,  # Delta content only
                TraceBrainAttributes.TOOL_NAME: step.tool_name,
            }
        })
        parent_id = spans[-1]["span_id"]
    return {"trace_id": agent_data.id, "spans": spans}
```

## 📁 Project Structure

```
TraceBrain/
├── src/
│   ├── tracebrain/          # Main package
│   │   ├── api/v1/                 # FastAPI REST endpoints
│   │   │   ├── ai_features.py      # AI evaluation + librarian endpoints
│   │   │   ├── api_router.py       # Main v1 router
│   │   │   ├── common.py           # Shared store/helpers
│   │   │   ├── curriculum.py       # Curriculum endpoints
│   │   │   ├── episodes.py         # Episode endpoints
│   │   │   ├── operations.py       # Ops + analytics endpoints
│   │   │   ├── system.py           # Root, health, settings, history
│   │   │   ├── traces.py           # Trace endpoints
│   │   │   └── schemas/            # Shared Pydantic models
│   │   │       └── api_models.py
│   │   ├── core/                   # TraceStore, schema, agent logic
│   │   ├── db/                     # Database session management
│   │   ├── sdk/                    # Client SDK
│   │   ├── static/                 # Frontend assets
│   │   ├── cli.py                  # CLI commands
│   │   ├── config.py               # Settings management
│   │   └── main.py                 # FastAPI app entry
│   └── examples/                   # Example implementations
│       └── seed_tracestore_samples.py  # Sample data seeder
├── data/                           # Sample OTLP traces
│   └── TraceBrain OTLP Trace Samples/
├── docker/                         # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── README.md
├── docs/                           # Documentation
│   └── Converter.md
├── web/                            # React frontend
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
    --samples-dir "../../data/TraceBrain OTLP Trace Samples"
```

### Database Migrations

No migration tooling is included yet. For schema changes:

1. Update models in `src/tracebrain/db/base.py`
2. Recreate the database:
    - **SQLite (local):** delete `tracebrain_traces.db`, then run `tracebrain-trace init-db`
    - **PostgreSQL (Docker):** `docker compose -f docker/docker-compose.yml down -v` then `tracebrain-trace up`

### Working with JSONB Queries (PostgreSQL)

When querying JSONB fields:

```python
from sqlalchemy import func, cast
from sqlalchemy.dialects.postgresql import JSONB

# Extract text from JSONB
span_type = func.jsonb_extract_path_text(Span.attributes, "tracebrain.span.type")

# Cast for complex queries
rating = func.jsonb_extract_path_text(cast(Trace.feedback, JSONB), "rating")
```

## 📚 Documentation

- **[Building Your Own Trace Converter](docs/Converter.md)** - Complete guide for integrating custom agent frameworks
- **[Trace Reconstruction Guide](docs/Reconstructor.md)** - Rebuild full context from delta traces for training
- **[Sample OTLP Traces](data/TraceBrain%20OTLP%20Trace%20Samples)** - Example trace files
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

If code changes aren't picked up after `tracebrain-trace up --build`:

```bash
tracebrain-trace down
docker compose -f docker/docker-compose.yml build --no-cache
tracebrain-trace up
```

### PostgreSQL connection errors

Ensure PostgreSQL is running and check connection string in `src/tracebrain/config.py`:

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
