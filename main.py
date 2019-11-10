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
try:
    from kivymd.toast import toast
except:
    print('no toast for you')
from fwupd import FWUpd
from fwget import FWGet
from nbcmd import Command

thread0 = Thread()
thread1 = Thread()

# toast or print
def tprint(msg):
    try:
        toast(msg)
    except:
        print(msg)



class NineRiFt(App):

# define helper functions
    def initilize_global_vars(self):
        self.root_folder = self.user_data_dir
        self.cache_folder = os.path.join(self.root_folder, 'cache')
        self.fwget = FWGet(self.cache_folder)
        self.fwupd = FWUpd()
        self.cm = Command()
        self.versel = False
        self.hasextbms = False
        self.command = None
        self.cmdarg = None
        self.connected = False

        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)


# hopefully update the progress bar
    @mainthread
    def update_flash_progress(self, var):
        if var is 'prog':
            return self.fwupd.getprog()
        if var is 'max':
            return self.fwupd.getmaxprog()


# load firmware repo
    def fwget_load(self, mod):
        tprint("loading Firmware repo")
        self.fwget.setModel(mod)
        self.fwget.setRepo("https://files.scooterhacking.org/" + mod + "/fw/repo.json")
        self.fwget.loadRepo(self.fwget.repoURL)
        tprint("Firmware repo loaded")

# threaded firmware downloading function
    def fwget_func(self, dev, ver):
        global thread1
        if thread1.isAlive() == False:
            tprint("starting firmware download")
            thread1 = Thread(target=self.fwget.Gimme, args=(dev, ver))
            thread1.start()
            tprint("Firmware download started")
        else:
            tprint("download already in progress!")


# threaded firmware flashing function
    def fwupd_func(self, sel):
        global thread0
        if thread0.isAlive() == False:
            thread0 = Thread(target=self.fwupd.Flash, args=(sel,))
            thread0.start()
            tprint("Firmware update started")
        else:
            tprint("Firmware update already in progress!")

# define build for Kivy UI
    def build(self):
        self.initilize_global_vars()
        sm = ScreenManager()

        def switch_screen(scrn):
            sm.current = scrn


# fwget function for loading available firmware versions based on selected part/device
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
            tprint('FWGet Vers. available: '+str(fwget_verselspin.values))
            return fwget_verselspin.values

# cmd function that executes known commands
        def cmd_sel_func(cmd):
            self.command = cmd
            if cmd is 'changesn':
                tprint(cmd)
            if cmd is 'lock':
                tprint(cmd)
            if cmd is 'unlock':
                tprint(cmd)
            if cmd is 'dump':
                tprint(cmd)
            if cmd is 'sniff':
                tprint(cmd)
            if cmd is 'powerdown':
                tprint(cmd)
            if cmd is 'reboot':
                tprint(cmd)
            if cmd is 'info':
                tprint(cmd)

        def cmd_arg_func(carg):
            self.cmdarg = carg
            tprint(carg)

        def cmd_run(cmd, carg):
            tprint(str(cmd)+''+str(carg))

        def cmd_connection_toggle():
            if self.connected is False:
                self.cm.open()
                self.connected = True
                tprint(self.connected)
                cmd_connect_btn.text = "Disconnect"
            else:
                self.cm.close()
                self.connected = False
                tprint(self.connected)
                cmd_connect_btn.text = "Connect"

# flash screen file filters for hiding md5 and showing encoded or not based on model and version of DRV
        def selfile_filter(mod, vers, dev):
            check = ['!.md5']
            if mod is 'm365':
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
            if mod is 'm365pro':
                if dev is 'DRV':
                    sf = ['*.bin.enc']
                    selfile.filters = sf+check
                else:
                    sf = ['*.bin']
                    selfile.filters = sf+check
            if mod is 'esx':
                sf = ['*.bin.enc']
                selfile.filters = sf+check
            print('selfile_filter set to %s' % selfile.filters)
            return selfile.filters
            flashmidlayout.do_layout()


# model selection (esx, m365, m365pro) function that updates UI and protocol based on selected vehicle model
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
                selfile_filter(mod, flash_verselspin.text, devselspin.text)
            if mod is 'esx':
                self.fwupd.setproto('ninebot')
                self.versel = False
                self.hasextbms = True
                selfile_filter(mod, None, devselspin.text)
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
            flashtopbtnlayout.do_layout()


# device (DRV,BMS, etc.) selection function
        def setdevice(dev):
            self.fwupd.setdev(dev)
            selfile_filter(flash_modelselspin.text, flash_verselspin.text, dev)
            flashtopbtnlayout.do_layout()


# define screens
        flashscreen = Screen(name='Flash')
        downloadscreen = Screen(name='Download')
        commandscreen = Screen(name='Command')

