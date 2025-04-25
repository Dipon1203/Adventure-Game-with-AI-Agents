import redis
import pickle
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
import json

class RedisChatStorage:
    def __init__(self, host='localhost', port=6379, db=0, character_name = "nancy"):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(host=host, port=port, db=db)
        self.character_name = character_name
    
    def save_chat(self, key, chat_history):
        """
        Save LangChain chat history to Redis
        
        Parameters:
            key (str): The key to store the chat under (e.g., 'nancy', 'albert')
            chat_history (ChatMessageHistory or list): LangChain chat history to save
        """
        # Serialize the chat history
        serialized_chat = pickle.dumps(chat_history)
        
        # Store in Redis
        self.redis_client.set(key, serialized_chat)
        print(f"Chat saved under key: {key}")
    
    def load_chat(self, key):
        """
        Load chat history from Redis
        
        Parameters:
            key (str): The key to retrieve the chat from
            
        Returns:
            The chat history or a new empty ChatMessageHistory if not found
        """
        # Try to get the chat history from Redis
        serialized_chat = self.redis_client.get(key)
        
        if serialized_chat:
            # Deserialize the chat history
            chat_history = pickle.loads(serialized_chat)
            print(f"Chat loaded from key: {key}")
            return chat_history
        else:
            # Return a new chat history if none exists
            print(f"No existing chat found for key: {key}. Creating new chat history.")
            return ChatMessageHistory()
    
    def delete_chat(self, key):
        """Delete a chat history by key"""
        self.redis_client.delete(key)
        print(f"Chat deleted for key: {key}")


# Example usage:

# Initialize the storage


# Example: Creating and saving Nancy's chat

"""



# Later: retrieve and continue a chat
def continue_chat(name):
    chat = chat_storage.load_chat(name)
    print(f"\nContinuing {name}'s chat:")
    for message in chat.messages:
        if isinstance(message, HumanMessage):
            print(f"Human: {message.content}")
        elif isinstance(message, AIMessage):
            print(f"AI: {message.content}")
    
    # Add a new message
    chat.add_user_message(f"Hello again, this is a new message for {name}")
    chat.add_ai_message("Nice to see you again!")
    
    # Save the updated chat
    chat_storage.save_chat(name, chat)

# Continue Nancy's chat
continue_chat("nancy")
"""