from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor


load_dotenv()

llm = ChatOpenAI(model = "gpt-4o-mini")

class NPCResponse(BaseModel):
    response: str 
    isBuying: str

response = llm.invoke("Tell me about NPC?")
parser = PydanticOutputParser(pydantic_object=NPCResponse)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a NPC in a game. You're name is Nancy. You sell diamond. You will be 
            cheerful. You will try to sell diamond. You're response will be under 20 characters.
            \n{format_instructions}
            """
        ),

        ("placeholder", "{chat_history}"),
        ("human","{query}"),
        ("placeholder", "{agent_scratchpad}")
    ]
).partial(format_instructions = parser.get_format_instructions())

tools = []

agent = create_tool_calling_agent(
    llm = llm,
    prompt = prompt,
    tools = tools
)

agent_executor = AgentExecutor(agent = agent,tools = tools, verbose=True)
query = input("Let me know your query:\n")
raw_response = agent_executor.invoke({"query": query})
print(raw_response)

try:
    structured_response = parser.parse(raw_response.get("output")[0])   
    print(structured_response)
except Exception as e:
    print("Error parsing response", e, "Raw response - ", raw_response)