# define the UI elements for the screens
# startig with the flash screen
        seladdr_label = Label(text="Addr:", font_size='12sp', height='15sp',
         size_hint_y=1, size_hint_x=.08)
        seladdr_input = TextInput(multiline=False, text='',
        height='15sp', font_size='12sp', size_hint_x=.92, size_hint_y=1)
        seladdr_input.bind(on_text_validate=lambda x, y: self.fwupd.setaddr(seladdr_input.text))
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
                               font_size='12sp',height='14sp', sync_height=True, size_hint_x=.30)
        lockselspin.bind(text=lambda x, y: self.fwupd.setnl(lockselspin.text))
        flash_modelselspin = Spinner(text='Model', values=('esx', 'm365', 'm365pro'),
                                     sync_height=True, font_size = '12sp', height = '14sp')
        flash_modelselspin.bind(text=lambda x, y: modsel_func(flash_modelselspin.text))
        flash_verselspin = Spinner(text='Version', values=('<141', '>=141'),
                                    sync_height=True, font_size = '12sp', height = '14sp')
        flash_verselspin.bind(text=lambda x, y: selfile_filter(flash_modelselspin.text, flash_verselspin.text, devselspin.text))

        flashpb = ProgressBar(size_hint_x=0.35, value=0, max=100)
        flashpb.bind(max=lambda x, y: update_flash_progress('max'))
        flashpb.bind(value=lambda x, y: update_flash_progress('prog'))
        selfile = FileChooserListView(path=self.cache_folder)


        flash_button = Button(text="Flash It!", font_size='12sp', height='14sp',
                              on_press=lambda x, y: self.fwupd_func(selfile.selection[0]))

#then define fwget/download screen elements
        fwget_modelselspin = Spinner(text='Model', values=('esx', 'm365', 'm365pro'),
                                   sync_height=True, font_size='12sp', height='14sp')
        fwget_modelselspin.bind(text=lambda x, y: self.fwget_load(fwget_modelselspin.text))
        fwget_devselspin = Spinner(text='Part', values=('BLE', 'DRV', 'BMS'),
                                   sync_height=True, font_size='12sp', height='14sp')
        fwget_verselspin = Spinner(text='Version', sync_height=True,
                                   font_size='12sp', height='14sp', values=[], text_autoupdate=True)


        self.fwget_load('esx')
        fwget_devselspin.bind(text=lambda x, y: fwget_dynver(fwget_devselspin.text))
        fwget_download_button = Button(text="Download It!", font_size='12sp', height='14sp',
                                       on_press=lambda x, y: self.fwget_func(fwget_devselspin.text, fwget_verselspin.text))


# TODO define command screen elements
        cmd_seladdr_label = Label(text="Addr:", font_size='12sp', height='15sp',
         size_hint_y=1, size_hint_x=.08)
        cmd_seladdr_input = TextInput(multiline=False, text='',
        height='15sp', font_size='12sp', size_hint_x=.92, size_hint_y=1)
        cmd_seladdr_input.bind(on_text_validate=lambda x: self.cm.setaddr(cmd_seladdr_input.text))
        cmd_protoselspin = Spinner(text='protocol', values=('xiaomi','ninebot'),
                               font_size='12sp',height='14sp', sync_height=True)
        cmd_protoselspin.bind(text=lambda x, y: self.cm.setproto(cmd_protoselspin.text))
        cmd_ifaceselspin = Spinner(text='interface', values=('TCP', 'Serial', 'BLE'),
                                   font_size='12sp',height='14sp', sync_height=True)
        cmd_ifaceselspin.bind(text=lambda x, y: self.cm.setiface(cmd_ifaceselspin.text))
        cmd_cmdselspin = Spinner(text='cmd', values=('lock','unlock','dump','sniff',
                                    'powerdown', 'reboot', 'info', 'changesn'),
                                    font_size='12sp',height='14sp', sync_height=True)
        cmd_cmdselspin.bind(text=lambda x, y: cmd_sel_func(cmd_cmdselspin.text))
        cmd_arglabel = Label(text="Argument:")
        cmd_argument = TextInput(multiline=False, text='', height='15sp', font_size='12sp', size_hint_y=1)
        cmd_argument.bind(on_text_validate=lambda x: cmd_arg_func(cmd_argument.text))
        cmd_connect_btn = Button(text="Connect", font_size='12sp', height='14sp',
                                       on_press=lambda x: cmd_connection_toggle())
        cmd_output = Label(text="")
        cmd_execute_btn = Button(text="Execute", font_size='12sp', height='14sp',
                                       on_press=lambda x: cmd_run(self.command, self.cmdarg))
