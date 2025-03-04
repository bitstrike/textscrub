#!/usr/bin/env python3
#!/usr/bin/env python3

import tkinter as tk
from tkinter import simpledialog, messagebox

# Global list to store key-value pairs for bulk replacement
bulk_replace_pairs = []

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

    def create_file_menu(self):
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def create_edit_menu(self):
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.text_area.edit_undo)
        edit_menu.add_command(label="Redo", command=self.text_area.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut_text)
        edit_menu.add_command(label="Copy", command=self.copy_text)
        edit_menu.add_command(label="Paste", command=self.paste_text)

    def create_search_menu(self):
        search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Search", menu=search_menu)
        search_menu.add_command(label="Find", command=self.find_text)
        search_menu.add_command(label="Bulk Replace", command=self.bulk_replace)

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

def main():
    root = tk.Tk()
    app = SimpleTextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
