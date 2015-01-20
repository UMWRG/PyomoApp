# -*- mode: python -*-
a = Analysis(['PyomoRunImport.py'],
             pathex=['..\\lib'],
             hiddenimports=['pyutilib.workflow', 'pyutilib.component.core'],
             hookspath=None,
             runtime_hooks=None,
             excludes=['_tkinter', 'IPython', 'win32ui', 'cPickle', 'win32com', 'sqlalchemy', 'sqlite3', 'pyexpat'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='PyomoRunImport.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='PyomoRunImport')
