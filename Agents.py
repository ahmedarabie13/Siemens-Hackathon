import os
import json
import re
from datetime import datetime
from pathlib import Path

from crewai import Agent, Task, Crew, LLM, Process
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
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
    model="mistral/pixtral-large-latest",
    # base_url="http://localhost:11434",
    temperature=0
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


# pdf_source = PDFKnowledgeSource(
#     file_paths='HEEDS MDO.pdf',
#     description="Documentation of HEEDS MDAO Product"
# )
text_file_source = TextFileKnowledgeSource(
    file_paths='results_formatted_example.txt'
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
    Ensures Mistral's output is a clean, valid JSON string.
    """
    cleaned = raw_output.strip()

    # Remove markdown code blocks if present
    cleaned = re.sub(r"```json|```", "", cleaned, flags=re.MULTILINE).strip()

    # Check if output is valid JSON
    try:
        json.loads(cleaned)  # Validate JSON
        return cleaned
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        return '{"error": "Invalid JSON format"}'


def parse_or_wrap_json(raw_result) -> dict:
    """
    Parses Mistral's output into JSON. If invalid, wraps it in a dictionary.
    """
    cleaned = clean_json_output(str(raw_result))
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw_output": cleaned}
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
            format_agent = create_format_agent()
            format_task = create_format_task(format_agent)
            siemens_agent_crew = Crew(
                agents=siemens_agents + [format_agent],
                tasks=siemens_agents_tasks + [format_task],
                process=Process.sequential,
                verbose=True,
                knowledge_sources=[text_file_source,
                                   # pdf_source,
                                   ]
            )
            final_results = siemens_agent_crew.kickoff()
            print('Final Results:', final_results)
            return parse_or_wrap_json(final_results)
        else:
            print("Siemens Agents is none")
            return {"error": "No relevant agents found."}


    except Exception as e:
        print("Error occurred:", str(e))
        return {"error": str(e)}

def run_flow_agent(data, agents_results) -> dict:
    """
    Generates a hierarchical React Flow graph dynamically based on relevant Siemens agents.
    - Uses agent responses to determine workflow dependencies.
    - Outputs a structured React Flow JSON graph.
    """
    print("📥 Received Task Data:", data.get("message"))

    if "message" not in data:
        return {"error": "Missing 'message' in input data."}

    try:
        if not agents_results or not isinstance(agents_results, dict):
            return {"error": "Invalid or missing agent results."}

        print("✅ Received Agents Results:", json.dumps(agents_results, indent=2))

        # 🔹 Siemens Product Mapping (Restricts Mistral to Valid Names)
        siemens_product_map = {
            "CAD Modeling": "Siemens NX",
            "Simulation": "Simcenter 3D",
            "Thermal Management": "Simcenter STAR-CCM+",
            "System Simulation": "Simcenter Amesim",
            "Multidisciplinary Design": "HEEDS",
            "Test & Validation": "Simcenter Testlab",
            "Simulation Data Management": "Teamcenter Simulation",
            "FEA Analysis": "Simcenter Nastran",
            "Topology Optimization": "Simcenter OptiStruct"
        }

        # Step 1: Define Flow Orchestrator Agent
        flow_orchestrator_agent = Agent(
            role="Flow Orchestrator Agent",
            goal=(
                "Generate a hierarchical React Flow JSON representing dependencies between Siemens products. "
                "Only use product names from the predefined Siemens software list."
            ),
            backstory="You specialize in structuring workflows based on Siemens software dependencies.",
            llm=llm,
            verbose=True
        )

        # Step 2: Define React Flow Diagram Task
        flow_task = Task(
            description=f"""
            Based on Siemens agent results:
            {json.dumps(agents_results, indent=2)}

            User Query: "{data['message']}"

            **TASK:**
            1️⃣ **Generate a React Flow JSON** showing dependencies between Siemens products.
            2️⃣ Each **product must be a node** with:
               - `id`: Unique string based on the product name
               - `data.label`: The correct Siemens product name (MUST match the provided Siemens product list)
               - `position.x, position.y`: Auto-calculated for hierarchy (spacing to prevent overlap)
               - `level`: Depth in the hierarchy (1 = top, increasing downwards)
            3️⃣ **Edges must represent dependencies** between products:
               - `source`: Parent node (higher-level product)
               - `target`: Child node (dependent product)

            🔹 **STRICT OUTPUT RULES:**
            - Nodes must use **ONLY these Siemens product names**:
              {json.dumps(list(siemens_product_map.values()), indent=2)}
            - **DO NOT** generate new product names.
            - **DO NOT** return explanations, markdown (` ```json `), or any extra text.
            - **ONLY** return **one valid JSON object**.
            - **Ensure correct hierarchy positioning.**
            """,
            expected_output="A structured React Flow JSON with 'nodes' and 'edges' using Siemens product names.",
            agent=flow_orchestrator_agent,
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

        # Step 5: Validate JSON before returning
        if not flow_parsed_results.get("nodes") or not flow_parsed_results.get("edges"):
            return {"error": "Failed to generate valid workflow hierarchy"}

        # Step 6: Save JSON results for debugging/logging
        save_to_file(flow_parsed_results, "flow_hierarchy_results")

        return flow_parsed_results

    except Exception as e:
        print("❌ Error occurred:", str(e))
        return {"error": str(e)}

def create_format_agent():
    return Agent(
        role='Message Formatter',
        goal='Format and beautify text messages into chat-like responses',
        backstory='Specialist in text formatting and presentation',
        allow_delegation=False,
        llm=llm,
    )


def create_format_task(agent):
    return Task(
        description='Format and beautify the input message',
        agent=agent,
        expected_output='A well-formatted informative chat-style message that highlights the key points',
        output_file=os.path.join(output_dir, "final_results_formatted.txt"),
    )
