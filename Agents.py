import os
import json
from crewai import Agent, Task, Crew, LLM

# 🔴 Ensure CrewAI Telemetry is Fully Disabled
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""  # Prevent OpenTelemetry timeout
os.environ["OPENAI_API_KEY"] = "sk-proj-1111"
os.environ["OPENAI_MODEL_NAME"] = "gpt-4"
os.environ["MISTRAL_API_KEY"] = "jIlcvnUbWBpWTT7f8jDOffD4ikTq19nR"

# Initialize the LLM using CrewAI's LLM interface with a Mistral model.
llm = LLM(
    model="mistral/mistral-large-latest",
    temperature=0.1
)


def get_agents(agents_data):
    """
    Convert a list of agent configuration dictionaries into Agent objects.
    """
    return [
        Agent(
            role=agent["role"],
            goal=agent["goals"],
            backstory=agent["backstory"],
            llm=llm,
            verbose=True
        ) for agent in agents_data
    ]


def get_tasks(agents):
    """
    Dynamically create a list of tasks for each agent.
    """
    return [
        Task(
            description=f"{agent.role} should respond to the user query based on its expertise.",
            expected_output=f"Detailed explanation from the perspective of {agent.role}.",
            agent=agent,
            llm=llm,
            verbose=True
        ) for agent in agents
    ]


def clean_json_output(raw_output: str) -> str:
    """
    Clean the raw output from the agent by removing markdown code fences and extra whitespace.
    """
    cleaned = raw_output.strip()
    # Remove markdown code fences if present.
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
    return cleaned


def parse_or_wrap_json(raw_result) -> dict:
    """
    Attempt to parse raw_result (converted to a string) as JSON.
    If parsing fails, wrap it in a dictionary under the key 'result'.
    """
    raw_str = str(raw_result)
    cleaned = clean_json_output(raw_str)
    try:
        return json.loads(cleaned)
    except Exception as parse_err:
        print("Error parsing output as JSON:", str(parse_err))
        # If parsing fails, return the cleaned string in a JSON object.
        return {"result": cleaned}


def run_orchestrator(data, agents_data) -> dict:
    """
    Original orchestrator task that returns the Crew's textual output as a JSON object.
    """
    agents = get_agents(agents_data)
    tasks = get_tasks(agents)

    print("Received Task Data:", data.get("message"))

    if "message" not in data:
        return {"error": "Missing 'message' in input data."}

    try:
        orchestrator_agent = Agent(
            role="Orchestrator agent",
            goal="Understand the user's query and recommend which application(s) to use and why.",
            backstory="You are the connector, ensuring users understand the strengths of each application.",
            llm=llm,
            verbose=True
        )

        orchestrator_task = Task(
            description=data["message"],
            expected_output="Determine which applications are relevant and explain their contributions.",
            agent=orchestrator_agent,
            llm=llm,
            verbose=True
        )

        crew_obj = Crew(
            agents=[orchestrator_agent] + agents,
            tasks=[orchestrator_task] + tasks,
            verbose=True
        )

        raw_result = crew_obj.kickoff()
        print("Raw Crew Result:", raw_result)

        return parse_or_wrap_json(raw_result)

    except Exception as e:
        print("Error occurred:", str(e))
        return {"error": str(e)}


def run_flow_agent(data, agents_data) -> dict:
    """
    New orchestrator-like function that instructs the agent to return a React Flow graph.
    It expects the agent to output a JSON string with 'nodes' and 'edges'.
    """
    agents = get_agents(agents_data)
    tasks = get_tasks(agents)

    print("Received Task Data:", data.get("message"))

    if "message" not in data:
        return {"error": "Missing 'message' in input data."}

    try:
        flow_orchestrator_agent = Agent(
            role="Flow Orchestrator agent",
            goal=(
                "Generate a React Flow graph that represents the applications needed. "
                "Return a JSON object with two keys: 'nodes' and 'edges'. "
                "Each node must include an 'id', a 'data' dict with a 'label', and a 'position'. "
                "Each edge must include an 'id', 'source', and 'target'. "
                "Return only the JSON object without any markdown formatting or commentary."
            ),
            backstory="You are the central orchestrator. Your output must be valid JSON.",
            llm=llm,
            verbose=True
        )

        flow_task = Task(
            description=data["message"],
            expected_output=(
                "Return a JSON object with 'nodes' and 'edges' keys defining a React Flow graph."
            ),
            agent=flow_orchestrator_agent,
        )

        crew_obj = Crew(
            agents=[flow_orchestrator_agent] + agents,
            tasks=[flow_task] + tasks,
            verbose=True
        )

        raw_result = crew_obj.kickoff()
        print("Raw Crew Result:", raw_result)

        return parse_or_wrap_json(raw_result)

    except Exception as e:
        print("Error occurred:", str(e))
        return {"error": str(e)}


