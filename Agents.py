import os
import json
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# 🔴 Ensure CrewAI Telemetry is Fully Disabled
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""  # Prevent OpenTelemetry timeout
os.environ["OPENAI_API_KEY"] = "sk-proj-1111"
os.environ["OPENAI_MODEL_NAME"] = "gpt-4"

# Define LLM with Ollama's endpoint
llm = ChatOpenAI(
    model="ollama/llama3.2",
    base_url="http://localhost:11434"
)

# Load predefined agents from JSON file
AGENTS_JSON_FILE = "predefined_agents.json"



# Create agents dynamically

def get_agents(agents):
    print(agents)
    agents_list = [
        Agent(
            role=agent["role"],
            goal=agent["goal"],
            backstory=agent["backstory"],
            llm=llm
        ) for agent in agents
    ]

    return agents_list




def run_orchestrator(data, agents):

    siemens_agents= get_agents(agents)
    print("Received Task Data:", data["description"])

    if "description" not in data:
        return

    try:
        orchestrator_agent = Agent(
            role="Orchestrator agent",
            goal="Understand the user's query and recommend which application(s) to use and why.",
            backstory="You are the connector, ensuring users understand the strengths of each application.",
            llm=llm
        )

        user_task = Task(
            description=data["description"],
            expected_output=data["expected_output"],
            agent=orchestrator_agent,
            llm=llm
        )

        # ✅ Fix: Ensure the agent list is correctly formatted
        crew = Crew(
            agents=[orchestrator_agent] + siemens_agents,  # Fix list structure
            tasks=[user_task],
            verbose=True
        )

        result = crew.kickoff()
        print("Crew Result:", result)
        result_data = str(result)
        print(result)
        return result

    except Exception as e:
        print("Error occurred:", str(e))
        return

