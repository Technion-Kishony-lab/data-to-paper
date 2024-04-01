import tkinter as tk
from tkinter import scrolledtext


def edit_text_gui(initial_text="", title="Text Editor", width=40, height=10):
    """
    GUI text editor that allows the user to edit provided text.
    """

    def submit():
        global edited_text
        edited_text = text_area.get("1.0", tk.END)
        root.destroy()

    root = tk.Tk()
    root.title(title)

    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=width, height=height)
    text_area.pack(padx=10, pady=10)
    text_area.insert(tk.INSERT, initial_text)

    save_button = tk.Button(root, text="Submit", command=submit)
    save_button.pack(pady=10)

    edited_text = None
    root.mainloop()
    return edited_text
