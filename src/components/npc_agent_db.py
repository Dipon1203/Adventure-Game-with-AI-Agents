import os
import redis
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
from langchain_community.chat_message_histories import RedisChatMessageHistory
from components.redis_db import RedisChatStorage
from openai import APIError


# Load environment variables
load_dotenv()

class AgentResponse(BaseModel):
    response: list 
    isSell: bool

class NPCAgent:
    """
    A configurable agent class that creates different agent personas based on character names.
    """
    
    def __init__(self, character_name: str, model: str = "gpt-4o"):

        self.character_name = character_name
        self.parser = PydanticOutputParser(pydantic_object=AgentResponse)

        self.chat_storage = RedisChatStorage()
        self.chat_history = self.chat_storage.load_chat(character_name)
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        self.llm = ChatOpenAI(model=model, api_key=api_key)

        #self.agent = agent
        
            
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

                You will reply as Nancy, a diamond seller who talks like a cheerful lady. You will
                try to sell diamond. Your reply must be within 30 characters. You will set isSell 
                to True only if the query says or shows clear intent to buy diamond. If isSell is
                True, you will thank and say something like here it is in the same sentence.

                Your responses MUST be formatted as JSON with the following structure and provide no other text
                \n{format_instructions}
                """,
                "tools": [],
            },
            "albert": {
                "system_prompt": """
                You will reply as Albert, an axe seller who talks like a savage pirate. You will
                try to sell axe. Your reply must be within 30 characters. You will set isSell 
                to True only if the query says or shows clear intent to buy axe. If isSell is
                True, you will thank and say something like here it is in the same sentence.

                Your responses MUST be formatted as JSON with the following structure and provide no other text
                \n{format_instructions}
                """,
                "tools": [],
            },

            "bob": {
                "system_prompt": """
                You will generate 5 conversations between Bob, an NPC character and a player, who talks
                like cranky Sheldon Cooper. Bob is a person who talks like Albert Einstein. Each conversation 
                must be within 30 characters. You will give a python list as output. Player's conversation will start
                with '- '. The response must nor contain character names.

                Your responses MUST be formatted as JSON with the following structure and provide no other text
                \n{format_instructions}
                """,
                "tools": [],
            },

            "amy": {
                "system_prompt": """
                You will generate 5 conversations between Amy, an NPC character and a player, who talks
                like cranky Sheldon Cooper. Amy is a cranky lady who complains about the forest. Each conversation 
                must be within 30 characters. You will give a python list as output. Player's conversation will start
                with '- '.

                Your responses MUST be formatted as JSON with the following structure and provide no other text
                \n{format_instructions}
                """,
                "tools": []
            }
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
        

    def update_chat_history(self, user_message, agent_response=None):
        """
        Update the chat history with both user message and agent response.
        This ensures proper formatting for OpenAI API.
        
        Args:
            user_message: String or list containing the user's message
            agent_response: String or list containing the agent's response (optional)
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

    
    #chat_history = []

    character_name = "Nancy"
    agent = NPCAgent(character_name = character_name, model = "gpt-4o")
    
    # Get user query

    while True:

        query = input("Your query: ")

        if query.lower() in ["quit", "exit", "bye"]:
            break

        # Run the agent
        raw_response = agent.run(query)
        #print(f"This is raw response: {raw_response}")

    
        # Parse the response
        structured_response = agent.get_structured_response(raw_response).response

        #chat_history.append(HumanMessage(content=query))
        #chat_history.append(AIMessage(content=structured_response))

        #chat_history.add_user_message(query)
        #chat_history.add_ai_message(structured_response)

        agent.update_chat_history(query, structured_response)

        if structured_response:
            print(f"This is response: {structured_response}")
