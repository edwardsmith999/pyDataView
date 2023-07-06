# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.compat import is_win, is_darwin, is_linux
from PyInstaller.utils.hooks import collect_submodules
import vispy.glsl
import vispy.io

block_cipher = None

data_files = [
    (os.path.dirname(vispy.glsl.__file__), os.path.join("vispy", "glsl")),
    (os.path.join(os.path.dirname(vispy.io.__file__), "_data"), os.path.join("vispy", "io", "_data"))
]

if is_darwin:
    hidden_imports = []
else:
    hidden_imports = [
        "vispy.ext._bundled.six",
        "vispy.app.backends._wx",    
    ]

a = Analysis(['pyDataView.py'],
             pathex=[],
             binaries=[],
             datas=data_files,
             hiddenimports=hidden_imports,
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
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='pyDataView',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None)

app = BUNDLE(exe,
             name='pyDataView.app',
             icon='logo.icns',
             info_plist={
                'NSHighResolutionCapable': 'True',
                'NSRequiresAquaSystemAppearance': 'No'
             },             
             bundle_identifier=None)
