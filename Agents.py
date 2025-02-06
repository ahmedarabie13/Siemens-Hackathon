import os
import json
from datetime import datetime

from crewai import Agent, Task, Crew, LLM, Process
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# 🔴 Ensure CrewAI Telemetry is Fully Disabled
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""  # Prevent OpenTelemetry timeout
os.environ["OPENAI_API_KEY"] = "sk-proj-1111"
os.environ["OPENAI_MODEL_NAME"] = "gpt-4"
os.environ["MISTRAL_API_KEY"] = "jIlcvnUbWBpWTT7f8jDOffD4ikTq19nR"
output_dir = "./ai-agent-output"

# Initialize the LLM using CrewAI's LLM interface with a Mistral model.
llm = LLM(
    # model="ollama/llama3.2",
    model="mistral/mistral-large-latest",
    # base_url="http://localhost:11434",
    temperature=0,
    # api_base="https://api.mistral.ai/v1/chat/completions",
    # role="user"  # Ensure this is correctly formatted
)


def save_to_file(data, filename):
    """
    Save JSON data to a file with timestamp.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{filename}_{timestamp}.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    print(f"✅ Saved output to {filepath}")
    return filepath

class RelevantAgents(BaseModel):
    agent_ids: list[str] = (
        Field(...,
              title="the ids of the agents that are relevant to the user query and could help in the implementation"))


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


def get_tasks(agents, query):
    """
    Dynamically create a list of tasks for each agent.
    """
    return [
        Task(
            # description=f"{agent.role} should respond to the user query {query} based on its expertise.",
            description="\n".join(
                [
                    f"{agent.role} should respond to the user query {query} based on its expertise reply as short as possible.",
                    "use the siemens product assigned for this agent and try to explain if applicable how this product will be helpful in the implementation of the user query",
                    "if you are not the first agent learn from the previous agent's output and try to provide a more detailed explanation only on your expertise",
                    "highlight in what part of the query your agent's product will be used",
                ]),
            # expected_output=f"Detailed explanation from the perspective of {agent.role}.",
            expected_output="\n".join(
                [f"Brief but complete explanation from the perspective of {agent.role} as short as possible.",
                 "highlight how your agent will be used in the implementation of the user query but make it as short as possible",
                 "use the previous agents output and change only the parts in your agent's expertise",
                 ]),
            agent=agent,
            output_file=os.path.join(output_dir, "final_results.txt")
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


def get_relevant_agents_ids(agents_data, data):
    """
    Runs the orchestrator to determine relevant agents with improved error handling.
    """
    orchestrator_agent = Agent(
        role="Orchestrator agent",
        goal="Understand the user's query and recommend which application(s) to use and why.",
        backstory="You are the connector, ensuring users understand the strengths of each application.",
        llm=llm,
        verbose=True
    )
    orchestrator_task_description = '\n'.join([
        f'Given this json data about the available agents: {json.dumps(agents_data)}',
        f"and Given this user query {data['message']}, recommend the most relevant agent(s) to handle the request.",
        "Determine which agent(s)'s products that could be used to help in the user query implementation.",
        "Return a list of the relevant agents ids."
    ])
    orchestrator_task = Task(
        description=orchestrator_task_description,
        expected_output="Determine which agent(s)'s product are most relevant to the user query and return a list of the relevant agents ids.",
        output_json=RelevantAgents,
        output_file=os.path.join(output_dir, "orchestrator_output.json"),
        agent=orchestrator_agent,
    )

    crew_obj = Crew(
        agents=[orchestrator_agent],
        tasks=[orchestrator_task],
        process=Process.sequential,
        verbose=True,
        # knowledge_sources=[orchestrator_knowledge_source]
    )

    raw_result = crew_obj.kickoff()
    # relevant_agents = RelevantAgents.parse_obj(raw_result)
    # print("Raw Crew Result:", relevant_agents.agent_ids)

    results = parse_or_wrap_json(raw_result.json)
    print("Orchestrator Results:", results)
    return results['agent_ids']


def run_orchestrator(data, agents_data) -> dict:
    """
    Original orchestrator task that returns the Crew's textual output as a JSON object.
    """
    os.makedirs(output_dir, exist_ok=True)
    # agents = get_agents(agents_data)
    # tasks = get_tasks(agents)

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
        orchestrator_task_description = '\n'.join([
            f'Given this json data about the available agents: {json.dumps(agents_data)}',
            f"and Given this user query {data['message']}, recommend the most relevant agent(s) to handle the request.",
            "Determine which agent(s)'s products that could be used to help in the user query implementation.",
            "Return a list of the relevant agents ids."
        ])
        orchestrator_task = Task(
            description=orchestrator_task_description,
            expected_output="Determine which agent(s)'s product are most relevant to the user query and return a list of the relevant agents ids.",
            output_json=RelevantAgents,
            output_file=os.path.join(output_dir, "orchestrator_output.json"),
            agent=orchestrator_agent,
        )

        crew_obj = Crew(
            agents=[orchestrator_agent],
            tasks=[orchestrator_task],
            process=Process.sequential,
            verbose=True,
            # knowledge_sources=[orchestrator_knowledge_source]
        )

        raw_result = crew_obj.kickoff()
        # relevant_agents = RelevantAgents.parse_obj(raw_result)
        # print("Raw Crew Result:", relevant_agents.agent_ids)

        results = parse_or_wrap_json(raw_result.json)
        print("Orchestrator Results:", results)
        agent_ids = results['agent_ids']
        # print('Agents Data: ', agents_data)
        relevant_agents_data = []
        for agent_data in agents_data:
            if agent_data['_id'] in agent_ids:
                print("Relevant Agent Data:", agent_data['_id'])
                relevant_agents_data.append(agent_data)

        # siemens_agents = get_agents([agent_data if agent_data['_id'] in agent_ids else None for agent_data in agents_data])
        siemens_agents = get_agents(relevant_agents_data)
        print("Siemens Agents num:", len(siemens_agents))
        if siemens_agents:
            manager = Agent(
                role="Project Manager",
                goal="Efficiently manage the crew and ensure high-quality task completion",
                backstory="You're an experienced project manager, skilled in overseeing complex projects and guiding teams to success. Your role is to coordinate the efforts of the crew members, ensuring that each task is completed on time and to the highest standard.",
                allow_delegation=True,
                llm=llm,
            )

            print("Siemens Agents is here")
            siemens_agents_tasks = get_tasks(siemens_agents, data['message'])
            # heeds_pds_docs = PDFKnowledgeSource("dependencies/HEEDS MDO.pdf")
            siemens_agent_crew = Crew(
                agents=siemens_agents,
                tasks=siemens_agents_tasks,
                verbose=True,
            )
            final_results = siemens_agent_crew.kickoff()
            print('Final Results:', final_results)

            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # filename = f"final_results_{timestamp}.json"
            # with open(filename, "w") as file:
            #     # file.write(parse_or_wrap_json(final_results))
            #     json.dump(parse_or_wrap_json(final_results), file, indent=4)
            return parse_or_wrap_json(final_results)
        else:
            print("Siemens Agents is none")
            return {"error": "No relevant agents found."}

        # print("Raw Crew Result:", raw_result.get('agent_ids'))
        # print('ids: ', results['agent_ids'])

    except Exception as e:
        print("Error occurred:", str(e))
        return {"error": str(e)}




def run_flow_agent(data, agents_results=None) -> dict:
    """
    Generates a hierarchical React Flow graph dynamically based on relevant Siemens agents.
    - Uses agent responses to determine workflow dependencies.
    - Outputs a structured React Flow JSON graph.
    """
    print("📥 Received Task Data:", data.get("message"))

    if "message" not in data:
        return {"error": "Missing 'message' in input data."}

    try:
        # Ensure we have agent results; otherwise, return an error
        if not agents_results or not isinstance(agents_results, dict):
            return {"error": "Invalid or missing agent results."}

        print("✅ Received Agents Results:", json.dumps(agents_results, indent=2))

        # Step 1: Define Flow Orchestrator Agent
        flow_orchestrator_agent = Agent(
            role="Flow Orchestrator Agent",
            goal=(
                "Generate a hierarchical React Flow JSON representing dependencies between agents. "
                "Ensure structured JSON output with clear parent-child relationships."
            ),
            backstory="You specialize in structuring workflows based on agent interactions and dependencies.",
            llm=llm,
            verbose=True
        )

        # Step 2: Define React Flow Diagram Task
        flow_task = Task(
            description=f"""
            Based on the Siemens agent results:
            {json.dumps(agents_results, indent=2)}

            User Query: "{data['message']}"

            **TASK:**
            - **Generate a structured React Flow JSON** showing dependencies between agents.
            - Each **agent must be a node** with:
                - `id`: Unique string
                - `data.label`: The agent's role
                - `position.x, position.y`: Auto-calculated for hierarchy
                - `level`: Depth in the hierarchy (1 = top, increasing downwards)
            - **Edges must represent dependencies** between agents:
                - `source`: Parent node
                - `target`: Child node

            🔹 **STRICT OUTPUT RULES:**
            - MUST return **ONLY JSON** (no extra text).
            - **DO NOT** use markdown (` ```json `) formatting.
            - **DO NOT** include explanations or commentary.

            🔹 **VALID JSON STRUCTURE:**
            {{
              "nodes": [
                {{
                  "id": "unique_id",
                  "data": {{
                    "label": "Agent Role"
                  }},
                  "position": {{
                    "x": x_coordinate,
                    "y": y_coordinate
                  }},
                  "level": hierarchical_level
                }}
              ],
              "edges": [
                {{
                  "id": "edge_id",
                  "source": "parent_node_id",
                  "target": "child_node_id"
                }}
              ]
            }}
            """,
            expected_output="A structured React Flow JSON with 'nodes' and 'edges'.",
            agent=flow_orchestrator_agent
        )

        # Step 3: Run Crew for React Flow Diagram Generation
        flow_crew = Crew(
            agents=[flow_orchestrator_agent],
            tasks=[flow_task],
            process=Process.sequential,
            verbose=True
        )

        raw_flow_result = flow_crew.kickoff()

        # Step 4: Parse & Validate JSON Output
        flow_parsed_results = parse_or_wrap_json(raw_flow_result)

        if not flow_parsed_results.get("nodes") or not flow_parsed_results.get("edges"):
            return {"error": "Failed to generate valid workflow hierarchy"}

        # Step 5: Save JSON results for debugging/logging
        save_to_file(flow_parsed_results, "flow_hierarchy_results")

        return flow_parsed_results

    except Exception as e:
        print("❌ Error occurred:", str(e))
        return {"error": str(e)}