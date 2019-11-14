# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['main.py'],
             pathex=['./'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='NineRiFt',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe, Tree('../../'),
               Tree('/Library/Frameworks/SDL2_ttf.framework/Versions/A/Frameworks/FreeType.framework'),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='NineRiFt')

app = BUNDLE(coll,
             name='NineRiFt.app',
             icon=None,
         bundle_identifier=None)
