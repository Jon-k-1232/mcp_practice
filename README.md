# MCP Rally Server

A minimal Model Context Protocol-style server that connects to CA Rally (Agile Central), fetches
defect data, and surfaces analytics around potential root causes and trends.

## Features

-  FastAPI service exposing `/defects` and `/defects/analysis` endpoints requiring a `workspace`
   query parameter and optional per-call project overrides.
-  Configurable through environment variables loaded from `.env`.
-  Modular code structure splitting auth, client, and analytics logic.
-  Heuristic analysis to highlight leading contributors and suspected causes.

## Getting Started

1. **Create a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -e .
   ```

3. **Configure Rally credentials**

   Update the `.env` file with your Rally details:

   -  `RALLY_API_KEY` – Rally personal API key.
   -  `RALLY_BASE_URL` – Rally instance base URL (defaults to `https://rally1.rallydev.com`).
   -  `RALLY_PAGE_SIZE` – Page size for Rally queries (defaults to `2000`).

4. **Run the server**

   ```bash
   python scripts/run_server.py
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000) with an OpenAPI UI at
   `/docs`.

## Project Layout

-  `src/mcp_rally/config.py` – Loads environment configuration.
-  `src/mcp_rally/auth/` – Authentication helpers (e.g., Rally API headers).
-  `src/mcp_rally/rally_client.py` – Handles REST calls to Rally.
-  `src/mcp_rally/analysis/defects.py` – Aggregates and analyzes defect data.
-  `src/mcp_rally/server.py` – FastAPI application exposing MCP endpoints.
-  `scripts/run_server.py` – Convenience launcher for the server.
-  `terraform/` – Infrastructure-as-code for dev and prod AWS environments.

## Terraform Deployment

-  Update `terraform/dev/terraform.tfvars` (and the prod equivalent) with your VPC, subnet,
   certificate, and container image details before applying.
-  From the desired environment directory run:

  ```bash
  cd terraform/dev
  terraform init
  terraform plan
  terraform apply
  ```

-  Push your Docker image to the provisioned ECR repo using the value output as `ecr_repository_url`.

## Next Steps

-  Add persistence or caching for frequent analyses.
-  Expand analytics heuristics with organization-specific insights.
-  Write automated tests against mocked Rally responses.
