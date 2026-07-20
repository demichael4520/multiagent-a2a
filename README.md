# Multi-Agent Purchasing Concierge on Vertex AI Agent Runtime (ADK)

This project implements a multi-agent purchasing concierge system deployed on **Vertex AI Agent Runtime (Reasoning Engine)** using the Google **Agent Development Kit (ADK)**. 

It is adapted from the [A2A Purchasing Concierge Codelab](https://codelabs.developers.google.com/intro-a2a-purchasing-concierge?hl=en#1), shifting the target runtime from Cloud Run to Agent Runtime (Reasoning Engines) for enhanced integration with Google's agent platform.

## Architecture Overview

The system consists of three independent agents executing on separate Reasoning Engine runtimes:

```mermaid
graph TD
    Client[Client / Playground] -->|Query| Concierge[Purchasing Concierge <br> Root Agent]
    Concierge -->|GAPIC stream_query| BurgerAgent[Burger Seller Agent]
    Concierge -->|GAPIC stream_query| PizzaAgent[Pizza Seller Agent]
    BurgerAgent -->|Tool| CreateBurger[create_burger_order]
    PizzaAgent -->|Tool| CreatePizza[create_pizza_order]
```

1.  **Purchasing Concierge (Root Agent)**: Coordinates the purchasing flow. It receives the user's intent (e.g., ordering both burgers and pizzas), splits the request, programmatically queries the respective seller agents, aggregates their responses, and returns the final order confirmation.
2.  **Burger Seller Agent**: A specialized agent handling queries about the burger menu and executing order creation.
3.  **Pizza Seller Agent**: A specialized agent handling queries about the pizza menu and executing order creation.

---

## Technical Details & Workarounds

To support cross-agent communication on Vertex AI Agent Runtime, several platform limitations had to be addressed:

1.  **Custom Client-Side Call Routing**: Since Reasoning Engines do not expose public HTTP endpoints, ADK's native `RemoteA2aAgent` (which relies on standard A2A HTTP protocols and GET `/agent.json` cards) cannot be used directly. Instead, the Purchasing Concierge uses a **custom Python tool** (`send_task`) that routes queries programmatically via the **Vertex AI GAPIC streaming client** (`stream_query_reasoning_engine`).
2.  **Session Auto-Creation Monkey-Patch**: The ADK template (`AdkApp`) normally throws a `SessionNotFoundError` if a client queries it with a new `session_id`. Since the Concierge must propagate its session tracking, we **monkey-patch** `google.adk.runners.Runner` inside the seller agents at runtime to enforce `auto_create_session = True`.
3.  **Interactive Playground Compatibility**: ADK agents require multiple parameters (`message`, `user_id`) which conflict with the Google Cloud Console Playground's single-argument expectation. The Purchasing Concierge is wrapped in `PlaygroundCompatibleAdkAgent` to map playground payloads to ADK's internal streaming runner.

---

## Prerequisites

Ensure you have the following before starting:
*   A Google Cloud Project with the Vertex AI API enabled.
*   The `gcloud` CLI installed and authenticated.
*   Python 3.10+ environment with the Vertex AI SDK and ADK installed:
    ```bash
    pip install google-cloud-aiplatform[agent_engines] google-adk==1.31.1 pydantic cloudpickle
    ```

---

## Deployment Sequence

Deployment must follow a strict order because the Root Agent requires the Resource IDs of the Seller Agents at deployment time.

### Step 1: Deploy Seller Agents
Run the deployment script to deploy both the Burger and Pizza seller agents:
```bash
python deploy_sellers_adk.py
```
This script will:
1.  Package and deploy the Burger Agent to Agent Runtime.
2.  Package and deploy the Pizza Agent to Agent Runtime.
3.  Write the deployed Resource IDs to a local file named `seller_agents.env`.

### Step 2: Deploy Purchasing Concierge (Root Agent)
Run the deployment script for the Purchasing Concierge:
```bash
python deploy_concierge_adk.py
```
This script will:
1.  Read the Seller Agent Resource IDs from `seller_agents.env` and set them as environment variables inside the Concierge's container.
2.  Wrap the Concierge in the Playground compatibility helper.
3.  Deploy the Concierge to Agent Runtime and print its Resource ID.

---

## Querying the Root Agent

### 1. Google Cloud Console Playground (Interactive UI)
1. Go to the [Vertex AI Reasoning Engine Console](https://console.cloud.google.com/vertex-ai/reasoning-engines).
2. Click on the deployed **`purchasing-concierge-adk`** agent.
3. Use the right-hand **Test Agent** panel to chat directly.

### 2. Python SDK
```python
import vertexai
from vertexai.preview.reasoning_engines import ReasoningEngine

vertexai.init(project="ge-test-3p-only-2", location="us-central1")
agent = ReasoningEngine("YOUR_CONCIERGE_RESOURCE_ID")

response = agent.query(
    input="I want to order 1 classic cheeseburger and 2 pepperoni pizzas.",
    user_id="customer_1"
)
print(response.get("output"))
```

### 3. REST API via curl
To send a prompt using the REST API from your terminal, execute the following commands:

```bash
# 1. Get an authentication token
TOKEN=$(gcloud auth print-access-token)

# 2. Make the POST call to the query endpoint
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://us-central1-aiplatform.googleapis.com/v1beta1/projects/ge-test-3p-only-2/locations/us-central1/reasoningEngines/3258707823390883840:query \
  -d '{
    "input": {
      "input": "I want to order 1 classic cheeseburger and 2 pepperoni pizzas.",
      "user_id": "terminal_user"
    }
  }'
```
