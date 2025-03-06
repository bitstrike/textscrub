#!/usr/bin/env python3

import os
import json
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import signal
import sys

# Global list to store key-value pairs for bulk replacement
bulk_replace_pairs = []
selected_theme = "Standard"  # Default theme

STATUS_MESSAGE_DURATION_MS = 0


class BulkReplaceDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        self.pairs = bulk_replace_pairs.copy()  # Use a copy
        super().__init__(parent, title)


    def body(self, master):
        # Use grid layout consistently
        tk.Label(master, text="Enter key-value pairs for bulk replace:").grid(row=0, columnspan=3, padx=5, pady=5) #expand the columnspan
        self.key_entry = tk.Entry(master)
        self.key_entry.grid(row=1, column=0, padx=5, pady=5)
        self.value_entry = tk.Entry(master)
        self.value_entry.grid(row=1, column=1, padx=5, pady=5)
        self.add_button = tk.Button(master, text="Add", command=self.add_pair)
        self.add_button.grid(row=1, column=2, padx=5, pady=5)
        self.pairs_listbox = tk.Listbox(master, height=6, width=50)
        self.pairs_listbox.grid(row=2, columnspan=3, padx=5, pady=5)

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
            index_to_delete = selected_index[0] #get the first element
            self.pairs_listbox.delete(index_to_delete) #delete the item
            del self.pairs[index_to_delete]          #delete the pair in the pairs list


    def apply(self):
        global bulk_replace_pairs
        bulk_replace_pairs = self.pairs.copy()  # Save the pairs
        self.write_prefs_and_notify()  # Notify about saving
        # Perform the replacement and highlighting
        app.replaceBulk()
        super().apply()  # Close the dialog

    def write_prefs_and_notify(self):
        app.writePrefs()
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "textscrub")
        prefs_file = os.path.join(config_dir, "textscrub-prefs.json")
        app.update_status(f"Bulk hash saved to: {prefs_file}")


    def buttonbox(self):
        """Override the default buttonbox"""
        box = tk.Frame(self)

        # Remove button
        self.remove_button = tk.Button(box, text="Remove Item", command=self.remove_pair)
        self.remove_button.pack(side=tk.LEFT, padx=5)

        #save and replace button - pack it on the left
        w = tk.Button(box, text="Save and Replace", command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5)

        #cancel button - pack it on the left too
        cancel = tk.Button(box, text="Cancel", command=self.cancel)
        cancel.pack(side=tk.LEFT, padx=5)

        box.pack(pady=5) #add pady to the button box
        box.pack(side="top", anchor="center") # Center the button box horizontally


        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

    def cancel(self, event=None):
        """Override cancel button"""
        self.pairs = []  # Reset pairs - no changes
        self.destroy()  # Destroy the dialog


class SimpleTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("TextScrub Editor")

        self.text_area = tk.Text(root, undo=True)
        self.text_area.pack(expand=True, fill='both')

        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        self.create_file_menu()
        self.create_edit_menu()
        self.create_search_menu()
        
        self.create_status_bar()

        # Bind hotkeys
        self.bind_hotkeys()

        # Read preferences
        self.readPrefs()

        # Apply the saved theme
        self.apply_theme(selected_theme)

    def setup_signal_handling(self):
        """
        Set up robust signal handling for clean and immediate application exit.
        
        This method configures the application to respond immediately to 
        interruption signals like SIGINT (Ctrl+C), ensuring:
        - Preferences are saved before exiting
        - Application exits without delay
        - Clean shutdown of resources
        """
        # Use signal.signal to intercept SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, self.handle_signal)
        
        # Optional: Also handle SIGTERM for consistent behavior across different 
        # termination scenarios (e.g., when process is killed)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        """
        Handle interruption signals with immediate and clean exit.
        
        Args:
            signum (int): Signal number received (e.g., signal.SIGINT)
            frame (frame): Current stack frame (not used in this implementation)
        """
        try:
            # Immediately stop any ongoing tkinter main loop
            self.root.after(0, self.root.quit)
            
            # Save application preferences before exiting
            self.writePrefs()
            
            # Print exit message to console
            print(f"\nReceived signal {signum}. Exiting application...")
            
            # Forcefully destroy all windows and exit
            self.root.destroy()
            sys.exit(0)
        except Exception as e:
            # Log any unexpected errors during exit
            print(f"Error during signal handling: {e}")
            sys.exit(1)


        
    def create_status_bar(self):
        """Create a status bar at the bottom of the window."""
        self.status_bar = tk.Label(
            self.root,
            #relief=tk.SUNKEN,
            anchor=tk.W  # Left-aligned text
        )
        self.status_bar.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            padx=2,
            pady=2
        )
    def update_status(self, message, duration=STATUS_MESSAGE_DURATION_MS):
        """Update the status bar with a message.
        Args:
            message (str): Message to display
            duration (int): How long to show the message in milliseconds
        """
        self.status_bar.config(text=message)
        if duration > 0:
            self.root.after(duration, lambda: self.update_status(""))
            
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
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_separator()
        edit_menu.add_command(label="ReplaceBulk", command=self.replaceBulk, accelerator="Ctrl+R")        
        edit_menu.add_command(label="Reverse Replace", command=self.bulk_replace, accelerator="Ctrl+G")


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
        search_menu.add_command(label="Bulk Replace", command=self.bulk_replace, accelerator="Ctrl+B")
    

    def bind_hotkeys(self):
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Alt-F4>', lambda e: self.exit_app())
        self.root.bind('<Control-f>', lambda e: self.find_text())
        self.root.bind('<Control-b>', lambda e: self.bulk_replace())
        self.root.bind('<Control-r>', lambda e: self.replaceBulk())
        self.root.bind('<Control-a>', lambda e: self.select_all())
        self.root.bind('<Control-g>', lambda e: self.bulkReplaceReverse())

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.update_status(f"New file created", STATUS_MESSAGE_DURATION_MS)


    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)

            self.update_status(f"Editing file {file_path}", STATUS_MESSAGE_DURATION_MS)


    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                content = self.text_area.get(1.0, tk.END)
                file.write(content)
            self.update_status(f"Saved {file_path}", STATUS_MESSAGE_DURATION_MS)


    def cut_text(self):
        self.text_area.event_generate("<<Cut>>")

    def copy_text(self):
        self.text_area.event_generate("<<Copy>>")

    def paste_text(self):
        self.text_area.event_generate("<<Paste>>")


    def select_all(self):
        # Select all text
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)
        
        # Get selected text and count words
        selected_text = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
        word_count = len(selected_text.split())
        
        # Update status bar with word count
        self.update_status(f"Selected {word_count} word{'s' if word_count != 1 else ''}", STATUS_MESSAGE_DURATION_MS)


    def find_text(self):
        # Calculate center position
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - 50
        
        # Create and position the dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Search")
        dialog.geometry(f"300x100+{x}+{y}")
        
        # Ensure dialog stays on top
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)  # Makes dialog modal relative to main window
        
        # Create the search entry
        search_term = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=search_term)
        entry.pack(pady=10)
        
        # Configure the highlight tag
        self.text_area.tag_config("highlight", background="gray", foreground="black")
        
        # Ensure cursor visibility by setting insertbackground
        current_theme = selected_theme
        if current_theme == "Dark":
            cursor_color = "white"
        else:
            cursor_color = "black"
        self.text_area.config(insertbackground=cursor_color)
        
        def search():
            # Remove previous highlights
            self.text_area.tag_remove("highlight", "1.0", tk.END)
            
            term = search_term.get()
            if not term:
                return
                    
            # Find all instances and highlight them
            start_pos = "1.0"
            matches = []
            
            while True:
                pos = self.text_area.search(term, start_pos, tk.END, nocase=True)
                if not pos:
                    break
                        
                end_pos = f"{pos}+{len(term)}c"
                self.text_area.tag_add("highlight", pos, end_pos)
                matches.append((pos, end_pos))
                
                # Move past current match
                start_pos = end_pos
            
            # Update status bar with count
            self.update_status(f"Found {len(matches)} matches", STATUS_MESSAGE_DURATION_MS)
            
            # Position cursor at first match if any found
            if matches:
                self.text_area.mark_set(tk.INSERT, matches[0][1])
                self.text_area.see(tk.INSERT)
                # Force update to ensure cursor is visible
                self.text_area.update_idletasks()
        
        def next_match():
            term = search_term.get()
            if not term:
                return
                    
            # Get current position
            current_pos = self.text_area.index(tk.INSERT)
            
            # Find next instance starting after current position
            next_pos = self.text_area.search(term, current_pos, tk.END, nocase=True)
            
            # If no more matches found, wrap around to beginning
            if not next_pos:
                next_pos = self.text_area.search(term, "1.0", tk.END, nocase=True)
            
            if next_pos:
                end_pos = f"{next_pos}+{len(term)}c"
                self.text_area.mark_set(tk.INSERT, end_pos)
                self.text_area.see(tk.INSERT)
                self.text_area.update_idletasks()  # Force update
                
                # Update status bar
                self.update_status(f"Moved to match #{self.text_area.index(next_pos).split('.')[1]}", 
                                STATUS_MESSAGE_DURATION_MS)
        
        # Create buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text="Find All", command=search).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Next", command=next_match).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Bind Escape key to close dialog
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Focus on the entry field
        entry.focus_set()


    def old_phind_find_text(self):
        # Calculate center position
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - 50
        
        # Create and position the dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Search")
        dialog.geometry(f"300x100+{x}+{y}")
        
        # Create the search entry
        search_term = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=search_term)
        entry.pack(pady=10)
        
        # Configure the highlight tag
        self.text_area.tag_config("highlight", background="gray", foreground="black")
        
        # Ensure cursor visibility by setting insertbackground
        current_theme = selected_theme
        if current_theme == "Dark":
            cursor_color = "white"
        else:
            cursor_color = "black"
        self.text_area.config(insertbackground=cursor_color)
        
        def search():
            # Remove previous highlights
            self.text_area.tag_remove("highlight", "1.0", tk.END)
            
            term = search_term.get()
            if not term:
                return
                
            # Find all instances and highlight them
            start_pos = "1.0"
            matches = []
            
            while True:
                pos = self.text_area.search(term, start_pos, tk.END, nocase=True)
                if not pos:
                    break
                    
                end_pos = f"{pos}+{len(term)}c"
                self.text_area.tag_add("highlight", pos, end_pos)
                matches.append((pos, end_pos))
                
                # Move past current match
                start_pos = end_pos
            
            # Update status bar with count
            self.update_status(f"Found {len(matches)} matches", STATUS_MESSAGE_DURATION_MS)
            
            # Position cursor at first match if any found
            if matches:
                self.text_area.mark_set(tk.INSERT, matches[0][1])
                self.text_area.see(tk.INSERT)
                # Force update to ensure cursor is visible
                self.text_area.update_idletasks()
        
        def next_match():
            term = search_term.get()
            if not term:
                return
                
            # Get current position
            current_pos = self.text_area.index(tk.INSERT)
            
            # Find next instance starting after current position
            next_pos = self.text_area.search(term, current_pos, tk.END, nocase=True)
            
            # If no more matches found, wrap around to beginning
            if not next_pos:
                next_pos = self.text_area.search(term, "1.0", tk.END, nocase=True)
            
            if next_pos:
                end_pos = f"{next_pos}+{len(term)}c"
                self.text_area.mark_set(tk.INSERT, end_pos)
                self.text_area.see(tk.INSERT)
                self.text_area.update_idletasks()  # Force update
                
                # Update status bar
                self.update_status(f"Moved to match #{self.text_area.index(next_pos).split('.')[1]}", 
                                STATUS_MESSAGE_DURATION_MS)
        
        # Create buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text="Find All", command=search).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Next", command=next_match).pack(side=tk.LEFT, padx=5)

        # Bind Escape key to close dialog
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Focus on the entry field
        entry.focus_set()


    def old_find_text(self):
        # Calculate center position
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - 50
        
        # Create and position the dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Search")
        dialog.geometry(f"300x100+{x}+{y}")
        
        # Create the search entry
        search_term = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=search_term)
        entry.pack(pady=10)
        
        # Search function
        def search():
            term = search_term.get()
            if term:
                start_pos = self.text_area.search(term, "1.0", tk.END)
                if start_pos:
                    end_pos = f"{start_pos}+{len(term)}c"
                    self.text_area.tag_add(tk.SEL, start_pos, end_pos)
                    self.text_area.mark_set(tk.INSERT, end_pos)
                    self.text_area.see(tk.INSERT)
        
        # Create search button
        tk.Button(dialog, text="Find", command=search).pack(pady=5)
        
        # Focus on the entry field
        entry.focus_set()



    def bulk_replace(self):
        dialog = BulkReplaceDialog(self.root, "Bulk Replace")
        if dialog.pairs:  # Only perform replacement if the dialog returned pairs (Save and Replace)
            content = self.text_area.get("1.0", tk.END)
            self.text_area.tag_remove("highlight", "1.0", tk.END)
            
            for key, value in dialog.pairs:
                start_pos = "1.0"
                while start_pos:
                    start_pos = self.text_area.search(key, start_pos, tk.END, nocase=True)
                    if start_pos:
                        end_pos = f"{start_pos}+{len(key)}c"
                        self.text_area.delete(start_pos, end_pos)
                        self.text_area.insert(start_pos, value)
                        self.text_area.tag_add("highlight", start_pos, 
                                            f"{start_pos}+{len(value)}c")
            
            self.text_area.tag_config("highlight", background="yellow", 
                                    foreground="black")


    def replaceBulk(self):
        content = self.text_area.get("1.0", tk.END)
        self.text_area.tag_remove("highlight", "1.0", tk.END)  # Remove existing highlights
        replacement_count = 0
        
        for key, value in bulk_replace_pairs:
            start_pos = "1.0"
            while start_pos:
                start_pos = self.text_area.search(key, start_pos, tk.END, nocase=True)
                if start_pos:
                    end_pos = f"{start_pos}+{len(key)}c"
                    self.text_area.delete(start_pos, end_pos)
                    self.text_area.insert(start_pos, value)
                    self.text_area.tag_add("highlight", start_pos, f"{start_pos}+{len(value)}c")
                    replacement_count += 1
                    start_pos = end_pos
        
        self.text_area.tag_config("highlight", background="yellow", foreground="black")
        self.update_status(f"Performed {replacement_count} replacements", STATUS_MESSAGE_DURATION_MS)

    def bulkReplaceReverse(self):
        content = self.text_area.get("1.0", tk.END)  # Get entire text
        self.text_area.tag_remove("highlight", "1.0", tk.END)  # Clear existing highlights
        replacement_count = 0

        for key, value in bulk_replace_pairs:
            # Search for the VALUE and replace with the KEY
            start_pos = "1.0"
            while start_pos:
                start_pos = self.text_area.search(value, start_pos, tk.END, nocase=True)
                if start_pos:
                    end_pos = f"{start_pos}+{len(value)}c"
                    self.text_area.delete(start_pos, end_pos)  # Delete the value
                    self.text_area.insert(start_pos, key)      # Insert the key
                    self.text_area.tag_add("highlight", start_pos,
                                            f"{start_pos}+{len(key)}c") #Highlight inserted Key
                    replacement_count += 1
                    start_pos = end_pos

        self.text_area.tag_config("highlight", background="yellow", foreground="black")
        self.update_status(f"Performed {replacement_count} reverse replacements", STATUS_MESSAGE_DURATION_MS)


    def apply_theme(self, theme):
        global selected_theme
        theme_configs = {
            "Standard": {
                "bg": "white",
                "fg": "black",
                "menu_bg": "lightgrey",
                "menu_fg": "black",
                "dialog_bg": "white",
                "cursor_color": "black"  # Added cursor color
            },
            "Dark": {
                "bg": "#002b36",
                "fg": "#839496",
                "menu_bg": "#073642",
                "menu_fg": "#839496",
                "dialog_bg": "#002b36",
                "cursor_color": "white"  # Added cursor color
            },
            "Light": {
                "bg": "#fdf6e3",
                "fg": "#657b83",
                "menu_bg": "#eee8d5",
                "menu_fg": "#657b83",
                "dialog_bg": "#fdf6e3",
                "cursor_color": "black"  # Added cursor color
            }
        }
        
        if theme in theme_configs:
            config = theme_configs[theme]
            self.text_area.config(
                bg=config["bg"],
                fg=config["fg"],
                insertbackground=config["cursor_color"]  # Added cursor color
            )
            self.menu_bar.config(bg=config["menu_bg"], fg=config["menu_fg"])
            self.root.config(bg=config["menu_bg"], menu=self.menu_bar)
            self.style_widgets(config["dialog_bg"], config["fg"])
            selected_theme = theme
            self.status_bar.config(bg=config["menu_bg"], fg=config["menu_fg"])
            
    def style_widgets(self, bg_color, fg_color):
        # Style the root window and its children
        self.root.config(bg=bg_color)
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Menu):
                widget.config(bg=bg_color, fg=fg_color)
            else:
                widget.config(bg=bg_color, fg=fg_color)

    def readPrefs(self):
        global bulk_replace_pairs, selected_theme
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "textscrub")
        prefs_file = os.path.join(config_dir, "textscrub-prefs.json")

        if os.path.exists(prefs_file):
            with open(prefs_file, 'r') as file:
                prefs = json.load(file)
                bulk_replace_pairs.extend(prefs.get("bulk_replace_pairs", []))
                selected_theme = prefs.get("selected_theme", "Standard")

    def writePrefs(self):
        global bulk_replace_pairs, selected_theme
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "textscrub")
        os.makedirs(config_dir, exist_ok=True)
        prefs_file = os.path.join(config_dir, "textscrub-prefs.json")

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
    app.setup_signal_handling() #<-- setup signal handling
    root.mainloop() #<-- Start the main loop

if __name__ == "__main__":
    main()
