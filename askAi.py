import sys
from pathlib import Path
import pyperclip
import requests
import json
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit,QHBoxLayout,QStatusBar,QProgressBar,QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt,QSize,QSettings,QEvent


import openai
from openai import OpenAI
import os
from os import path

# Define the shared style
button_style = """
    QPushButton {
        border: 2px solid rgb(250,250,250);  
        border-radius: 10px;      
        background-color: black;  
        color: white;             
        padding: 5px;             
    }
    QPushButton:hover {
        background-color: #505050;  
    }
"""

status_style = """
            QStatusBar {
                background-color: #404040;  
                color: white;               
                font-weight: bold;          
                border-top: 1px solid #606060; 
            }
        """

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.answer = ""
        self.clipboard_content=""

    def initUI(self):
        self.setWindowTitle("askAi")
        self.setMinimumSize(500, 300)
        

        self.settings = QSettings("aiTalks", "askAI")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
        

        self.setStyleSheet("background-color: rgb(31, 31, 31);")

        
        # Set the window to be frameless
        #self.setWindowFlags(Qt.FramelessWindowHint)

        # Set the window's opacity
        #self.setWindowOpacity(0.9)  # Adjust opacity from 0.0 (fully transparent) to 1.0 (fully opaque)

        if getattr( sys, 'frozen', False ) :
                # runs in a pyinstaller bundle
                here_dir = sys._MEIPASS
                icon_path = path.join(here_dir, 'askAi.png')
        else :
                here_dir = path.dirname(__file__)
                icon_path = path.join(here_dir, 'askAi.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon file not found: {icon_path}")
        # Layout

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
 


        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet(status_style)

        # Progress Bar (Spinner)
        self.spinner = QProgressBar()
        self.spinner.setRange(0, 0)  # Indeterminate mode
        self.spinner.setVisible(False)  # Hidden by default
        self.status_bar.addPermanentWidget(self.spinner)


       # Label above prompt area
        label = QLabel("Prompt:", self)
        label.setStyleSheet("background-color: rgb(31, 31, 31); color: white;")
        layout.addWidget(label)

        # Prompt Area
        self.prompt_area = QTextEdit(self)
        self.prompt_area.setStyleSheet("background-color: white; color: black;")
        self.prompt_area.setFixedHeight(30)  # Set a fixed height for prompt area
        # Load content from QSettings or set default
        self.prompt_area.setText(self.settings.value("promptText", "sum-up the following text"))
        layout.addWidget(self.prompt_area)


        # Scroll Area
        self.scroll_area = QScrollArea(self)  # Create Scroll Area
        self.scroll_area.setWidgetResizable(True)  # Allow the contained widget to resize

        # Label above message area
        label = QLabel("Answer:", self)
        label.setStyleSheet("background-color: rgb(31, 31, 31); color: white;")
        layout.addWidget(label)

        # Message area
        self.message_area = QLabel("", self)
        self.message_area.setStyleSheet("""background-color: white; 
                                        color: black;""")
        self.message_area.setWordWrap(True)
        self.message_area.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Align text to the left and top

        # Add the message area to the scroll area
        self.scroll_area.setWidget(self.message_area)
        
        # Add the scroll area to the layout
        layout.addWidget(self.scroll_area)
        
        button_layout = QHBoxLayout()

        # Text Button Before
        self.regenerate_button = QPushButton("Regenerate", self)
        self.regenerate_button.clicked.connect(self.on_generate_click)  # Define this method
        self.regenerate_button.setStyleSheet(button_style)
        button_layout.addWidget(self.regenerate_button)

        # Icon Button (Existing Button)
        self.copy_clipboard = QPushButton(self)
        if getattr( sys, 'frozen', False ) :
            # runs in a pyinstaller bundle
            here_dir = sys._MEIPASS
            icon_path = path.join(here_dir, 'askAi.png')
        else :
            here_dir = path.dirname(__file__)
            icon_path = path.join(here_dir, 'askAi.png')
        self.copy_clipboard .setIcon(QIcon(icon_path))  # Set the icon here
        self.copy_clipboard .setIconSize(QSize(64, 64))
        self.copy_clipboard .clicked.connect(self.on_copy_to_clipboard_click)  # Define this method
        button_layout.addWidget(self.copy_clipboard )

        # Text Button After
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(button_style)
        self.close_button.clicked.connect(QApplication.instance().quit)  # Define this method
        button_layout.addWidget(self.close_button)

        # Add the horizontal layout to the main vertical layout
        layout.addLayout(button_layout)

    def enableUI(self,val):
        self.copy_clipboard.setEnabled(val)
        self.regenerate_button.setEnabled(val)
        self.prompt_area

    def closeEvent(self, event):
        # Save the current text of the prompt area to QSettings
        self.settings.setValue("promptText", self.prompt_area.toPlainText())
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def on_copy_to_clipboard_click(self):
        if self.answer=="":
            self.status_bar.showMessage("Nothing to copy to clipboard")
            return
        pyperclip.copy(self.answer)
        QApplication.instance().quit()

    def update_text_box(self, text):
        self.message_area.setText(text)

    def sprint(self, text):
        self.status_bar.showMessage(text)

    def stream_from_lm_server(self, text):
        self.update_text_box("...")
        self.enableUI(False)
        self.spinner.setVisible(True)
        try:
            stream = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": text,
                    }
                ],
                model="gpt-3.5-turbo",
                stream=True,
            )

            self.answer = ""
            try:
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        if content is not None:
                            self.answer += content
                            self.update_text_box(self.answer)
            except Exception as e:
                self.update_text_box(f"Error: {e}")


        except Exception as e:
            if isinstance(e, openai.Timeout):
                self.sprint(f"OpenAI API request timed out: {str(e)}")
            elif isinstance(e, openai.APIError):
                self.sprint(f"OpenAI APIError: {str(e)}")
            elif isinstance(e, openai.APIConnectionError):
                self.sprint(f"OpenAI API request failed to connect: {str(e)}")
            elif isinstance(e, openai.InvalidRequestError):
                self.sprint(f"OpenAI API request was invalid: {str(e)}")
            elif isinstance(e, openai.APICoAuthenticationErrornnectionError):
                self.sprint(f"OpenAI API request was not authorized: {str(e)}")
            elif isinstance(e, openai.PermissionError):
                self.sprint(f"OpenAI API request was not permitted: {str(e)}")
            elif isinstance(e, openai.RateLimitError):
                self.sprint(f"OpenAI API request exceeded rate limit: {str(e)}")
            else:
                self.sprint(f"Error: {str(e)}")

        self.enableUI(True)
        self.spinner.setVisible(False)

    def on_generate_click(self):
        self.clipboard_content = get_clipboard_content()
        if self.clipboard_content:
            threading.Thread(target=self.stream_from_lm_server, args=(self.clipboard_content,), daemon=True).start()
        else :
            self.status_bar.showMessage("No text in clipboard - or contains images")

    def event(self, event):
        if event.type() == QEvent.ActivationChange:
            if self.isActiveWindow():
                self.onFocus()
        return super(MainWindow, self).event(event)

    def onFocus(self):
        # Votre code ici
        clp =get_clipboard_content()
        if clp == self.clipboard_content:
            return
        self.clipboard_content = clp
        if clp:
            threading.Thread(target=self.stream_from_lm_server, args=(clp,), daemon=True).start()

def get_clipboard_content():
    try:
        clipboard_content = pyperclip.paste()
        print(clipboard_content)
        if isinstance(clipboard_content, str):
            return clipboard_content
        else:
            return None
    except Exception as e:
        return None
   

key = os.environ.get("OPENAI_API_KEY")

client = OpenAI(
    api_key="key",
    base_url="http://localhost:1234/v1"
)

app = QApplication(sys.argv)
mainWindow = MainWindow()
mainWindow.show()
mainWindow.on_generate_click()
sys.exit(app.exec_())
