from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.chat_message_histories import RedisChatMessageHistory
import os

# Load environment variables
load_dotenv()

class AgentResponse(BaseModel):
    response: str 
    isSell: bool

class NPCAgent:
    """
    A configurable agent class that creates different agent personas based on character names.
    """
    
    def __init__(self, character_name: str, model: str = "gpt-4o-mini", chat_history: list = []):

        self.character_name = character_name
        self.parser = PydanticOutputParser(pydantic_object=AgentResponse)
        self.chat_history = chat_history
        # Configure the LLM based on model name

        #script_dir = "content\intelligent_npcs"
        #env_path =  os.path.join(script_dir, '.env')

        """
        with open(".env", 'r') as f:
            env_content = f.read()

        # Find the API key line in the raw file
        for line in env_content.split('\n'):
            if 'OPENAI_API_KEY' in line:
                api_key = line.split('=', 1)[1].strip()
                break
       """
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        self.llm = ChatOpenAI(model=model, api_key=api_key)
        
            
        # Set up character-specific configurations
        self._configure_character()
        
        # Initialize the agent
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            prompt=self.prompt,
            tools=self.tools,
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools, 
            verbose=True
        )

    def _configure_character(self):
        """
        Configure the prompt and tools based on the character name.
        This method sets up character-specific behaviors and capabilities.
        """
        # Default tools that all characters have access to
        self.tools = []
        
        # Character-specific configurations
        character_configs = {
            "nancy": {
                "system_prompt": """
                You are Nancy. You are a character in a NPC game. You are a cheerful lady and a 
                diamond seller. Make sure your response is within 20 characters. You will interact with 
                player to sell diamond. 

                Your responses MUST be formatted as JSON with the following structure and provide no other text
                \n{format_instructions}
                """,
                "tools": [],
            },
            "albert": {
                "system_prompt": """
                You are Albert. You are a character in a NPC game. You are tough guy and a 
                axe seller. Make sure your response is within 20 characters. You will interact with 
                player to sell axe.
                Wrap the output in this format and provide no other text \n{format_instructions}
                """,
                "tools": [],
            }
        }
        
        
            
        config = character_configs[self.character_name.lower()]
        system_prompt = config["system_prompt"]
        self.tools = config["tools"]
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{query}"),
                ("placeholder", "{agent_scratchpad}")
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())

    def run(self, query: str, chat_history: list) -> Dict[str, Any]:
        """
        Run the agent with the given query.
        
        Args:
            query: The user's query string
            
        Returns:
            Dict containing the raw response from the agent
        """
        return self.agent_executor.invoke({"chat_history": chat_history, "query": query})
    
    def get_structured_response(self, raw_response: Dict[str, Any]) -> Optional[AgentResponse]:
        """
        Parse the raw response into a structured AgentResponse object.
        
        Args:
            raw_response: The raw response from the agent_executor
            
        Returns:
            A AgentResponse object if parsing succeeds, None otherwise
        """
        try:
            structured_response = self.parser.parse(raw_response.get("output"))
            return structured_response
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {raw_response}")
            return None

# Example usage:
if __name__ == "__main__":
    # Create an agent with a specific character

    
    #chat_history = []

    chat_history = RedisChatMessageHistory(session_id="user1", url = "redis://localhost:6379")
    character_name = "Nancy"
    agent = NPCAgent(character_name = character_name, model = "gpt-4o")
    
    # Get user query

    while True:
        print(chat_history)

        query = input("Your query: ")


        if query.lower() == "quit" or query.lower() == "exit" or query.lower() == "bye":
            break

        # Run the agent
        raw_response = agent.run(query, chat_history)
        print(f"This is raw response: {raw_response}")

    
        # Parse the response
        structured_response = agent.get_structured_response(raw_response).response

        #chat_history.append(HumanMessage(content=query))
        #chat_history.append(AIMessage(content=structured_response))

        chat_history.add_user_message(query)
        chat_history.add_ai_message(structured_response)

        if structured_response:
            print(f"This is response: {structured_response}")
            chat_history.append(structured_response)