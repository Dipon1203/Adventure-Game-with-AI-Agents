import os
import time
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ChatMessageHistory
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from openai import APIError
from components.agent_tools import neighbor_tool, forest_tree_tool, search_tool
from components.local_storage import LocalChatStorage

try:
    import redis
    from langchain_community.chat_message_histories import RedisChatMessageHistory
    from components.redis_db import RedisChatStorage
    REDIS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    REDIS_AVAILABLE = False


load_dotenv()

class AgentResponse(BaseModel):
    response: list 
    isSell: bool
    tools_used: list[str]

class NPCAgent:
    """
    A configurable agent class that creates different agent personas based on character names.
    """
    
    def __init__(self, character_name: str, model: str = "gpt-4o-mini" ):

        self.character_name = character_name
        self.parser = PydanticOutputParser(pydantic_object=AgentResponse)

        if REDIS_AVAILABLE:
            try:
                self.chat_storage = RedisChatStorage(character_name=character_name)
                # Test connection to see if Redis is running
                self.chat_storage.redis_client.ping()
                print("Using Redis for chat storage")
            except (redis.exceptions.ConnectionError, AttributeError) as e:
                print(f"Redis connection failed: {e}. Falling back to local storage.")
                self.chat_storage = LocalChatStorage(character_name=character_name)
        else:
            print("Redis not available. Using local storage for chat history.")
            self.chat_storage = LocalChatStorage(character_name=character_name)

        self.chat_history = self.chat_storage.load_chat(character_name)

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
        self.tools = [neighbor_tool]
        
        # Character-specific configurations
        character_configs = {
            "nancy": {
                "system_prompt": """

                You are Nancy, a cheerful diamond seller. Your responses must follow these strict guidelines:

                1. Strictly format all output responses as JSON with the following structure {format_instructions}.

                2. The "response" field must:
                - Contain exactly ONE string in the array
                - Be 50 characters or less
                - Be a single sentence
                - Sound like a cheerful, lovely diamond seller

                3. Set "isSell" to true ONLY when:
                - The query explicitly states an intention to purchase a diamond
                - The query clearly indicates a buying decision
                
                4. For all other queries, set "isSell" to false

                5. If "isSell" is true, include a brief thank you message within your response.

                Do not provide any text outside of the JSON structure. Ensure your JSON is properly formatted and valid.
                """,
                "tools": [neighbor_tool],
            },
            "albert": {
                "system_prompt": """

                You are Albert, a savage axe seller. Your responses must follow these strict guidelines:

                1. Strictly format all output responses as JSON with the following structure {format_instructions}.

                2. The "response" field must:
                - Contain exactly ONE string in the array
                - Be 50 characters or less
                - Be a single sentence
                - Sound like a savage axe seller

                3. Set "isSell" to true ONLY when:
                - The query explicitly states an intention to purchase an axe
                - The query clearly indicates a buying decision
                - If true, include a brief thank you message in the response

                4. For all other queries, set "isSell" to false

                5. If asked about trees in the Forest, you must consider the number of trees before replying.

                6. Do not provide any text outside of the JSON structure. Ensure your JSON is properly formatted and valid.
                """,
                "tools": [neighbor_tool, forest_tree_tool],
            },


            "bob": {
                "system_prompt": """

                You are Bob, the Eye of Sauron. Your responses must follow these strict guidelines:

                1. Strictly format all output responses as JSON with the following structure {format_instructions}.

                2. The "response" field must:
                - Contain exactly ONE string in the array
                - Be 50 characters or less
                - Be a single sentence
                - Sound like the Eye of Sauron

                3. Set "isSell" to false ALWAYS, no matter the query.

                4. Do not provide any text outside of the JSON structure. Ensure your JSON is properly formatted and valid.
                """,
                "tools": [neighbor_tool, search_tool, forest_tree_tool],
            },


            "amy": {
                "system_prompt": """

                You are Amy, a mad physics teacher. Your responses must follow these strict guidelines:

                1. Strictly format all output responses as JSON with the following structure {format_instructions}.

                2. The "response" field must:
                - Contain exactly ONE string in the array
                - Be 50 characters or less
                - Be a single sentence
                - Always sound like a mad physics teacher
                - Always try to teach physics and ask questions

                3. Set "isSell" to false ALWAYS, no matter the query.

                4. Do not provide any text outside of the JSON structure. Ensure your JSON is properly formatted and valid.
                """,
                "tools": [neighbor_tool],
            },
        }
        
            
        config = character_configs.get(self.character_name.lower(), character_configs["nancy"])
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

    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the agent with the given query.
        
        Args:
            query: The user's query string
            
        Returns:
            Dict containing the raw response from the agent
        """

        max_retries = 3
        retry_delay = 1  # seconds

        messages = self.chat_history.messages if hasattr(self.chat_history, "messages") else []
        
        for attempt in range(max_retries):
            try:
                return self.agent_executor.invoke({"chat_history": messages, "query": query})
            except APIError as e:
                if attempt < max_retries - 1:
                    print(f"API Error: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        
        messages = self.chat_history.messages if hasattr(self.chat_history, "messages") else []

        print(f"This is from inside run{messages}")

        return self.agent_executor.invoke({"chat_history": messages, "query": query})
    
    def get_structured_response(self, raw_response: Dict[str, Any]) -> Optional[AgentResponse]:
        """
        Parse the raw response into a structured AgentResponse object.
        """
        try:
            structured_response = self.parser.parse(raw_response.get("output"))
            return structured_response
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {raw_response}")
            return None
        

    def update_chat_history(self, user_message, agent_response=None):
        """
        Update the chat history with both user message and agent response.
        This ensures proper formatting for OpenAI API.
        """

        user_msg = user_message[0] if isinstance(user_message, list) and user_message else user_message

        # Initialize a new chat history if one doesn't exist
        if not hasattr(self.chat_history, "add_user_message"):
            self.chat_history = ChatMessageHistory()

        if user_msg:
            self.chat_history.add_user_message(user_msg)
            

        if agent_response:
            agent_msg = agent_response[0] if isinstance(agent_response, list) and agent_response else agent_response
            
            self.chat_history.add_ai_message(agent_msg)
        
        self.chat_storage.save_chat(self.character_name, self.chat_history)

# Example usage:
if __name__ == "__main__":
    # Create an agent with a specific character

    character_name = "Nancy"
    agent = NPCAgent(character_name = character_name, model = "gpt-4o")
    
    # Get user query
    while True:
        query = input("Your query: ")
        if query.lower() in ["quit", "exit", "bye", "ok bye"]:
            break

        # Run the agent
        raw_response = agent.run(query)
    
        # Parse the response
        structured_response = agent.get_structured_response(raw_response).response
        agent.update_chat_history(query, structured_response)

        if structured_response:
            print(f"This is response: {structured_response}")
