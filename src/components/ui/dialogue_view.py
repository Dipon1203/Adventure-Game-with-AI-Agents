import pygame
from components.ui.window import create_window
from math import ceil
from components.entity import Entity
from components.sprite import Sprite
from components.ui.window import Window
from components.button import Button
from components.label import Label
from core.input import is_key_just_pressed

dialogue_box_width = 500  # The size, left and right, of the dialogue box in pixels
dialogue_box_height = 200 # The size, up and down, of the dialogue box in pixels
padding_bottom = 50       # Empty pixels separating the dialogue box and the bottom
                          # of the window

# Where the name of the speaker is, in the dialogue box
speaker_label_x = 50     
speaker_label_y = 25     

# Where what is being said is, in the dialogue box
content_label_x = 50      
content_label_y = 75

# Where what is being said is, in the dialogue box
helper_label_x = 50
helper_label_y = 150

# Where the text input box will be positioned
input_box_x = 50
input_box_y = 150
input_box_width = 400
input_box_height = 30

# How many letters, per frame, are printed.
letter_speed = 1

active_dialogue_view = None

class InputBox(Sprite):
    def __init__(self, x=0, y=0, width=100, height=30):
        # We're not calling Sprite.__init__ directly as our implementation is different
        self.entity = None
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.surface.fill((50, 50, 50, 180))  # More visible dark gray background
        self.rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.is_ui = True
        
        from core.engine import engine
        engine.ui_drawables.append(self)
        
    def draw(self, screen):
        # Draw the input box with a border
        screen.blit(self.surface, (self.entity.x, self.entity.y))
        pygame.draw.rect(screen, (255, 255, 255), 
                         pygame.Rect(self.entity.x, self.entity.y, self.width, self.height), 2)

    def breakdown(self):
        from core.engine import engine
        if self in engine.ui_drawables:
            engine.ui_drawables.remove(self)

