from __future__ import print_function
from sys import exit
import os

from kivy.app import App

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput

from .fwupd import FWUpd as fwupd


class NineRiFt(App):

	def build(self):
		root_folder = getattr(self, 'user_data_dir')
		cache_folder = os.path.join(root_folder, 'cache')

		title_label = Label(text="NineRiFt", font_size='12sp',
		 size_hint_x=1, height='16sp')

		seladdr_label = Label(text="Addr:", font_size='12sp', height='14sp',
		 size_hint_y=1, size_hint_x=.08)

		seladdr_input = TextInput(multiline=False, text='',
		height='12sp', font_size='12sp', size_hint_x=.92, size_hint_y=1)

		seladdr_input.bind(on_text_validate=lambda x: fwupd.setdev(seladdr_input.text))

		selfile_label = Label(text="FW file:", font_size='12sp', size_hint_x=1, height='12sp')

		ble_button = Button(text="BLE", font_size='12sp', height='15sp',
		 on_press=lambda x:fwupd.setdev('ble'))

		esc_button = Button(text="ESC", font_size='12sp', height='15sp',
		 on_press=lambda x:fwupd.setdev('esc'))

		bms_button = Button(text="BMS", font_size='12sp', height='15sp',
		 on_press=lambda x:fwupd.setdev('bms'))

		ebms_button = Button(text="EBMS", font_size='12sp', height='15sp',
		 on_press=lambda x:fwupd.setdev('extbms'))

		selfile = FileChooserListView(path=cache_folder)

		flash_button = Button(text="Flash", font_size='15sp', height='16sp',
		 on_press=lambda x:fwupd.Flash(selfile.selection[0]))

		titlelayout = BoxLayout(orientation='vertical', size_hint_y=.15)
		titlelayout.add_widget(title_label)

		toplayout = GridLayout(rows=2, size_hint_y=.2)
		addrlayout = BoxLayout(orientation='horizontal', size_hint_y=.3)
		addrlayout.add_widget(seladdr_label)
		addrlayout.add_widget(seladdr_input)
		topbtnlayout = BoxLayout(orientation='horizontal', size_hint_y=.7)
		topbtnlayout.add_widget(ble_button)
		topbtnlayout.add_widget(esc_button)
		topbtnlayout.add_widget(bms_button)
		topbtnlayout.add_widget(ebms_button)
		toplayout.add_widget(addrlayout)
		toplayout.add_widget(topbtnlayout)

		midlayout = BoxLayout(orientation='vertical', size_hint_y=.85)
		midlabelbox = AnchorLayout(anchor_y='top', size_hint_y=.1)
		midlabelbox.add_widget(selfile_label)
		midlayout.add_widget(midlabelbox)
		midlayout.add_widget(selfile)

		botlayout = BoxLayout(orientation='vertical', size_hint_y=.2)
		botlayout.add_widget(flash_button)
		flash_button = Button(text="Flash", font_size='18sp', height='20sp')
		#botlayout.add_widget(pb)

		mainlayout = GridLayout(cols=1, rows=4)
		mainlayout.add_widget(titlelayout)
		mainlayout.add_widget(toplayout)
		mainlayout.add_widget(midlayout)
		mainlayout.add_widget(botlayout)
		return mainlayout

if __name__ == "__main__":
	NineRiFt().run()
