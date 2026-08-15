import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from gui import Gui

def main():
    width, height = 1000, 700

    w = ttk.Window(title='MyStocker (Unsaved)')
    w.iconbitmap('Icon.ico')
    # w.style.configure('Custom.TNotebook.Tab')

    screen_width = w.winfo_screenwidth()
    screen_height = w.winfo_screenheight()
    xcenter = (screen_width // 2) - (width // 2)
    ycenter = (screen_height // 2) - (height // 2)

    w.geometry(f'{width}x{height}+{xcenter}+{ycenter}')
    w.grid_columnconfigure(0,weight=1)
    w.grid_rowconfigure(0,weight=1)

    Frame = Gui(w)
    Frame.grid(column=0,row=0)

    w.protocol("WM_DELETE_WINDOW", Frame.script.OnClosing) 
    w.mainloop()

if __name__ == '__main__':
    main()
