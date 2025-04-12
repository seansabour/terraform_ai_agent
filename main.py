

import getpass
import os
from langchain.tools import Tool
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import traceable
from langserve import RemoteRunnable, add_routes
from github import Github
import subprocess
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()  # Loads from .env by default


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


_set_env("OPENAI_API_KEY")




# --- Define the state structure ---
class AgentState(dict):
    prompt: str
    validate_result: str
    validation_passed: bool
    scan_result: str
    scan_passed: bool


# --- LLM Setup ---
llm = ChatOpenAI(model="gpt-4o", temperature=.7, max_retries=5)

# --- LangChain Tools with LangSmith Tracing ---
@traceable(name="generate_terraform")
def terraform_generator(prompt: str) -> str:
    response =  llm.invoke(f"Try to generate secure and reusable Terraform code that has a keen eye for security and cost for: {prompt}")

    print(response)
    return response.content

@traceable(name="validate_terraform")
def terraform_validator(_: str = "") -> str:
    try:
        result = subprocess.run(
            ["terraform", "init"],
            check=True,
            capture_output=True,
            text=True  # so output is string, not bytes
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Terraform init failed!")
        print("Return code:", e.returncode)
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)    
    fmt = subprocess.run(["terraform", "fmt", "-check"], capture_output=True, text=True)
    validate = subprocess.run(["terraform", "validate"], capture_output=True, text=True)
    return fmt.stdout + "\n" + validate.stdout

@traceable(name="lint_terraform")
def terraform_linter(_: str = "") -> str:
    tflint = subprocess.run(["tflint"], capture_output=True, text=True)
    checkov = subprocess.run(["checkov", "-d", "."], capture_output=True, text=True)
    return tflint.stdout + "\n" + checkov.stdout

# --- LangChain Tool Wrappers ---
generate_tool = Tool(name="generate_terraform", func=terraform_generator, description="Generate Terraform code from prompt")
validate_tool = Tool(name="validate_terraform", func=terraform_validator, description="Validate and format Terraform")
lint_tool = Tool(name="lint_terraform", func=terraform_linter, description="Lint and scan Terraform code")

# --- Tool Nodes ---
def generate_terraform_code(state: AgentState) -> AgentState:
    code = generate_tool.invoke(state["prompt"])
    with open("main.tf", "w") as f:
        f.write(code)
    state["terraform_code"] = code
    return state

def validate_terraform_code(state: AgentState) -> AgentState:
    result = validate_tool.invoke("")
    print(result)
    state["validate_result"] = result
    state["validation_passed"] = "Success!" in result
    return state

def scan_terraform_code(state: AgentState) -> AgentState:
    result = lint_tool.invoke("")
    state["scan_result"] = result
    state["scan_passed"] = "Passed checks" in result
    return state




# --- Build LangGraph ---
graph = StateGraph(AgentState)

graph.add_node("generate", RunnableLambda(generate_terraform_code))
graph.add_node("validate", RunnableLambda(validate_terraform_code))
graph.add_node("scan", RunnableLambda(scan_terraform_code))

graph.set_entry_point("generate")
graph.add_edge("generate", "validate")
graph.add_edge("validate", "scan")
graph.add_edge("scan", END)


workflow = graph.compile()

# --- LangServe API ---
app = FastAPI()
add_routes(app, workflow, path="/terraform-agent")

# --- CLI Runner ---
if __name__ == "__main__":
    initial_state = AgentState({"prompt": "Generate only valid Terraform HCL code to deploy a S3 bucket in us-west-2. Do not include explanations or markdown formatting. Only output code without formatting hcl. Use checkov to ensure best practices are being met"})
    final_state = workflow.invoke(initial_state)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Terraform generator. Only respond with valid Terraform HCL code. Never explain. Never use markdown. Use tools like checkov and tflint to ensure best practices are followed. "),
        ("human", "{input}")
    ])

    chain = prompt | llm
    chain.invoke({"input": "Create a Terraform module for an S3 bucket with versioning enabled"})

