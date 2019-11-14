# -*- mode: python ; coding: utf-8 -*-
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, get_deps_all, hookspath, runtime_hooks
from kivy_deps import sdl2, glew

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/home/ark/NineRiFt-kivy'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=hookspath(),
             runtime_hooks=runtime_hooks(),
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='NineRiFt',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
