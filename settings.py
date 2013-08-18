import json
import os

class Settings:
    _option_file_path = os.path.expanduser("~/.xpmidiplus.json")

    def __init__(self):
        self.current_dir = ['.']
        self.favorite_dirs = []
        self.player_program = "aplaymidi"
        self.player_options = "-p 20:0"
        self.sysex = "GM"
        self.background_color = "white"
        self.foreground_color = "medium blue"
        self.viewer_program = ""
        self.viewer_options = ""

        if os.path.exists(self._option_file_path):
            file = open(self._option_file_path, "r")
            try:
                dict = json.load(file)
            except StandardError:
                return

#            try:
            self.current_dir = dict["current_dir"]
            self.favorite_dirs = dict["favorite_dirs"]
            self.player_program = dict["player_program"]
            self.player_options = dict["player_options"]
            self.sysex = dict["sysex"]
            self.background_color = dict["background_color"]
            self.foreground_color = dict["foreground_color"]
            self.viewer_program = dict["viewer_program"]
            self.viewer_options = dict["viewer_options"]
            if not self.current_dir:
                self.current_dir = ["."]
#            except KeyError:
#                return


    def __del__(self):
        options = {
            "current_dir": self.current_dir,
            "favorite_dirs": self.favorite_dirs,
            "player_program": self.player_program,
            "player_options": self.player_options,
            "sysex": self.sysex,
            "background_color": self.background_color,
            "foreground_color": self.foreground_color,
            "viewer_program": self.viewer_program,
            "viewer_options": self.viewer_options,
            }
        file = open(self._option_file_path, "w")
        json.dump(options, file, ensure_ascii = False, indent = True)
