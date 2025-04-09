import pygame
from components.ui.window import create_window
from math import ceil
from components.entity import Entity
from components.sprite import Sprite
from components.ui.window import Window
from components.button import Button
from components.label import Label
from core.input import is_key_just_pressed


class DialogueView:
    def __init__(self, lines, npc, player, dialogue_box_sprite="text_box.png"):
        global active_dialogue_view
        active_dialogue_view = self
        self.lines = lines
        self.npc = npc
        self.player = player

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
                                  y=window_y + content_label_y).get(Label)

        self.helper_label = Entity(Label("EBGaramond-Medium.ttf", 
                                         "[Press Enter or Space]", 
                                         size=25), 
                                  x=window_x + helper_label_x, 
                                  y=window_y + helper_label_y).get(Label)
        
        
        self.window.items.append(self.background)
        self.window.items.append(self.speaker_label)
        self.window.items.append(self.content_label)
        self.window.items.append(self.helper_label)

        from core.engine import engine
        engine.active_objs.append(self)

        self.current_line = -1
        

    