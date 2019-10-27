import os
#from time import sleep
#import threading

from kivy.app import App
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


class NineRiFt(App):

    def initilize_global_vars(self):
        self.root_folder = self.user_data_dir
        self.cache_folder = os.path.join(self.root_folder, 'cache')
        self.fwget = FWGet(self.cache_folder)
        self.fwupd = FWUpd()

        if not os.path.exists(self.cache_folder):
            os.makedirs(self.cache_folder)


    def fwget_preload(self):
        self.fwget.setRepo("https://files.scooterhacking.org/esx/fw/repo.json")
        self.fwget.loadRepo(self.fwget.repoURL)


    # def fwget_func(self, dev, ver):
    #     fwget_thread = threading.Thread(target=self.fwget.Gimme, kwargs=dict(firm=dev, ver=ver))
    #     getting = threading.Event()
    #     if getting.is_set() is False:
    #         getting.set()
    #         fwget_thread.start()
    #         # while threading.activeCount() > 1:
    #         #     sleep(1)
    #         fwget_thread.join()
    #         getting.clear()
    #     else:
    #         try:
    #             toast('already downloading')
    #         except:
    #             print('already downloading')
    #     return

    def fwget_func(self, dev, ver):
        self.fwget.Gimme(dev, ver)


    # def fwupd_func(self, sel):
    #     fwupd_thread = threading.Thread(target=self.fwupd.Flash, kwargs=dict(fwfilep=sel))
    #     flashing = threading.Event()
    #     if flashing.is_set() is False:
    #         flashing.set()
    #         fwupd_thread.start()
    #         # while threading.activeCount() > 1:
    #         #     sleep(1)
    #         fwupd_thread.join()
    #         flashing.clear()
    #     else:
    #         try:
    #             toast('already flashing')
    #         except:
    #             print('already flashing')
    #     return

    def fwupd_func(self, sel):
        self.fwupd.Flash(sel)


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


        flashscreen = Screen(name='Flash')
        downloadscreen = Screen(name='Download')


        seladdr_label = Label(text="Addr:", font_size='12sp', height='15sp',
         size_hint_y=1, size_hint_x=.08)
        seladdr_input = TextInput(multiline=False, text='',
        height='15sp', font_size='12sp', size_hint_x=.92, size_hint_y=1)
        seladdr_input.bind(on_text_validate=lambda x: self.fwupd.setaddr(seladdr_input.text))
        selfile_label = Label(text="FW file:", font_size='12sp', size_hint_x=1, height='12sp')
        if platform != 'android':
            ifaceselspin = Spinner(text='Interface', values=('TCP', 'Serial', 'BLE'),
                                   font_size='12sp',height='14sp', sync_height=True)
        elif platform == 'android':
            ifaceselspin = Spinner(text='Interface', values=('TCP', 'BLE'),
                                   font_size='12sp',height='14sp', sync_height=True)
        ifaceselspin.bind(text=lambda x, y: self.fwupd.setiface(ifaceselspin.text))
        devselspin = Spinner(text='Device', values=('BLE', 'ESC', 'BMS', 'ExtBMS'),
                             sync_height=True, font_size='12sp', height='14sp')
        devselspin.bind(text=lambda x, y: self.fwupd.setdev(devselspin.text))
        flashpb = ProgressBar(size_hint_x=0.35, value=0, max=100)
        flashpb.bind(max=lambda x: self.fwupd.getmaxprog())
        flashpb.bind(value=lambda x: self.fwupd.getprog())
        selfile = FileChooserListView(path=self.cache_folder)
        flash_button = Button(text="Flash It!", font_size='12sp', height='14sp',
                              on_press=lambda x: self.fwupd_func(selfile.selection[0]))


        fwupd_screen_btn = Button(text="Flash", font_size='12sp', height='14sp',
                                  on_press=lambda x: switch_screen('Flash'))
        fwget_devselspin = Spinner(text='Device', values=('BLE', 'DRV', 'BMS'),
                                   sync_height=True, font_size='12sp', height='14sp')
        fwget_verselspin = Spinner(text='Version', sync_height=True,
                                   font_size='12sp', height='14sp', values=[], text_autoupdate=True)

        self.fwget_preload()

        fwget_devselspin.bind(text=lambda x, y: fwget_dynver(fwget_devselspin.text))
        fwget_download_button = Button(text="Download It!", font_size='12sp', height='14sp',
                                       on_press=lambda x: self.fwget_func(fwget_devselspin.text, fwget_verselspin.text))
        fwget_screen_btn = Button(text="Download", font_size='12sp', height='14sp',
                                  on_press=lambda x: switch_screen('Download'))


        switcherlayout = BoxLayout(orientation='horizontal', size_hint_y=.08)
        flashtoplayout = GridLayout(rows=2, size_hint_y=.2)
        flashaddrlayout = BoxLayout(orientation='horizontal', size_hint_y=.3)
        flashaddrlayout.add_widget(seladdr_label)
        flashaddrlayout.add_widget(seladdr_input)
        flashtopbtnlayout = GridLayout(cols=2, size_hint_y=.7)
        flashtopbtnlayout.add_widget(ifaceselspin)
        flashtopbtnlayout.add_widget(devselspin)
        #flashtopbtnlayout.add_widget()
        flashtoplayout.add_widget(flashaddrlayout)
        flashtoplayout.add_widget(flashtopbtnlayout)
        flashmidlayout = BoxLayout(orientation='vertical', size_hint_y=.70)
        flashmidlabelbox = AnchorLayout(anchor_y='top', size_hint_y=.1)
        flashmidlabelbox.add_widget(selfile_label)
        flashmidlayout.add_widget(flashmidlabelbox)
        flashmidlayout.add_widget(selfile)
        flashbotlayout = GridLayout(rows=2, size_hint_y=.15)
        flashbotlayout.add_widget(flash_button)
        flashbotlayout.add_widget(flashpb)
        flashlayout = GridLayout(cols=1, rows=3)
        flashlayout.add_widget(flashtoplayout)
        flashlayout.add_widget(flashmidlayout)
        flashlayout.add_widget(flashbotlayout)


        fwget_toplayout = AnchorLayout(anchor_y='top', size_hint_y=.15)
        fwget_topbtnlayout = GridLayout(cols=2)
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


        switcherlayout.add_widget(fwupd_screen_btn)
        switcherlayout.add_widget(fwget_screen_btn)


        mainlayout = GridLayout(cols=1, rows=2)
        mainlayout.add_widget(switcherlayout)


        flashscreen.add_widget(flashlayout)
        downloadscreen.add_widget(downloadlayout)


        sm.add_widget(flashscreen)
        sm.add_widget(downloadscreen)


        mainlayout.add_widget(sm)
        return mainlayout


if __name__ == "__main__":
    NineRiFt().run()
