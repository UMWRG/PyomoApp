a = Analysis(['PyomoAutoRun.py'],
             pathex=['..\\lib\\'],
             hiddenimports=['pyutilib.component.core', 'coopr.pyomo','coopr.environ', 'coopr.opt.plugins','coopr.os.plugins','coopr.pysp.plugins','coopr.neos.plugins','coopr.openopt.plugins','coopr.gdp.plugins','coopr.mpec.plugins','coopr.dae.plugins','coopr.bilevel.plugins'],
             hookspath=None,
             runtime_hooks=None,
             excludes=['_tkinter', 'IPython', 'win32ui', 'cPickle', 'win32com', 'sqlalchemy', 'sqlite3', 'pyexpat'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='PyomoAutoRun.exe',
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
               name='PyomoAutoRun')
