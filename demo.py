#!/usr/bin/env python3

import os
import json
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

# Global list to store key-value pairs for bulk replacement
bulk_replace_pairs = []
selected_theme = "Standard"  # Default theme

class BulkReplaceDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        self.pairs = bulk_replace_pairs.copy()  # Use a copy to avoid modifying the global list directly
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Enter key-value pairs for bulk replace:").grid(row=0, columnspan=2)

        self.key_entry = tk.Entry(master)
        self.key_entry.grid(row=1, column=0, padx=5, pady=5)

        self.value_entry = tk.Entry(master)
        self.value_entry.grid(row=1, column=1, padx=5, pady=5)

        self.add_button = tk.Button(master, text="Add", command=self.add_pair)
        self.add_button.grid(row=1, column=2, padx=5, pady=5)

        self.pairs_listbox = tk.Listbox(master, height=6, width=50)
        self.pairs_listbox.grid(row=2, columnspan=3, padx=5, pady=5)

        self.remove_button = tk.Button(master, text="Remove", command=self.remove_pair)
        self.remove_button.grid(row=3, columnspan=3, padx=5, pady=5)

        # Populate the listbox with existing pairs
        for key, value in self.pairs:
            self.pairs_listbox.insert(tk.END, f"{key}: {value}")

        return self.key_entry  # Initial focus

    def add_pair(self):
        key = self.key_entry.get().strip()
        value = self.value_entry.get().strip()
        if key and value:
            self.pairs.append((key, value))
            self.pairs_listbox.insert(tk.END, f"{key}: {value}")
            self.key_entry.delete(0, tk.END)
            self.value_entry.delete(0, tk.END)

    def remove_pair(self):
        selected_index = self.pairs_listbox.curselection()
        if selected_index:
            self.pairs_listbox.delete(selected_index)
            del self.pairs[selected_index[0]]

    def apply(self):
        global bulk_replace_pairs
        bulk_replace_pairs = self.pairs.copy()  # Update the global list with the modified pairs
        self.write_prefs_and_notify()

    def write_prefs_and_notify(self):
        # Call the writePrefs function from the main app class
        app.writePrefs()
        # Show a popup message with the file location
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "ai-editor")
        prefs_file = os.path.join(config_dir, "ai-editor-prefs.json")
        messagebox.showinfo("Preferences Saved", f"Bulk replace preferences have been saved to:\n{prefs_file}")

class SimpleTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Text Editor")

        self.text_area = tk.Text(root, undo=True)
        self.text_area.pack(expand=True, fill='both')

        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        self.create_file_menu()
        self.create_edit_menu()
        self.create_search_menu()

        # Bind hotkeys
        self.bind_hotkeys()

        # Read preferences
        self.readPrefs()

        # Apply the saved theme
        self.apply_theme(selected_theme)

    def create_file_menu(self):
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu, underline=0)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app, accelerator="Alt+F4")

    def create_edit_menu(self):
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu, underline=0)
        edit_menu.add_command(label="Undo", command=self.text_area.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.text_area.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut_text, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy_text, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste_text, accelerator="Ctrl+V")
        edit_menu.add_separator()

        # Create theme submenu
        theme_menu = tk.Menu(edit_menu, tearoff=0)
        edit_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Standard", command=lambda: self.apply_theme("Standard"))
        theme_menu.add_command(label="Dark", command=lambda: self.apply_theme("Dark"))
        theme_menu.add_command(label="Light", command=lambda: self.apply_theme("Light"))

    def create_search_menu(self):
        search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Search", menu=search_menu, underline=0)
        search_menu.add_command(label="Find", command=self.find_text, accelerator="Ctrl+F")
        search_menu.add_command(label="Bulk Replace", command=self.bulk_replace, accelerator="Ctrl+H")

    def bind_hotkeys(self):
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Alt-F4>', lambda e: self.exit_app())
        self.root.bind('<Control-f>', lambda e: self.find_text())
        self.root.bind('<Control-h>', lambda e: self.bulk_replace())

    def new_file(self):
        self.text_area.delete(1.0, tk.END)

    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                content = self.text_area.get(1.0, tk.END)
                file.write(content)

    def cut_text(self):
        self.text_area.event_generate("<<Cut>>")

    def copy_text(self):
        self.text_area.event_generate("<<Copy>>")

    def paste_text(self):
        self.text_area.event_generate("<<Paste>>")

    def find_text(self):
        search_term = simpledialog.askstring("Search", "Enter text to find:")
        if search_term:
            start_pos = self.text_area.search(search_term, "1.0", tk.END)
            if start_pos:
                end_pos = f"{start_pos}+{len(search_term)}c"
                self.text_area.tag_add(tk.SEL, start_pos, end_pos)
                self.text_area.mark_set(tk.INSERT, end_pos)
                self.text_area.see(tk.INSERT)

    def bulk_replace(self):
        dialog = BulkReplaceDialog(self.root, "Bulk Replace")
        if dialog.pairs:
            content = self.text_area.get("1.0", tk.END)
            for key, value in dialog.pairs:
                content = content.replace(key.strip(), value.strip())
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)

    def apply_theme(self, theme):
        global selected_theme
        theme_configs = {
            "Standard": {"bg": "white", "fg": "black", "menu_bg": "lightgrey", "menu_fg": "black"},
            "Dark": {"bg": "#002b36", "fg": "#839496", "menu_bg": "#073642", "menu_fg": "#839496"},
            "Light": {"bg": "#fdf6e3", "fg": "#657b83", "menu_bg": "#eee8d5", "menu_fg": "#657b83"}
        }

        if theme in theme_configs:
            config = theme_configs[theme]
            self.text_area.config(bg=config["bg"], fg=config["fg"])
            self.menu_bar.config(bg=config["menu_bg"], fg=config["menu_fg"])
            self.root.config(bg=config["menu_bg"])
            selected_theme = theme  # Update the selected theme

    def readPrefs(self):
        global bulk_replace_pairs, selected_theme
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "ai-editor")
        prefs_file = os.path.join(config_dir, "ai-editor-prefs.json")

        if os.path.exists(prefs_file):
            with open(prefs_file, 'r') as file:
                prefs = json.load(file)
                bulk_replace_pairs.extend(prefs.get("bulk_replace_pairs", []))
                selected_theme = prefs.get("selected_theme", "Standard")

    def writePrefs(self):
        global bulk_replace_pairs, selected_theme
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "ai-editor")
        os.makedirs(config_dir, exist_ok=True)
        prefs_file = os.path.join(config_dir, "ai-editor-prefs.json")

        prefs = {"bulk_replace_pairs": bulk_replace_pairs, "selected_theme": selected_theme}
        with open(prefs_file, 'w') as file:
            json.dump(prefs, file)

    def exit_app(self):
        self.writePrefs()
        self.root.quit()

def main():
    global app
    root = tk.Tk()
    app = SimpleTextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
