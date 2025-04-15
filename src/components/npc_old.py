from components.usable import Usable

npc_folder_location = "content/npcs"
npc_talk_distance = 150

class NPC(Usable):
    def __init__(self, obj_name, npc_file):
        super().__init__(obj_name)
        self.npc_file = npc_file

    def on(self, other, distance):
        from components.player import Player
        player = other.get(Player)

        
        print(f"Talking to {self.obj_name}")

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



pass

from components.usable import Usable
from content.intelligent_npcs.npc_agent import NPCAgent

npc_folder_location = "content/npcs"
npc_talk_distance = 150

class NPC(Usable):
    def __init__(self, obj_name, npc_file):
        super().__init__(obj_name)
        self.npc_file = npc_file

    def on(self, other, distance):
        from components.player import Player
        player = other.get(Player)


        print(f"Talking to {self.obj_name}")

        if distance < npc_talk_distance:

            agent = NPCAgent(character_name=self.obj_name)
            agent.run()

            # Run the agent
            raw_response = agent.run(query)
            print(raw_response)
            
            # Parse the response
            structured_response = agent.get_structured_response(raw_response)
            if structured_response:
                print(structured_response)
            
            
            from components.ui.dialogue_view import DialogueView
            DialogueView(structured_response, self, player)

            
        else:
            player.show_message("I need to get closer")

