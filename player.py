import os
import time
import shlex
import signal

class Player:
    def __init__(self, root):
        self.root = root
        self.player_pid = None
        self.viewer_pid = None
        self.tone_generator_clean = False


    def play_sysex(self, settings, wait = os.P_WAIT):
        if self.is_playing():
            self.stop()
        self.tone_generator_clean = True
        self.play("./sysex/" + settings.sysex + ".mid", settings, wait)


    def play(self, file_path, settings, wait,
             callback_while_playing = None, callback_when_finished = None):
        if self.is_playing():
            self.stop()
        if not self.tone_generator_clean:
            self.play_sysex(settings)

        self.play_timer = time.time()
        op = shlex.split(settings.player_options)
        self.player_pid = os.spawnvp(wait, settings.player_program,
            [settings.player_program] + op + [file_path])

        self.tone_generator_clean = False

        self.root.after(500, self.check)

        self.while_playing = callback_while_playing
        self.when_finished = callback_when_finished


    def view(self, midifile_path, settings):
        if not settings.viewer_program:
            return

        pdffile_path = os.path.expanduser(
            midifile_path.replace(".mid", ".pdf"))
        if os.path.exists(pdffile_path):
            self.viewer_pid = os.spawnvp(os.P_NOWAIT, settings.viewer_program,
                [settings.viewer_program] + settings.viewer_options.split() + [pdffile_path])
        else:
            self.viewer_pid = None


    def check(self):
        if self.is_viewing():
            try:
                os.waitpid(self.viewer_pid, os.WNOHANG)
            except OSError:   # our display is gone, kill the player
                self.viewer_pid = None
#                self.stop()

        if self.is_playing():
            try:
                s = os.waitpid(self.player_pid, os.WNOHANG)
                t = time.time() - self.play_timer
                if self.while_playing:
                    self.while_playing(t)
                self.root.after(500, self.check)
            except OSError:  # player is gone, kill display
                if self.viewer_pid:
                    os.kill(self.viewer_pid, signal.SIGKILL)
                self.viewer_pid = None
                self.player_pid = None
                self.play_timer = 0

                # play next file
                if self.when_finished:
                    self.when_finished()


    def stop(self):
        if self.is_viewing():
            os.kill(self.viewer_pid, signal.SIGKILL)
            self.viewer_pid = None

        """ See if last run is still running. The call to os.waitpid()
            returns a process ID and a status indication. We check the PID
            returned. If this value is equal to the current PID then
            the process has died ... and we can ignore the whole issue.
        """

        if self.is_playing():
            try:
                pid, s = os.waitpid(self.player_pid, os.WNOHANG)
            except OSError:
                return

            if not pid:
                # stop current player, could leave hanging notes
                os.kill(self.player_pid, signal.SIGKILL)

            self.player_pid = None


    def is_playing(self):
        return self.player_pid

    def is_viewing(self):
        return self.viewer_pid
