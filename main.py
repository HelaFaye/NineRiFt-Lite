import os
from threading import Thread
from kivy.app import App
from kivy.clock import Clock
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
try:
    from kivymd.toast import toast
except:
    print('no toast for you')
from fwupd import FWUpd
from fwget import FWGet

thread = Thread()

class NineRiFt(App):

# define helper functions
    def initilize_global_vars(self):
        self.root_folder = self.user_data_dir
        self.cache_folder = os.path.join(self.root_folder, 'cache')
        self.fwget = FWGet(self.cache_folder)
        self.fwupd = FWUpd()
        self.model = 'esx'
        self.versel = False
        self.hasextbms = False
        self.flashprog = 0
        self.flashmaxprog = 100
        self.part = ''

        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)

    @mainthread
    def update_flash_progress(self, var):
        self.flashprog = self.fwupd.getprog()
        self.flashmaxprog = self.fwupd.getmaxprog()
        if var is 'prog':
            return self.flashprog
        if var is 'max':
            return self.flashmaxprog

    def fwget_preload(self):
        self.fwget.setRepo("https://files.scooterhacking.org/"+self.model+"/fw/repo.json")
        self.fwget.loadRepo(self.fwget.repoURL)


    def fwget_reload(self, mod):
        self.model = mod
        self.fwget.setModel(mod)
        self.fwget.setRepo("https://files.scooterhacking.org/" + self.model + "/fw/repo.json")
        self.fwget.loadRepo(self.fwget.repoURL)


    def fwget_func(self, dev, ver):
        global thread
        if thread.isAlive() == False:
            thread = Thread(target=self.fwget.Gimme, args=(dev, ver))
            thread.start()
        else:
            try:
                toast("download already in progress!")
            except:
                print("download already in progress!")


    def fwupd_func(self, sel):
        global thread
        if thread.isAlive() == False:
            thread = Thread(target=self.fwupd.Flash, args=(sel,))
            thread.start()
        else:
            try:
                toast("Firmware update already in progress!")
            except:
                print("Firmware update already in progress!")


# define build for Kivy UI
    def build(self):
        self.initilize_global_vars()
        sm = ScreenManager()

        def switch_screen(scrn):
            sm.current = scrn

        def fwget_dynver(sel):
            fwget_verselspin.values = []
            if sel == 'BLE':
                dev = self.fwget.BLE
            elif sel == 'BMS':
                dev = self.fwget.BMS
            elif sel == 'DRV':
                dev = self.fwget.DRV
            for i in dev:
                fwget_verselspin.values.append(str(i))
            return fwget_verselspin.values


# flash screen file filters
        def selfile_filter(vers, dev):
            check = ['!.md5']
            if self.model is 'm365':
                if dev is 'DRV':
                    if vers=='>=141':
                        sf = ['*.bin.enc']
                        selfile.filters = sf+check
                    if vers=='<141':
                        sf = ['*.bin']
                        selfile.filters = sf+check
                    else:
                        sf = ['*.bin']
                        selfile.filters = sf+check
            elif self.model is 'm365pro':
                sf = ['*.bin.enc']
                selfile.filters = sf+check
            else:
                sf = ['*.bin.enc']
                selfile.filters = sf+check
            flashmidlayout.remove_widget(selfile)
            flashmidlayout.add_widget(selfile)
            flashmidlayout.do_layout()


