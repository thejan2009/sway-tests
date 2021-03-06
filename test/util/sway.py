import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import os
from subprocess import Popen, PIPE, STDOUT
from i3ipc import Con


class TestWindow:
    def __init__(self, sway, title):
        self.id = -1
        self.sway = sway
        self.title = title
        env = os.environ.copy()

        if sway.variant == 'sway':
            if 'DISPLAY' in env:
                del env['DISPLAY']
            env['WAYLAND_DISPLAY'] = sway.display
        elif sway.variant == 'i3':
            if 'WAYLAND_DISPLAY' in env:
                del env['WAYLAND_DISPLAY']
            env['DISPLAY'] = sway.display

        self.proc = Popen(
            ['test/util/gtk-window.py', '--title', title],
            env=env,
            stdout=PIPE,
            stderr=STDOUT)

        self.con = None

        def on_window_new(ipc, e):
            if e.container.name == title:
                self.id = e.container.id
                self.con = e.container
                ipc.main_quit()

        sway.ipc.on('window::new', on_window_new)
        sway.ipc.main(timeout=5)
        sway.ipc.off(on_window_new)

        if self.con == None:
            raise Exception('could not open a new window')

    def close(self):
        self.con.command('kill')

        def on_window_close(ipc, e):
            if e.container.name == self.title:
                ipc.main_quit()

        self.sway.ipc.on('window::close', on_window_close)
        self.sway.ipc.main(timeout=5)
        self.sway.ipc.off(on_window_close)

    def focus(self):
        self.con.command('focus')

    def command(self, cmd):
        self.con.command(cmd)


class Sway:
    window_counter = 1

    def __init__(self, ipc, display, variant):
        self.ipc = ipc
        self.display = display
        self.variant = variant

    def open_window(self, title=None):
        if not title:
            title = 'window-%d' % Sway.window_counter
            Sway.window_counter += 1

        return TestWindow(self, title)

    def focused(self):
        root = self.ipc.get_tree()
        return root.find_focused()

    def cmd(self, content):
        return self.ipc.command(content)

    def workspace(self):
        return self.ipc.get_tree().find_focused().workspace()
