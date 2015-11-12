a = Analysis(['PyomoAutoRun.py'],
             pathex=['..\\lib\\'],
             hiddenimports=['pyomo.core.plugins', 'pyomo.scripting.plugins' , 'pyutilib.component.core', 'pyomo','pyomo.environ', 'pyomo.checker.plugins','pyomo.opt.plugins','pyomo.os.plugins','pyomo.pysp.plugins','pyomo.neos.plugins','pyomo.openopt.plugins','pyomo.gdp.plugins','pyomo.mpec.plugins','pyomo.dae.plugins','pyomo.bilevel.plugins'],
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