# model selection function that updates UI and protocol based on selected vehicle model
        def modsel_func(mod):
            if self.versel is True:
                flashtopbtnlayout.remove_widget(flash_verselspin)
            if mod.startswith('m365'):
                self.hasextbms = False
                self.fwupd.setproto('xiaomi')
                if mod is 'm365':
                    self.versel = True
                elif mod is 'm365pro':
                    self.versel = False
            else:
                self.fwupd.setproto('ninebot')
                self.versel = False
                if mod is 'esx':
                    self.hasextbms = True
                    selfile_filter(flash_verselspin.text, self.part)
            if self.hasextbms is True:
                try:
                    devselspin.values.append('ExtBMS')
                except:
                    print('ExtBMS entry already present')
            if self.hasextbms is False:
                try:
                    devselspin.values.remove('ExtBMS')
                except:
                    print('no ExtBMS entry to remove')
            if self.versel is True:
                flashtopbtnlayout.add_widget(flash_verselspin)
            self.model = mod
            selfile_filter(flash_verselspin.text, self.part)
            flashtopbtnlayout.do_layout()

        def setdevice(dev):
            self.part = dev
            self.fwupd.setdev(self.part)
            selfile_filter(flash_verselspin.text, self.part)


        flashscreen = Screen(name='Flash')
        downloadscreen = Screen(name='Download')

# define all  the UI elements
        seladdr_label = Label(text="Addr:", font_size='12sp', height='15sp',
         size_hint_y=1, size_hint_x=.08)
        seladdr_input = TextInput(multiline=False, text='',
        height='15sp', font_size='12sp', size_hint_x=.92, size_hint_y=1)
        seladdr_input.bind(on_text_validate=lambda x: self.fwupd.setaddr(seladdr_input.text))
        selfile_label = Label(text="FW file:", font_size='12sp', size_hint_x=1, height='12sp')
        protoselspin = Spinner(text='Model', values=('xiaomi','ninebot'),
                               font_size='12sp',height='14sp', sync_height=True)
        protoselspin.bind(text=lambda x, y: self.fwupd.setproto(protoselspin.text))
        ifaceselspin = Spinner(text='Interface', values=('TCP', 'Serial', 'BLE'),
                                   font_size='12sp',height='14sp', sync_height=True)
        ifaceselspin.bind(text=lambda x, y: self.fwupd.setiface(ifaceselspin.text))
        devselspin = Spinner(text='Part', values=('BLE', 'DRV', 'BMS'),
                             sync_height=True, font_size='12sp', height='14sp')
        devselspin.bind(text=lambda x, y: setdevice(devselspin.text))
        lockselspin = Spinner(text='Lock', values=('lock', 'nolock'),
                               font_size='12sp',height='14sp', sync_height=True)
        lockselspin.bind(text=lambda x, y: self.fwupd.setnl(lockselspin.text))
        flash_modelselspin = Spinner(text='Model', values=('esx', 'm365', 'm365pro'),
                                     sync_height=True, font_size = '12sp', height = '14sp')
        flash_modelselspin.bind(text=lambda x, y: modsel_func(flash_modelselspin.text))
        flash_verselspin = Spinner(text='Version', values=('<141', '>=141'),
                                    sync_height=True, font_size = '12sp', height = '14sp')
        flash_verselspin.bind(text=lambda x, y: selfile_filter(flash_verselspin.text, self.part))

        flashpb = ProgressBar(size_hint_x=0.35, value=0, max=100)
        flashpb.bind(max=lambda x: update_flash_progress('max'))
        flashpb.bind(value=lambda x: update_flash_progress('prog'))
        selfile = FileChooserListView(path=self.cache_folder)


        flash_button = Button(text="Flash It!", font_size='12sp', height='14sp',
                              on_press=lambda x: self.fwupd_func(selfile.selection[0]))

        fwget_modelselspin = Spinner(text='Model', values=('esx', 'm365', 'm365pro'),
                                   sync_height=True, font_size='12sp', height='14sp')
        fwget_modelselspin.bind(text=lambda x, y: self.fwget_reload(fwget_modelselspin.text))
        fwget_devselspin = Spinner(text='Part', values=('BLE', 'DRV', 'BMS'),
                                   sync_height=True, font_size='12sp', height='14sp')
        fwget_verselspin = Spinner(text='Version', sync_height=True,
                                   font_size='12sp', height='14sp', values=[], text_autoupdate=True)


        self.fwget_preload()
        fwget_devselspin.bind(text=lambda x, y: fwget_dynver(fwget_devselspin.text))
        fwget_download_button = Button(text="Download It!", font_size='12sp', height='14sp',
                                       on_press=lambda x: self.fwget_func(fwget_devselspin.text, fwget_verselspin.text))

        fwupd_screen_btn = Button(text="Flash", font_size='12sp', height='14sp',
                                  on_press=lambda x: switch_screen('Flash'))
        fwget_screen_btn = Button(text="Download", font_size='12sp', height='14sp',
                                  on_press=lambda x: switch_screen('Download'))

