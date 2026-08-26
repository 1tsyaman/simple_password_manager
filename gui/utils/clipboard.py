from kivy.core.clipboard import Clipboard

def copy_text(text: str):
	Clipboard.copy(text)