pyinstaller --name 'askAi' \
            --icon 'askAi.ico' \
            --windowed  \
            --add-data='./askAi.png:.' \
            --hidden-import=pyperclip  \
            --hidden-import=requests  \
--hidden-import=pydantic  \
            askAi.py