# piece together flash screen contents
        flashtoplayout = GridLayout(rows=2, size_hint_y=.2)
        flashaddrlayout = BoxLayout(orientation='horizontal', size_hint_y=.3)
        flashaddrlayout.add_widget(seladdr_label)
        flashaddrlayout.add_widget(seladdr_input)
        flashtopbtnlayout = GridLayout(cols=4, size_hint_y=.7)
        flashtopbtnlayout.add_widget(flash_modelselspin)
        flashtopbtnlayout.add_widget(ifaceselspin)
        flashtopbtnlayout.add_widget(devselspin)
        flashtopbtnlayout.add_widget(lockselspin)
        flashtoplayout.add_widget(flashaddrlayout)
        flashtoplayout.add_widget(flashtopbtnlayout)
        flashmidlayout = BoxLayout(orientation='vertical', size_hint_y=.70)
        flashmidlabelbox = AnchorLayout(anchor_y='top', size_hint_y=.1)
        flashmidlabelbox.add_widget(selfile_label)
        flashmidlayout.add_widget(flashmidlabelbox)
        flashmidlayout.add_widget(selfile)
# run file filter function to hide md5 files
        selfile_filter(None, None)
        flashbotlayout = GridLayout(rows=2, size_hint_y=.15)
        flashbotlayout.add_widget(flash_button)
        flashbotlayout.add_widget(flashpb)
        flashlayout = GridLayout(cols=1, rows=3)
        flashlayout.add_widget(flashtoplayout)
        flashlayout.add_widget(flashmidlayout)
        flashlayout.add_widget(flashbotlayout)


# piece together download screen contents
        fwget_toplayout = AnchorLayout(anchor_y='top', size_hint_y=.15)
        fwget_topbtnlayout = GridLayout(cols=3)
        fwget_topbtnlayout.add_widget(fwget_modelselspin)
        fwget_topbtnlayout.add_widget(fwget_devselspin)
        fwget_topbtnlayout.add_widget(fwget_verselspin)
        fwget_toplayout.add_widget(fwget_topbtnlayout)
        fwget_midlayout = BoxLayout(orientation='vertical', size_hint_y=.70)
        fwget_botlayout = AnchorLayout(anchor_y='bottom', size_hint_y=.15)
        fwget_botlayout.add_widget(fwget_download_button)


        downloadlayout = GridLayout(cols=1, rows=3)
        downloadlayout.add_widget(fwget_toplayout)
        downloadlayout.add_widget(fwget_midlayout)
        downloadlayout.add_widget(fwget_botlayout)

# make switcher layout that stays at the top of the mainlayout
        switcherlayout = BoxLayout(orientation='horizontal', size_hint_y=.08)
        switcherlayout.add_widget(fwupd_screen_btn)
        switcherlayout.add_widget(fwget_screen_btn)

# piece together the mainlayout
        mainlayout = GridLayout(cols=1, rows=2)
        mainlayout.add_widget(switcherlayout)

# add the layouts to the screens
        flashscreen.add_widget(flashlayout)
        downloadscreen.add_widget(downloadlayout)

# add the screens to the screen manager
        sm.add_widget(flashscreen)
        sm.add_widget(downloadscreen)

# add the screen manager to the mainlayout and return the constructed UI
        mainlayout.add_widget(sm)
        return mainlayout


if __name__ == "__main__":
    NineRiFt().run()