class DialogueView:
    def __init__(self, lines, npc, player, dialogue_box_sprite="text_box.png"):
        global active_dialogue_view
        active_dialogue_view = self
        self.lines = lines
        self.npc = npc
        self.player = player
        self.waiting_for_input = False
        self.input_text = ""
        self.active_input = False
        self.key_cooldown = {}  # To track key press cooldowns

        from core.camera import camera
        window_x = camera.width/2 - dialogue_box_width/2
        window_y = camera.height - padding_bottom - dialogue_box_height
        self.window = create_window(window_x, window_y, 
                                    dialogue_box_width, dialogue_box_height).get(Window)
        
        self.background = Entity(Sprite(dialogue_box_sprite, is_ui=True),
                                 x=window_x,
                                 y=window_y).get(Sprite)

        self.speaker_label = Entity(Label("EBGaramond-ExtraBold.ttf", "", size=25), 
                                  x=window_x + speaker_label_x, 
                                  y=window_y + speaker_label_y).get(Label)

        self.content_label = Entity(Label("EBGaramond-Regular.ttf", "", size=25), 
                                  x=window_x + content_label_x, 
                                  y=window_y + content_label_y - 5).get(Label)
        
        # Create a visual input box
        self.input_box = Entity(InputBox(x=0, y=0, width=input_box_width, height=input_box_height),
                              x=window_x + input_box_x,
                              y=window_y + input_box_y).get(InputBox)
        
        # Create a label for the input text
        self.input_label = Entity(Label("EBGaramond-Regular.ttf", 
                                       "Click here to type...", 
                                       size=20,
                                       color=(220, 220, 220)), 
                                x=window_x + input_box_x + 10, 
                                y=window_y + input_box_y + 5).get(Label)
        
        self.helper_label = Entity(Label("EBGaramond-Medium.ttf", 
                                         "[Press Enter or Space]", 
                                         size=20), 
                                  x=window_x + helper_label_x, 
                                  y=window_y + helper_label_y - 35).get(Label)
        
        self.window.items.append(self.background)
        self.window.items.append(self.speaker_label)
        self.window.items.append(self.content_label)
        self.window.items.append(self.helper_label)
        self.window.items.append(self.input_box)
        self.window.items.append(self.input_label)

        # Make the input box invisible initially
        self.toggle_input_box(False)

        from core.engine import engine
        engine.active_objs.append(self)

        self.current_line = -1
        self.next_line()
        
        # Store keymapping for character input
        self.key_mapping = {
            pygame.K_a: 'a', pygame.K_b: 'b', pygame.K_c: 'c', pygame.K_d: 'd',
            pygame.K_e: 'e', pygame.K_f: 'f', pygame.K_g: 'g', pygame.K_h: 'h',
            pygame.K_i: 'i', pygame.K_j: 'j', pygame.K_k: 'k', pygame.K_l: 'l',
            pygame.K_m: 'm', pygame.K_n: 'n', pygame.K_o: 'o', pygame.K_p: 'p',
            pygame.K_q: 'q', pygame.K_r: 'r', pygame.K_s: 's', pygame.K_t: 't',
            pygame.K_u: 'u', pygame.K_v: 'v', pygame.K_w: 'w', pygame.K_x: 'x',
            pygame.K_y: 'y', pygame.K_z: 'z', pygame.K_SPACE: ' ',
            pygame.K_0: '0', pygame.K_1: '1', pygame.K_2: '2', pygame.K_3: '3',
            pygame.K_4: '4', pygame.K_5: '5', pygame.K_6: '6', pygame.K_7: '7',
            pygame.K_8: '8', pygame.K_9: '9', pygame.K_PERIOD: '.', pygame.K_COMMA: ',',
            pygame.K_MINUS: '-', pygame.K_SEMICOLON: ';', pygame.K_QUOTE: "'",
            pygame.K_SLASH: '/', pygame.K_BACKSLASH: '\\', pygame.K_EQUALS: '=',
        }
        
    def toggle_input_box(self, active):
        self.active_input = active
        if active:
            self.input_box.surface.fill((50, 50, 50, 180))  # More visible dark gray
            self.input_label.set_text("Click here to type...")
        else:
            self.input_box.surface.fill((0, 0, 0, 0))  # Fully transparent
            self.input_label.set_text("")

    def next_line(self):
        self.current_line += 1
        if self.current_line >= len(self.lines):
            self.breakdown()
            return
        line = self.lines[self.current_line]
        if len(line) == 0:
            self.next_line()
            return
        if line[0] == '-':
            self.player_speak(line)
        elif line[0] == '!':
            self.command(line)
        elif line[0] == '$':
            self.narrate(line)
        else:
            self.npc_speak(line)

    def npc_speak(self, line):
        self.speaker_label.set_text(self.npc.obj_name)
        self.content_label.set_text(line)
        self.waiting_for_input = True
        self.toggle_input_box(True)
        self.input_text = ""
        self.helper_label.set_text("[Type your response and press Enter]")

    def player_speak(self, line):
        self.speaker_label.set_text("You")
        self.content_label.set_text(line[1:])
        self.waiting_for_input = False
        self.toggle_input_box(False)
        self.helper_label.set_text("[Press Enter or Space]")

    def narrate(self, line):
        self.speaker_label.set_text("")
        self.content_label.set_text(line[1:])
        self.waiting_for_input = False
        self.toggle_input_box(False)
        self.helper_label.set_text("[Press Enter or Space]")

    def command(self, line):
        words = line.split(" ")
        command = words[1]
        arguments = words[2:]
        if command == "give":
            from components.player import inventory
            from data.item_types import item_types
            t = item_types[int(arguments[0])]
            amount = int(arguments[1])
            excess = inventory.add(t, amount)
            amount_added = amount - excess
            if amount_added == 0:
                self.speaker_label.set_text("")
                self.content_label.set_text(f"Your inventory is full")
            else:
                self.speaker_label.set_text("")
                self.content_label.set_text(f"You receive {amount_added} {t.name}")
        elif command == "goto":
            self.current_line = int(arguments[0])-2
            print(self.current_line)
            self.next_line()
        elif command == "end":
            self.breakdown()
        elif command == "random":
            import random
            next_lines = [int(x) for x in arguments]
            result = random.choice(next_lines)
            self.current_line = result-2
            self.next_line()
        else:
            print(f"Unknown command {command}")

    def handle_typing(self):
        """Handle keyboard input for the text box"""
        # Handle backspace
        if is_key_just_pressed(pygame.K_BACKSPACE):
            self.input_text = self.input_text[:-1]
            self.update_input_label()
            return True
            
        # Handle enter/return key
        if is_key_just_pressed(pygame.K_RETURN):
            if self.input_text:
                # Add player response to dialogue
                player_line = f"- {self.input_text}"
                self.lines.insert(self.current_line + 1, player_line)
                self.toggle_input_box(False)
                self.waiting_for_input = False
                self.next_line()
            return True
            
        # Handle all other keys
        keys = pygame.key.get_pressed()
        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        
        # Check each mapped key
        for key, char in self.key_mapping.items():
            if is_key_just_pressed(key) and len(self.input_text) < 30:
                # Apply shift modifier if needed
                if shift_pressed:
                    if 'a' <= char <= 'z':
                        char = char.upper()
                    elif char == '1': char = '!'
                    elif char == '2': char = '@'
                    elif char == '3': char = '#'
                    elif char == '4': char = '$'
                    elif char == '5': char = '%'
                    elif char == '6': char = '^'
                    elif char == '7': char = '&'
                    elif char == '8': char = '*'
                    elif char == '9': char = '('
                    elif char == '0': char = ')'
                    elif char == ';': char = ':'
                    elif char == "'": char = '"'
                    elif char == ',': char = '<'
                    elif char == '.': char = '>'
                    elif char == '/': char = '?'
                    elif char == '\\': char = '|'
                    elif char == '=': char = '+'
                    elif char == '-': char = '_'
                
                self.input_text += char
                self.update_input_label()
                return True
                
        return False
    
    def update_input_label(self):
        """Update the input label text"""
        if not self.input_text:
            self.input_label.set_text("Click here to type...")
        else:
            self.input_label.set_text(self.input_text)

    def update(self):
        # Handle keyboard input for the input box when active
        if self.active_input:
            self.handle_typing()
            
        # Handle advancing dialogue with space/enter when not waiting for input
        if not self.waiting_for_input and (is_key_just_pressed(pygame.K_SPACE) or is_key_just_pressed(pygame.K_RETURN)):
            self.next_line()

        # Exit dialogue with WASD or ESC
        if is_key_just_pressed(pygame.K_ESCAPE):
            self.breakdown()

    def breakdown(self):
        from core.engine import engine
        engine.active_objs.remove(self)
        for c in self.window.items:
            c.breakdown()