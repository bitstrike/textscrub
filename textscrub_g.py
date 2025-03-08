#!/usr/bin/env python3

import os
import json
import signal
import sys
import gi

# Import GTK
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

# Global list to store key-value pairs for bulk replacement
bulk_replace_pairs = []
selected_theme = "Standard"  # Default theme

STATUS_MESSAGE_DURATION_MS = 0

class BulkReplaceDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(
            title="Bulk Replace",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL
        )

        self.pairs = bulk_replace_pairs.copy()  # Use a copy
        self.parent = parent

        # Set dialog size
        self.set_default_size(400, 300)

        # Create content area
        content_area = self.get_content_area()
        content_area.set_spacing(6)

        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_area.add(main_box)

        # Add label
        label = Gtk.Label(label="Enter key-value pairs for bulk replace:")
        main_box.pack_start(label, False, False, 0)

        # Create entry fields and add button
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.pack_start(entry_box, False, False, 0)

        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("Search for")
        entry_box.pack_start(self.key_entry, True, True, 0)

        self.value_entry = Gtk.Entry()
        self.value_entry.set_placeholder_text("Replace with")
        entry_box.pack_start(self.value_entry, True, True, 0)

        add_button = Gtk.Button(label="Add")
        add_button.connect("clicked", self.add_pair)
        entry_box.pack_start(add_button, False, False, 0)

        # Create scrollable list
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        main_box.pack_start(scrolled_window, True, True, 0)

        # List store and view
        self.list_store = Gtk.ListStore(str, str)
        self.tree_view = Gtk.TreeView(model=self.list_store)

        # Populate store with existing pairs
        for key, value in self.pairs:
            self.list_store.append([key, value])

        # Create columns
        key_column = Gtk.TreeViewColumn("Key", Gtk.CellRendererText(), text=0)
        value_column = Gtk.TreeViewColumn("Value", Gtk.CellRendererText(), text=1)

        self.tree_view.append_column(key_column)
        self.tree_view.append_column(value_column)

        # Selection mode
        selection = self.tree_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.tree_selection = selection

        scrolled_window.add(self.tree_view)

        # Add button for removing selected item
        remove_button = Gtk.Button(label="Remove Selected")
        remove_button.connect("clicked", self.remove_pair)
        main_box.pack_start(remove_button, False, False, 0)

        # Add action buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save and Replace", Gtk.ResponseType.OK)

        self.show_all()

    def add_pair(self, button):
        key = self.key_entry.get_text().strip()
        value = self.value_entry.get_text().strip()

        if key and value:
            self.list_store.append([key, value])
            self.pairs.append((key, value))

            # Clear entries
            self.key_entry.set_text("")
            self.value_entry.set_text("")
            self.key_entry.grab_focus()

    def remove_pair(self, button):
        model, treeiter = self.tree_selection.get_selected()
        if treeiter:
            index = model.get_path(treeiter)[0]
            model.remove(treeiter)
            del self.pairs[index]

    def get_pairs(self):
        return self.pairs

