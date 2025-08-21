import os
import pickle
import json
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

class LocalChatStorage:
    """A replacement for RedisChatStorage that uses local files instead of Redis"""
    
    def __init__(self, storage_dir='content/chat_data', character_name="nancy"):
        """Initialize local file storage"""
        self.storage_dir = storage_dir
        self.character_name = character_name
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_filepath(self, key):
        """Get the file path for a specific key"""
        return os.path.join(self.storage_dir, f"{key}.pkl")
    
    def save_chat(self, key, chat_history):
        """
        Save LangChain chat history to a local file
        
        Parameters:
            key (str): The key to store the chat under (e.g., 'nancy', 'albert')
            chat_history (ChatMessageHistory or list): LangChain chat history to save
        """
        # Serialize the chat history
        filepath = self._get_filepath(key)
        
        try:
            # Store in file
            with open(filepath, 'wb') as f:
                pickle.dump(chat_history, f)
            print(f"Chat saved under key: {key}")
        except Exception as e:
            print(f"Error saving chat: {e}")
    
    def load_chat(self, key):
        """
        Load chat history from a local file
        
        Parameters:
            key (str): The key to retrieve the chat from
            
        Returns:
            The chat history or a new empty ChatMessageHistory if not found
        """
        filepath = self._get_filepath(key)
        
        if os.path.exists(filepath):
            try:
                # Load the chat history from file
                with open(filepath, 'rb') as f:
                    chat_history = pickle.load(f)
                print(f"Chat loaded from key: {key}")
                return chat_history
            except Exception as e:
                print(f"Error loading chat: {e}")
                return ChatMessageHistory()
        else:
            # Return a new chat history if none exists
            print(f"No existing chat found for key: {key}. Creating new chat history.")
            return ChatMessageHistory()
    
    def delete_chat(self, key):
        """Delete a chat history by key"""
        filepath = self._get_filepath(key)
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Chat deleted for key: {key}")
            except Exception as e:
                print(f"Error deleting chat: {e}")