# piece together flash screen contents
        flashtoplayout = GridLayout(rows=2, size_hint_y=.25)
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
        flashmidlayout = BoxLayout(orientation='vertical', size_hint_y=.65)
        flashmidlabelbox = AnchorLayout(anchor_y='top', size_hint_y=.1)
        flashmidlabelbox.add_widget(selfile_label)
        flashmidlayout.add_widget(flashmidlabelbox)
        flashmidlayout.add_widget(selfile)
# run file filter function to hide md5 files
        selfile_filter(None, None, None)
        flashbotlayout = GridLayout(rows=2, size_hint_y=.10)
        flashbotlayout.add_widget(flash_button)
        flashbotlayout.add_widget(flashpb)
        flashlayout = GridLayout(cols=1, rows=3)
        flashlayout.add_widget(flashtoplayout)
        flashlayout.add_widget(flashmidlayout)
        flashlayout.add_widget(flashbotlayout)

#define screen switcher button
        fwupd_screen_btn = Button(text="Flash", font_size='12sp', height='14sp',
                                  on_press=lambda x: switch_screen('Flash'))

# piece together download screen contents
        fwget_toplayout = AnchorLayout(anchor_y='top', size_hint_y=.25)
        fwget_topbtnlayout = GridLayout(cols=3)
        fwget_topbtnlayout.add_widget(fwget_modelselspin)
        fwget_topbtnlayout.add_widget(fwget_devselspin)
        fwget_topbtnlayout.add_widget(fwget_verselspin)
        fwget_toplayout.add_widget(fwget_topbtnlayout)
        fwget_midlayout = BoxLayout(orientation='vertical', size_hint_y=.65)
        fwget_botlayout = AnchorLayout(anchor_y='bottom', size_hint_y=.10)
        fwget_botlayout.add_widget(fwget_download_button)
        downloadlayout = GridLayout(cols=1, rows=3)
        downloadlayout.add_widget(fwget_toplayout)
        downloadlayout.add_widget(fwget_midlayout)
        downloadlayout.add_widget(fwget_botlayout)

#define screen switcher button
        fwget_screen_btn = Button(text="Download", font_size='12sp', height='14sp',
                                  on_press=lambda x: switch_screen('Download'))

# TODO piece together command screen contents
        cmdaddrlayout = BoxLayout(orientation='horizontal', size_hint_y=.3)
        cmdaddrlayout.add_widget(cmd_seladdr_label)
        cmdaddrlayout.add_widget(cmd_seladdr_input)
        cmdtopbtnlayout = GridLayout(cols=3, size_hint_y=.7)
        cmdtopbtnlayout.add_widget(cmd_protoselspin)
        cmdtopbtnlayout.add_widget(cmd_ifaceselspin)
        cmdtopbtnlayout.add_widget(cmd_connect_btn)
        cmdtoplayout = GridLayout(rows=3, size_hint_y=.25)
        cmdtoplayout.add_widget(cmdaddrlayout)
        cmdtoplayout.add_widget(cmdtopbtnlayout)
        cmdsellayout = BoxLayout(orientation='vertical', size_hint_y=.5)
        cmdsellayout.add_widget(cmd_cmdselspin)
        cmdsellayout.add_widget(cmd_arglabel)
        cmdsellayout.add_widget(cmd_argument)
        cmdmidlayout = BoxLayout(orientation='vertical', size_hint_y=.65)
        cmdmidlayout.add_widget(cmdsellayout)
        cmdmidlayout.add_widget(cmd_output)
        cmdbotlayout = AnchorLayout(anchor_y='bottom', size_hint_y=.10)
        cmdbotlayout.add_widget(cmd_execute_btn)
        commandlayout = GridLayout(cols=1, rows=3)
        commandlayout.add_widget(cmdtoplayout)
        commandlayout.add_widget(cmdmidlayout)
        commandlayout.add_widget(cmdbotlayout)

#define screen switcher button
        cmd_screen_btn = Button(text="Command", font_size='12sp', height='14sp',
                              on_press=lambda x: switch_screen('Command'))

# make switcher layout that stays at the top of the mainlayout
        switcherlayout = BoxLayout(orientation='horizontal', size_hint_y=.08)
        switcherlayout.add_widget(fwupd_screen_btn)
        switcherlayout.add_widget(fwget_screen_btn)
        switcherlayout.add_widget(cmd_screen_btn)

# piece together the mainlayout
        mainlayout = GridLayout(cols=1, rows=2)
        mainlayout.add_widget(switcherlayout)

# add the layouts to the screens
        flashscreen.add_widget(flashlayout)
        downloadscreen.add_widget(downloadlayout)
        commandscreen.add_widget(commandlayout)

# add the screens to the screen manager
        sm.add_widget(flashscreen)
        sm.add_widget(downloadscreen)
        sm.add_widget(commandscreen)

# add the screen manager to the mainlayout and return the constructed UI
        mainlayout.add_widget(sm)
        return mainlayout


if __name__ == "__main__":
    NineRiFt().run()
