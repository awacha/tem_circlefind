"%PYTHON%" setup.py install
if errorlevel 1 exit 1
copy menu-temcirclefind.json "%PREFIX%"/Menu
copy tem_circlefind.ico "%PREFIX%"/Menu
if errorlevel 1 exit 1