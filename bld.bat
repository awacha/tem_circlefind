"%PYTHON%" setup.py install
if errorlevel 1 exit 1
copy menu.json "%PREFIX%"/Menu
if errorlevel 1 exit 1