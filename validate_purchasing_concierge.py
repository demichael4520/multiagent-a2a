import sys
from google.cloud import aiplatform
from vertexai.preview.reasoning_engines import ReasoningEngine

PROJECT_ID = "ge-test-3p-only-2"
LOCATION = "us-central1"

# Initialize Vertex AI SDK
aiplatform.init(project=PROJECT_ID, location=LOCATION)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_purchasing_concierge.py <CONCIERGE_AGENT_ID>")
        sys.exit(1)
        
    agent_id = sys.argv[1]
    
    print(f"Loading agent: {agent_id}")
    agent = ReasoningEngine(agent_id)
    
    query = "I want to order 1 classic cheeseburger and 2 pepperoni pizzas."
    print(f"Querying agent with: '{query}'")
    
    try:
        response = agent.query(input=query, user_id="e2e_val_user")
        print("\n--- Response ---")
        print(response.get("output"))
        print("----------------")
    except Exception as e:
        print(f"Error querying agent: {e}")

if __name__ == "__main__":
    main()
