from components.usable import Usable
from components.npc_agent_db import NPCAgent
from components.ui.dialogue_view import DialogueView


npc_folder_location = "content/npcs"
npc_talk_distance = 150

from components.usable import Usable

npc_folder_location = "content/npcs"
npc_talk_distance = 150

class static_NPC(Usable):
    def __init__(self, obj_name, npc_file):
        super().__init__(obj_name)
        self.npc_file = npc_file

    def on(self, other, distance):
        from components.player import Player
        player = other.get(Player)
        if distance < npc_talk_distance:
        
            file = open(npc_folder_location + "/" + self.npc_file, "r")
            data = file.read()
    
            file.close()
            lines = data.split('\n')

            print(lines)
            
            
            from components.ui.dialogue_view import DialogueView
            DialogueView(lines, self, player)
        else:
            player.show_message("I need to get closer")

class NPC(Usable):

    npc_conversation_dict = {
            "Nancy": ["Hi, I'm Nancy!"],
            "Albert" : ["Hey ya mate! Albert here!"],
            "Amy" : ["Physics is everything!"],
            "Bob" : ["I see everything!"]
        }
    
    def __init__(self, obj_name, npc_file):
        super().__init__(obj_name)
        self.npc_file = npc_file

    def on(self, other, distance):
        from components.player import Player
        player = other.get(Player)


        if distance < npc_talk_distance:

            lines = self.npc_conversation_dict[self.obj_name]

            agent = NPCAgent(character_name = self.obj_name, model = "gpt-4o")

            query = ""

            try:

                #raw_response = agent.run(query)
                #structured_response = agent.get_structured_response(raw_response)

                """
                if structured_response.response:
                    lines = structured_response.response
                else:
                """

                agent.update_chat_history(lines)
            
            except Exception as e:
                print(f"Error initializing NPC dialogue: {e}")
                lines = [f"Hi, how can I help you?"]

            from components.ui.dialogue_view import DialogueView
            DialogueView(lines, self, player)
        else:
            player.show_message("I need to get closer")
"""  
class NPC(Usable):

    npc_conversation_dict = {
            "Nancy": ["Hi, I'm Nancy", "- Hello"],
            "Albert" : ["Hi, I'm Albert", "- Hello"],
            "Amy" : ["Hi, I'm Amy", "- Hello"],
            "Bob" : ["Hi, I'm Bob", "- Hello"]
        }
    
    def __init__(self, obj_name, npc_file):
        super().__init__(obj_name)
        self.npc_file = npc_file

    def on(self, other, distance):
        from components.player import Player
        player = other.get(Player)


        if distance < npc_talk_distance:

            lines = self.npc_conversation_dict[self.obj_name]

            agent = NPCAgent(character_name = self.obj_name, model = "gpt-4o")

            query = "Generate the next"

            raw_response = agent.run(query)
            lines = agent.get_structured_response(raw_response).response

            from components.ui.dialogue_view import DialogueView
            DialogueView(lines, self, player)
        else:
            player.show_message("I need to get closer")

"""
"""    
class NPC(static_NPC):

    def __init__(self, obj_name, npc_file):
        super().__init__(obj_name)
        self.npc_file = npc_file


    def on(self, other, distance):
        from components.player import Player
        player = other.get(Player)


        print(f"Talking to {self.obj_name}")

        if distance < npc_talk_distance:

            agent = NPCAgent(character_name = self.obj_name, model = "gpt-4o")
 
            while True:

                query = input("Your query: ")

                if query.lower() in ["quit", "exit", "bye"]:
                    break

                # Run the agent

                query_line = query
                
                DialogueView(query_line, self, player)

                raw_response = agent.run(query)
                print(f"This is raw response: {raw_response}")

            
                # Parse the response
                structured_response = agent.get_structured_response(raw_response).response
                isSell = agent.get_structured_response(raw_response).isSell

                if isSell:
                    npc_response = "! give " + structured_response

                
                DialogueView(npc_response, self, player)

                agent.update_chat_history(query, structured_response)
                

                if structured_response:
                    print(f"This is response: {structured_response}")

        else:
            player.show_message("I need to get closer")


"""