class SimpleTextEditor(Gtk.Application):
    def __init__(self):
        super().__init__()
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title("TextScrub Editor")
        self.window.set_default_size(800, 600)

        # Create main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(self.main_box)

        # Create the menu bar (using HeaderBar in GTK3)
        self.create_header_bar()

        # Create scrollable window for text view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.main_box.pack_start(scrolled_window, True, True, 0)

        # Create text view
        self.text_buffer = Gtk.TextBuffer()
        self.text_view = Gtk.TextView.new_with_buffer(self.text_buffer)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled_window.add(self.text_view)

        # Enable undo and redo
        self.text_buffer.set_can_undo(True)

        # Create status bar
        self.status_bar = Gtk.Statusbar()
        self.context_id = self.status_bar.get_context_id("main")
        self.main_box.pack_start(self.status_bar, False, False, 0)

        # Create search highlight tag
        self.text_buffer.create_tag("highlight", background="yellow", foreground="black")

        # Connect signals
        self.connect_signals()

        # Read preferences
        self.readPrefs()

        # Apply the saved theme
        self.apply_theme(selected_theme)

        self.window.show_all()

    def create_header_bar(self):
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.props.title = "TextScrub Editor"
        self.window.set_titlebar(self.header_bar)

        # Create file menu button
        file_button = Gtk.MenuButton()
        file_button.set_label("File")
        file_menu = Gtk.Menu()
        file_button.set_popup(file_menu)

        # File menu items
        new_item = Gtk.MenuItem(label="New")
        new_item.connect("activate", self.on_new_file)
        file_menu.append(new_item)

        open_item = Gtk.MenuItem(label="Open")
        open_item.connect("activate", self.on_open_file)
        file_menu.append(open_item)

        save_item = Gtk.MenuItem(label="Save")
        save_item.connect("activate", self.on_save_file)
        file_menu.append(save_item)

        file_menu.append(Gtk.SeparatorMenuItem())

        exit_item = Gtk.MenuItem(label="Exit")
        exit_item.connect("activate", self.on_exit_app)
        file_menu.append(exit_item)

        file_menu.show_all()
        self.header_bar.pack_start(file_button)

        # Create edit menu button
        edit_button = Gtk.MenuButton()
        edit_button.set_label("Edit")
        edit_menu = Gtk.Menu()
        edit_button.set_popup(edit_menu)

        # Edit menu items
        undo_item = Gtk.MenuItem(label="Undo")
        undo_item.connect("activate", self.on_undo)
        edit_menu.append(undo_item)

        redo_item = Gtk.MenuItem(label="Redo")
        redo_item.connect("activate", self.on_redo)
        edit_menu.append(redo_item)

        edit_menu.append(Gtk.SeparatorMenuItem())

        cut_item = Gtk.MenuItem(label="Cut")
        cut_item.connect("activate", self.on_cut_text)
        edit_menu.append(cut_item)

        copy_item = Gtk.MenuItem(label="Copy")
        copy_item.connect("activate", self.on_copy_text)
        edit_menu.append(copy_item)

        paste_item = Gtk.MenuItem(label="Paste")
        paste_item.connect("activate", self.on_paste_text)
        edit_menu.append(paste_item)

        select_all_item = Gtk.MenuItem(label="Select All")
        select_all_item.connect("activate", self.on_select_all)
        edit_menu.append(select_all_item)

        edit_menu.append(Gtk.SeparatorMenuItem())

        replace_bulk_item = Gtk.MenuItem(label="Replace Bulk")
        replace_bulk_item.connect("activate", self.on_replace_bulk)
        edit_menu.append(replace_bulk_item)

        reverse_replace_item = Gtk.MenuItem(label="Reverse Replace")
        reverse_replace_item.connect("activate", self.on_bulk_replace_reverse)
        edit_menu.append(reverse_replace_item)

        edit_menu.append(Gtk.SeparatorMenuItem())

        # Theme submenu
        theme_item = Gtk.MenuItem(label="Theme")
        theme_menu = Gtk.Menu()

        standard_theme_item = Gtk.MenuItem(label="Standard")
        standard_theme_item.connect("activate", lambda w: self.apply_theme("Standard"))
        theme_menu.append(standard_theme_item)

        dark_theme_item = Gtk.MenuItem(label="Dark")
        dark_theme_item.connect("activate", lambda w: self.apply_theme("Dark"))
        theme_menu.append(dark_theme_item)

        light_theme_item = Gtk.MenuItem(label="Light")
        light_theme_item.connect("activate", lambda w: self.apply_theme("Light"))
        theme_menu.append(light_theme_item)

        theme_item.set_submenu(theme_menu)
        edit_menu.append(theme_item)

        edit_menu.show_all()
        self.header_bar.pack_start(edit_button)

        # Create search menu button
        search_button = Gtk.MenuButton()
        search_button.set_label("Search")
        search_menu = Gtk.Menu()
        search_button.set_popup(search_menu)

        # Search menu items
        find_item = Gtk.MenuItem(label="Find")
        find_item.connect("activate", self.on_find_text)
        search_menu.append(find_item)

        bulk_replace_item = Gtk.MenuItem(label="Bulk Replace")
        bulk_replace_item.connect("activate", self.on_bulk_replace)
        search_menu.append(bulk_replace_item)

        search_menu.show_all()
        self.header_bar.pack_start(search_button)

    def connect_signals(self):
        # Connect window close event
        self.window.connect("delete-event", self.on_delete_event)

        # Connect key press event
        self.window.connect("key-press-event", self.on_key_press)

    def setup_signal_handling(self):
        """
        Set up robust signal handling for clean and immediate application exit.
        """
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        """
        Handle interruption signals with immediate and clean exit.
        """
        try:
            print(f"\nReceived signal {signum}. Exiting application...")
            self.writePrefs()
            self.quit()
            sys.exit(0)
        except Exception as e:
            print(f"Error during signal handling: {e}")
            sys.exit(1)

    def update_status(self, message, duration=STATUS_MESSAGE_DURATION_MS):
        """
        Update the status bar with a message.

        Args:
            message (str): Message to display
            duration (int): How long to show the message in milliseconds
        """
        # Remove any existing messages
        self.status_bar.remove_all(self.context_id)

        # Add the new message
        message_id = self.status_bar.push(self.context_id, message)

        # Set a timer to clear the message if duration > 0
        if duration > 0:
            GLib.timeout_add(duration, lambda: self.status_bar.remove(self.context_id, message_id))

    def on_delete_event(self, widget, event):
        """Handle window close event"""
        self.on_exit_app(widget)
        return True  # Stop other handlers

    def on_key_press(self, widget, event):
        """Handle keyboard shortcuts"""
        keyval = event.keyval
        keyval_name = Gdk.keyval_name(keyval)
        state = event.state

        # Check for Ctrl modifier
        ctrl = (state & Gdk.ModifierType.CONTROL_MASK)

        # Handle key combinations
        if ctrl:
            if keyval_name == 'n':
                self.on_new_file(widget)
                return True
            elif keyval_name == 'o':
                self.on_open_file(widget)
                return True
            elif keyval_name == 's':
                self.on_save_file(widget)
                return True
            elif keyval_name == 'f':
                self.on_find_text(widget)
                return True
            elif keyval_name == 'b':
                self.on_bulk_replace(widget)
                return True
            elif keyval_name == 'r':
                self.on_replace_bulk(widget)
                return True
            elif keyval_name == 'a':
                self.on_select_all(widget)
                return True
            elif keyval_name == 'g':
                self.on_bulk_replace_reverse(widget)
                return True
            elif keyval_name == 'z':
                self.on_undo(widget)
                return True
            elif keyval_name == 'y':
                self.on_redo(widget)
                return True

        return False  # Continue event propagation

    def on_new_file(self, widget):
        """Create a new empty file"""
        self.text_buffer.set_text("")
        self.update_status("New file created", STATUS_MESSAGE_DURATION_MS)

    def on_open_file(self, widget):
        """Open a file"""
        dialog = Gtk.FileChooserDialog(
            title="Open File",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        filter_text.add_pattern("*.txt")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("All files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    self.text_buffer.set_text(content)
                self.update_status(f"Editing file {file_path}", STATUS_MESSAGE_DURATION_MS)
            except Exception as e:
                self.update_status(f"Error opening file: {e}", STATUS_MESSAGE_DURATION_MS)

        dialog.destroy()

    def on_save_file(self, widget):
        """Save current text to a file"""
        dialog = Gtk.FileChooserDialog(
            title="Save File",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )

        dialog.set_do_overwrite_confirmation(True)

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        filter_text.add_pattern("*.txt")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("All files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            try:
                start, end = self.text_buffer.get_bounds()
                content = self.text_buffer.get_text(start, end, True)

                with open(file_path, 'w') as file:
                    file.write(content)

                self.update_status(f"Saved {file_path}", STATUS_MESSAGE_DURATION_MS)
            except Exception as e:
                self.update_status(f"Error saving file: {e}", STATUS_MESSAGE_DURATION_MS)

        dialog.destroy()

    def on_cut_text(self, widget):
        """Cut selected text to clipboard"""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.cut_clipboard(clipboard, True)

    def on_copy_text(self, widget):
        """Copy selected text to clipboard"""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.copy_clipboard(clipboard)

    def on_paste_text(self, widget):
        """Paste text from clipboard"""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.paste_clipboard(clipboard, None, True)

    def on_select_all(self, widget):
        """Select all text and count words"""
        start, end = self.text_buffer.get_bounds()
        self.text_buffer.select_range(start, end)

        # Get selected text and count words
        selected_text = self.text_buffer.get_text(start, end, True)
        word_count = len(selected_text.split())

        # Update status bar with word count
        self.update_status(f"Selected {word_count} word{'s' if word_count != 1 else ''}", STATUS_MESSAGE_DURATION_MS)

    def on_find_text(self, widget):
        """Show find dialog"""
        dialog = Gtk.Dialog(
            title="Search",
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE,
            )
        )

        dialog.set_default_size(300, 100)

        content_area = dialog.get_content_area()
        content_area.set_spacing(6)

        # Create search entry
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        content_area.add(entry_box)

        search_entry = Gtk.Entry()
        search_entry.set_placeholder_text("Enter search term")
        entry_box.pack_start(search_entry, True, True, 0)

        # Create buttons
        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_spacing(6)
        content_area.add(button_box)

        find_all_button = Gtk.Button(label="Find All")
        next_button = Gtk.Button(label="Next")

        button_box.add(find_all_button)
        button_box.add(next_button)

        # Mark for tracking current position
        self.current_match_position = None
        self.matches = []

        # Find all occurrences function
        def search():
            self.matches = []

            # Remove previous highlights
            start, end = self.text_buffer.get_bounds()
            self.text_buffer.remove_tag_by_name("highlight", start, end)

            term = search_entry.get_text()
            if not term:
                return

            # Find all instances and highlight them
            text = self.text_buffer.get_text(start, end, True)
            search_term_lower = term.lower()

            offset = 0
            while True:
                index = text.lower().find(search_term_lower, offset)
                if index == -1:
                    break

                match_start = self.text_buffer.get_iter_at_offset(index)
                match_end = self.text_buffer.get_iter_at_offset(index + len(term))

                self.text_buffer.apply_tag_by_name("highlight", match_start, match_end)
                self.matches.append((match_start.get_offset(), match_end.get_offset()))

                offset = index + len(term)

            # Update status bar with count
            self.update_status(f"Found {len(self.matches)} matches", STATUS_MESSAGE_DURATION_MS)

            # Position cursor at first match if any found
            if self.matches:
                self.current_match_position = 0
                match_start = self.text_buffer.get_iter_at_offset(self.matches[0][0])
                match_end = self.text_buffer.get_iter_at_offset(self.matches[0][1])

                self.text_buffer.select_range(match_start, match_end)
                self.text_view.scroll_to_iter(match_start, 0.1, False, 0.0, 0.0)

        # Next match function
        def next_match():
            if not self.matches:
                search()
                return

            if self.current_match_position is None:
                self.current_match_position = 0
            else:
                self.current_match_position = (self.current_match_position + 1) % len(self.matches)

            match = self.matches[self.current_match_position]
            match_start = self.text_buffer.get_iter_at_offset(match[0])
            match_end = self.text_buffer.get_iter_at_offset(match[1])

            self.text_buffer.select_range(match_start, match_end)
            self.text_view.scroll_to_iter(match_start, 0.1, False, 0.0, 0.0)

            self.update_status(f"Match {self.current_match_position + 1} of {len(self.matches)}",
                               STATUS_MESSAGE_DURATION_MS)

        # Connect buttons
        find_all_button.connect("clicked", lambda w: search())
        next_button.connect("clicked", lambda w: next_match())

        # Handle Enter key in search entry
        search_entry.connect("activate", lambda w: search())

        dialog.show_all()
        search_entry.grab_focus()

        dialog.run()
        dialog.destroy()

    def on_bulk_replace(self, widget):
        """Show bulk replace dialog"""
        dialog = BulkReplaceDialog(self.window)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            global bulk_replace_pairs
            bulk_replace_pairs = dialog.get_pairs()
            self.writePrefs()
            self.replaceBulk()

        dialog.destroy()

    def on_replace_bulk(self, widget):
        """Perform bulk replacement with saved pairs"""
        self.replaceBulk()

    def replaceBulk(self):
        """Replace text according to bulk_replace_pairs"""
        # Remove existing highlights
        start, end = self.text_buffer.get_bounds()
        self.text_buffer.remove_tag_by_name("highlight", start, end)

        replacement_count = 0

        for key, value in bulk_replace_pairs:
            # Convert buffer to text for searching
            current_text = self.text_buffer.get_text(start, end, True)
            search_key = key

            # Track position changes due to replacements
            offset = 0

            # Find all occurrences (case-insensitive)
            lower_text = current_text.lower()
            lower_key = search_key.lower()

            pos = 0
            while True:
                pos = lower_text.find(lower_key, pos)
                if pos == -1:
                    break

                # Get the exact text that matched to preserve case in replacements
                match_start = self.text_buffer.get_iter_at_offset(pos + offset)
                match_end = self.text_buffer.get_iter_at_offset(pos + len(key) + offset)

                # Delete the match and insert replacement
                self.text_buffer.delete(match_start, match_end)
                self.text_buffer.insert(match_start, value)

                # Apply highlight to the replacement
                highlight_start = self.text_buffer.get_iter_at_offset(pos + offset)
                highlight_end = self.text_buffer.get_iter_at_offset(pos + len(value) + offset)
                self.text_buffer.apply_tag_by_name("highlight", highlight_start, highlight_end)

                # Update offsets for length difference
                offset += len(value) - len(key)

                # Move past this replacement
                pos += len(key)

                replacement_count += 1

                # Get updated text for next search
                start, end = self.text_buffer.get_bounds()
                current_text = self.text_buffer.get_text(start, end, True)
                lower_text = current_text.lower()

        self.update_status(f"Performed {replacement_count} replacements", STATUS_MESSAGE_DURATION_MS)

    def on_bulk_replace_reverse(self, widget):
        """Perform reverse bulk replacement"""
        # Remove existing highlights
        start, end = self.text_buffer.get_bounds()
        self.text_buffer.remove_tag_by_name("highlight", start, end)

        replacement_count = 0

        for key, value in bulk_replace_pairs:
            # Convert buffer to text for searching
            current_text = self.text_buffer.get_text(start, end, True)
            search_value = value

            # Track position changes due to replacements
            offset = 0

            # Find all occurrences (case-insensitive)
            lower_text = current_text.lower()
            lower_value = search_value.lower()

            pos = 0
            while True:
                pos = lower_text.find(lower_value, pos)
                if pos == -1:
                    break

                # Get the exact text that matched to preserve case in replacements
                match_start = self.text_buffer.get_iter_at_offset(pos + offset)
                match_end = self.text_buffer.get_iter_at_offset(pos + len(value) + offset)

                # Delete the match and insert original key
                self.text_buffer.delete(match_start, match_end)
                self.text_buffer.insert(match_start, key)

                # Apply highlight to the replacement
                highlight_start = self.text_buffer.get_iter_at_offset(pos + offset)
                highlight_end = self.text_buffer.get_iter_at_offset(pos + len(key) + offset)
                self.text_buffer.apply_tag_by_name("highlight", highlight_start, highlight_end)

                # Update offsets for length difference
                offset += len(key) - len(value)

                # Move past this replacement
                pos += len(value)

                replacement_count += 1

                # Get updated text for next search
                start, end = self.text_buffer.get_bounds()
                current_text = self.text_buffer.get_text(start, end, True)
                lower_text = current_text.lower()

        self.update_status(f"Performed {replacement_count} reverse replacements", STATUS_MESSAGE_DURATION_MS)

    def on_undo(self, widget):
        """Undo the last action"""
        if self.text_buffer.can_undo():
            self.text_buffer.undo()

    def on_redo(self, widget):
        """Redo the last undone action"""
        if self.text_buffer.can_redo():
            self.text_buffer.redo()

    def apply_theme(self, theme):
        """Apply the selected theme to the UI"""
        global selected_theme

        theme_configs = {
            "Standard": {
                "bg": "#FFFFFF",
                "fg": "#000000",
                "menu_bg": "#F0F0F0",
                "menu_fg": "#000000",
                "cursor_color": "#000000"
            },
            "Dark": {
                "bg": "#002b36",
                "fg": "#839496",
                "menu_bg": "#073642",
                "menu_fg": "#839496",
                "cursor_color": "#FFFFFF"
            },
            "Light": {
                "bg": "#fdf6e3",
                "fg": "#657b83",
                "menu_bg": "#eee8d5",
                "menu_fg": "#657b83",
                "cursor_color": "#000000"
            }
        }

        if theme in theme_configs:
            config = theme_configs[theme]

            # Create CSS for the theme
            css_provider = Gtk.CssProvider()
            css_data = f"""
            textview {{
                background-color: {config["bg"]};
                color: {config["fg"]};
                caret-color: {config["cursor_color"]};
            }}
            headerbar {{
                background-color: {config["menu_bg"]};
                color: {config["menu_fg"]};
            }}
            window {{
                background-color: {config["bg"]};
            }}
            """

            css_provider.load_from_data(css_data.encode())

            # Apply CSS
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

            # Update the global theme setting
            selected_theme = theme

    def readPrefs(self):
        """Read preferences from file"""
        global bulk_replace_pairs, selected_theme
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "textscrub")
        prefs_file = os.path.join(config_dir, "textscrub-prefs.json")

        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, 'r') as file:
                    prefs = json.load(file)
                    bulk_replace_pairs.extend(prefs.get("bulk_replace_pairs", []))
                    selected_theme = prefs.get("selected_theme", "Standard")
            except Exception as e:
                print(f"Error reading preferences: {e}")

    def writePrefs(self):
        """Write preferences to file"""
        global bulk_replace_pairs, selected_theme
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "textscrub")
        os.makedirs(config_dir, exist_ok=True)
        prefs_file = os.path.join(config_dir, "textscrub-prefs.json")

        prefs = {"bulk_replace_pairs": bulk_replace_pairs, "selected_theme": selected_theme}
        with open(prefs_file, 'w') as file:
            json.dump(prefs, file)

    def on_exit_app(self, widget):
        """Exit the application"""
        self.writePrefs()
        self.quit()

def main():
    global app
    app = SimpleTextEditor()
    app.setup_signal_handling()
    app.run(None)

if __name__ == "__main__":
    main()
