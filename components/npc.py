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

            agent = NPCAgent(character_name = self.obj_name, model = "gpt-4o-mini")

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
