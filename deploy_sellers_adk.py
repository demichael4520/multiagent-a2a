import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines
import os

PROJECT_ID = "ge-test-3p-only-2"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://cloud-ai-platform-4b9e1436-0660-427d-be6d-5ce6712f87a1"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

# Custom AdkApp to enable auto_create_session in runners
class AutoCreateSessionAdkApp(reasoning_engines.AdkApp):
    def set_up(self):
        print("AutoCreateSessionAdkApp.set_up() called!")
        super().set_up()
        if "runner" in self._tmpl_attrs:
            self._tmpl_attrs["runner"].auto_create_session = True
            print("Set runner.auto_create_session = True")
        if "in_memory_runner" in self._tmpl_attrs:
            self._tmpl_attrs["in_memory_runner"].auto_create_session = True
            print("Set in_memory_runner.auto_create_session = True")

# Import ADK agents
from remote_seller_agents.burger_agent.agent_adk import burger_agent as burger_adk_agent
from remote_seller_agents.pizza_agent.agent_adk import pizza_agent as pizza_adk_agent

# Deploy Burger Agent
print("Deploying Burger Agent to Agent Runtime...")
burger_app = AutoCreateSessionAdkApp(
    agent=burger_adk_agent,
    env_vars={
        "GOOGLE_GENAI_USE_VERTEXAI": "true",
        "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
        "GOOGLE_CLOUD_LOCATION": LOCATION,
    }
)
deployed_burger = agent_engines.create(
    agent_engine=burger_app,
    display_name="burger-seller-agent-adk",
    requirements=[
        "google-cloud-aiplatform[agent_engines]",
        "google-adk==1.31.1",
    ],
    extra_packages=["./remote_seller_agents"],
)
print(f"Burger Agent deployed: {deployed_burger.resource_name}")

# Deploy Pizza Agent
print("Deploying Pizza Agent to Agent Runtime...")
pizza_app = AutoCreateSessionAdkApp(
    agent=pizza_adk_agent,
    env_vars={
        "GOOGLE_GENAI_USE_VERTEXAI": "true",
        "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
        "GOOGLE_CLOUD_LOCATION": LOCATION,
    }
)
deployed_pizza = agent_engines.create(
    agent_engine=pizza_app,
    display_name="pizza-seller-agent-adk",
    requirements=[
        "google-cloud-aiplatform[agent_engines]",
        "google-adk==1.31.1",
    ],
    extra_packages=["./remote_seller_agents"],
)
print(f"Pizza Agent deployed: {deployed_pizza.resource_name}")

# Save the IDs to a file
with open("seller_agents.env", "w") as f:
    f.write(f"BURGER_SELLER_AGENT_ID={deployed_burger.name}\n")
    f.write(f"PIZZA_SELLER_AGENT_ID={deployed_pizza.name}\n")
print("Saved agent IDs to seller_agents.env")
