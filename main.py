import os
from threading import Thread
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.utils import platform
from kivy.properties import BooleanProperty

from utils import tprint, sidethread
from fwupd import FWUpd
from fwget import FWGet
from nbcmd import Command
from nbclient import Client



class MainWindow(BoxLayout):
    pass


class NineRiFt(App):
    def initialize(self):
        self.root_folder = self.user_data_dir
        self.cache_folder = os.path.join(self.root_folder, 'cache')

        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)

        self.conn = Client()
        self.conn.bind(on_error=lambda a,b: tprint(b))

        self.fwupd = FWUpd(self.conn)
        self.fwget = FWGet(self.cache_folder)

        self.versel = BooleanProperty(False)
        self.hasextbms = BooleanProperty(False)

    def build(self):
        self.initialize()

        return MainWindow()

    def connection_toggle(self):
        if self.conn.state == 'connected':
            self.conn.disconnect()
        elif self.conn.state == 'disconnected':
            self.conn.connect()

    @sidethread
    def fwget_select_model(self, screen, mod):
        self.fwget.setModel(mod)
        self.fwget.setRepo("https://files.scooterhacking.org/" + mod + "/fw/repo.json")
        self.fwget.loadRepo(self.fwget.repoURL)

    @sidethread
    def fwget_func(self, dev, version):
        self.fwget.Gimme(dev, version)

    def selfile_filter(self, mod, vers, dev):
            check = ['!.md5']
            filters = []
            if mod is 'm365':
                if dev is 'DRV':
                    if vers=='>=141':
                        sf = ['*.bin.enc']
                        filters = sf+check
                    if vers=='<141':
                        sf = ['*.bin']
                        filters = sf+check
                else:
                    sf = ['*.bin']
                    filters = sf+check
            if mod is 'm365pro':
                if dev is 'DRV':
                    sf = ['*.bin.enc']
                    filters = sf+check
                else:
                    sf = ['*.bin']
                    filters = sf+check
            if mod is 'esx':
                sf = ['*.bin.enc']
                filters = sf+check
            print('selfile_filter set to %s' % filters)
            return filters

    @mainthread
    def fwget_update_versions(self, screen):
        sel = screen.ids.part.text
        if sel == 'BLE':
            dev = self.fwget.BLE
        elif sel == 'BMS':
            dev = self.fwget.BMS
        elif sel == 'DRV':
            dev = self.fwget.DRV
        else:
            dev = []
        versions = [str(e) for e in dev]
        screen.ids.version.values = versions
        tprint('FWGet Vers. available: '+str(versions))

    def select_model(self, mod):
        values = ['BLE', 'DRV', 'BMS']
        if mod.startswith('m365'):
            self.hasextbms = False
            if mod is 'm365':
                self.versel = True
            elif mod is 'm365pro':
                self.versel = False
        if mod is 'esx':
            self.versel = False
            self.hasextbms = True
        if self.hasextbms is True:
            try:
                values.append('ExtBMS')
            except:
                print('ExtBMS entry already present')
        if self.hasextbms is False:
            try:
                values.remove('ExtBMS')
            except:
                print('no ExtBMS entry to remove')
        return values

    def on_stop(self):
        self.conn.disconnect()

    def fwupd_func(self, chooser):
        if len(chooser.selection) != 1:
            tprint('Choose file to flash')
            return
        self.fwupd.Flash(chooser.selection[0])


if __name__ == "__main__":
    NineRiFt().run()
