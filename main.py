from __future__ import absolute_import
from sys import exit
import os
import threading

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
#from kivy.uix.progressbar import ProgressBar
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
    def build(self):
        root_folder = getattr(self, 'user_data_dir')
        cache_folder = os.path.join(root_folder, 'cache')
        fwget = FWGet(cache_folder)
        fwupd = FWUpd()
        sm = ScreenManager()
        def switch_screen(scrn):
            sm.current = scrn
        flashscreen = Screen(name='Flash')
        downloadscreen = Screen(name='Download')


        seladdr_label = Label(text="Addr:", font_size='12sp', height='15sp',
         size_hint_y=1, size_hint_x=.08)
        seladdr_input = TextInput(multiline=False, text='',
        height='15sp', font_size='12sp', size_hint_x=.92, size_hint_y=1)
        seladdr_input.bind(on_text_validate=lambda x: fwupd.setaddr(seladdr_input.text))
        selfile_label = Label(text="FW file:", font_size='12sp', size_hint_x=1, height='12sp')
        if platform != 'android':
            ifaceselspin = Spinner(text='Interface', values=('TCP', 'Serial', 'BLE')
        , font_size='12sp',height='14sp', sync_height=True)
        elif platform == 'android':
            ifaceselspin = Spinner(text='Interface', values=('TCP', 'BLE')
        , font_size='12sp',height='14sp', sync_height=True)
        ifaceselspin.bind(text=lambda x, y: fwupd.setiface(ifaceselspin.text))
        devselspin = Spinner(text='Device', values=('BLE', 'ESC', 'BMS', 'ExtBMS'),
         sync_height=True, font_size='12sp', height='14sp')
        devselspin.bind(text=lambda x, y: fwupd.setdev(devselspin.text))

        selfile = FileChooserListView(path=cache_folder)
        flash_button = Button(text="Flash It!", font_size='12sp', height='14sp',
         on_press=lambda x: fwupd.Flash(selfile.selection[0]))

        switcherlayout = BoxLayout(orientation='horizontal', size_hint_y=.08)
        flashtoplayout = GridLayout(rows=2, size_hint_y=.2)
        flashaddrlayout = BoxLayout(orientation='horizontal', size_hint_y=.3)
        flashaddrlayout.add_widget(seladdr_label)
        flashaddrlayout.add_widget(seladdr_input)
        #flashtopbtnlayout = GridLayout(orientation='horizontal', cols=3, size_hint_y=.7)
        flashtopbtnlayout = GridLayout(cols=2, size_hint_y=.7)
        # topbtnlayout.add_widget(ble_button)
        # topbtnlayout.add_widget(esc_button)
        # topbtnlayout.add_widget(bms_button)
        # topbtnlayout.add_widget(ebms_button)
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
        flashbotlayout = BoxLayout(orientation='vertical', size_hint_y=.15)
        flashbotlayout.add_widget(flash_button)
        #botlayout.add_widget(pb)

        flashlayout = GridLayout(cols=1, rows=3)
        flashlayout.add_widget(flashtoplayout)
        flashlayout.add_widget(flashmidlayout)
        flashlayout.add_widget(flashbotlayout)

        fwget_devselspin = Spinner(text='Device', values=('BLE', 'DRV', 'BMS'),
         sync_height=True, font_size='12sp', height='14sp')
        fwget_verselspin = Spinner(text='Version', sync_height=True,
         font_size='12sp', height='14sp', values = [], text_autoupdate = True)

        def fwget_preload():
            fwget.setRepo("https://files.scooterhacking.org/esx/fw/repo.json")
            fwget.loadRepo(fwget.repoURL)
        fwget_preload()

        def fwget_dynver(sel):
            fwget_verselspin.values = []
            if sel == 'BLE':
                dev = fwget.BLE
            elif sel == 'BMS':
                dev = fwget.BMS
            elif sel == 'DRV':
                dev = fwget.DRV
            for i in dev:
                fwget_verselspin.values.append(str(i))
            return fwget_verselspin.values

        def fwget_thread():
            fwthread = threading.Thread(target=fwget.Gimme(fwget_devselspin.text, fwget_verselspin.text))
            fwthread.start()
            try:
                toast('download finished')
            except:
                print('download finished')

        fwget_devselspin.bind(text=lambda x, y: fwget_dynver(fwget_devselspin.text))
        fwget_download_button = Button(text="Download It!", font_size='12sp', height='14sp',
         on_press=lambda x: fwget_thread())

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

        fwupd_screen_btn = Button(text="Flash", font_size='12sp', height='14sp',
         on_press=lambda x: switch_screen('Flash'))
        fwget_screen_btn = Button(text="Download", font_size='12sp', height='14sp',
         on_press=lambda x: switch_screen('Download'))

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
