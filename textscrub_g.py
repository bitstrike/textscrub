#!/usr/bin/env python3


#!/usr/bin/env python3
import gi
import os
import json
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

class EditorConfig:
    def __init__(self):
        self.window_x = 1000
        self.window_y = 800
        self.bulk_dialog_x = 600
        self.bulk_dialog_y = 400
        self.MAX_LIST_ROWS = 8
        
        # Create config directory if it doesn't exist
        self.config_dir = os.path.expanduser("~/.config/textscrub")
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        
        self.config_file = os.path.join(self.config_dir, "textscrub-prefs.json")
        self.load_config()
    
    def load_config(self):
        # Default values
        self.theme = "default"
        self.font = "Monospace 12"
        self.replacements = {}
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.theme = config.get('theme', 'default')
                    self.font = config.get('font', 'Monospace 12')
                    self.replacements = config.get('replacements', {})
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        config = {
            'theme': self.theme,
            'font': self.font,
            'replacements': self.replacements
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")


class TextEditor(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="TextScrub")
        self.config = EditorConfig()
        self.set_default_size(self.config.window_x, self.config.window_y)
        
        # Main layout
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.vbox)
        
        # Create menu bar
        self.create_menu()
        
        # Text view for editing
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)
        
        self.text_buffer = Gtk.TextBuffer()
        self.text_view = Gtk.TextView.new_with_buffer(self.text_buffer)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Set font from config
        self.update_font()
        
        self.scrolled_window.add(self.text_view)
        self.vbox.pack_start(self.scrolled_window, True, True, 0)
        
        # Status bar
        self.statusbar = Gtk.Statusbar()
        self.context_id = self.statusbar.get_context_id("main")
        self.vbox.pack_start(self.statusbar, False, False, 0)
        self.update_status("Ready")
        
        # Apply theme
        self.apply_theme(self.config.theme)
        
        # Set up text buffer for highlighting
        self.highlight_tag = self.text_buffer.create_tag("highlight", 
                                                background="yellow", 
                                                foreground="black")
        
        # Track if we're doing replacements or reverse replacements
        self.replacement_direction = "forward"
        
        # Show the window
        self.connect("destroy", Gtk.main_quit)
        self.show_all()
    
    def create_menu(self):
        # Menu bar
        self.menubar = Gtk.MenuBar()
        self.vbox.pack_start(self.menubar, False, False, 0)
        
        # File menu
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem.new_with_label("File")
        file_item.set_submenu(file_menu)
        
        new_item = Gtk.MenuItem.new_with_label("New")
        new_item.connect("activate", self.on_new_clicked)
        file_menu.append(new_item)
        
        open_item = Gtk.MenuItem.new_with_label("Open")
        open_item.connect("activate", self.on_open_clicked)
        file_menu.append(open_item)
        
        save_item = Gtk.MenuItem.new_with_label("Save")
        save_item.connect("activate", self.on_save_clicked)
        file_menu.append(save_item)
        
        save_as_item = Gtk.MenuItem.new_with_label("Save As")
        save_as_item.connect("activate", self.on_save_as_clicked)
        file_menu.append(save_as_item)
        
        file_menu.append(Gtk.SeparatorMenuItem())
        
        quit_item = Gtk.MenuItem.new_with_label("Quit")
        quit_item.connect("activate", Gtk.main_quit)
        file_menu.append(quit_item)
        
        self.menubar.append(file_item)
        
        # Edit menu
        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem.new_with_label("Edit")
        edit_item.set_submenu(edit_menu)
        
        # Theme submenu
        theme_menu = Gtk.Menu()
        theme_item = Gtk.MenuItem.new_with_label("Theme")
        theme_item.set_submenu(theme_menu)
        
        theme_default = Gtk.MenuItem.new_with_label("Default")
        theme_default.connect("activate", self.on_theme_clicked, "default")
        theme_menu.append(theme_default)
        
        theme_light = Gtk.MenuItem.new_with_label("Solarized Light")
        theme_light.connect("activate", self.on_theme_clicked, "light")
        theme_menu.append(theme_light)
        
        theme_dark = Gtk.MenuItem.new_with_label("Solarized Dark")
        theme_dark.connect("activate", self.on_theme_clicked, "dark")
        theme_menu.append(theme_dark)
        
        edit_menu.append(theme_item)
        
        # Font selection
        font_item = Gtk.MenuItem.new_with_label("Font")
        font_item.connect("activate", self.on_font_clicked)
        edit_menu.append(font_item)
        
        # Bulk replace
        edit_menu.append(Gtk.SeparatorMenuItem())
        bulk_replace_item = Gtk.MenuItem.new_with_label("Bulk Replace")
        bulk_replace_item.connect("activate", self.on_bulk_replace_clicked)
        edit_menu.append(bulk_replace_item)
        
        self.menubar.append(edit_item)
        
        # Search menu
        search_menu = Gtk.Menu()
        search_item = Gtk.MenuItem.new_with_label("Search")
        search_item.set_submenu(search_menu)
        
        find_item = Gtk.MenuItem.new_with_label("Find")
        find_item.connect("activate", self.on_find_clicked)
        search_menu.append(find_item)
        
        replace_item = Gtk.MenuItem.new_with_label("Replace")
        replace_item.connect("activate", self.on_replace_clicked)
        search_menu.append(replace_item)
        
        self.menubar.append(search_item)
    
    def update_status(self, message):
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, message)
    
    def update_font(self):
        font_desc = Pango.FontDescription.from_string(self.config.font)
        self.text_view.override_font(font_desc)
    
    def apply_theme(self, theme_name):
        self.config.theme = theme_name
        self.config.save_config()
        
        # Get style context
        context = self.get_style_context()
        
        if theme_name == "default":
            # Reset to system default
            self.reset_css()
            self.update_status("Default theme applied")
        elif theme_name == "light":
            # Solarized Light theme
            css = b"""
            window, menubar, statusbar, textview {
                background-color: #fdf6e3;
                color: #657b83;
            }
            menuitem {
                color: #657b83;
            }
            menuitem:hover {
                background-color: #eee8d5;
            }
            textview text {
                background-color: #fdf6e3;
                color: #657b83;
            }
            """
            self.apply_css(css)
            self.update_status("Solarized Light theme applied")
        elif theme_name == "dark":
            # Solarized Dark theme
            css = b"""
            window, menubar, statusbar, textview {
                background-color: #002b36;
                color: #839496;
            }
            menuitem {
                color: #839496;
            }
            menuitem:hover {
                background-color: #073642;
            }
            textview text {
                background-color: #002b36;
                color: #839496;
            }
            """
            self.apply_css(css)
            self.update_status("Solarized Dark theme applied")
    
    def reset_css(self):
        # Reset CSS to default
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"")
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def apply_css(self, css):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def on_new_clicked(self, widget):
        self.text_buffer.set_text("")
        self.update_status("New document created")
    
    def on_open_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Open File", parent=self, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                with open(filename, 'r') as f:
                    text = f.read()
                    self.text_buffer.set_text(text)
                    self.update_status(f"Opened file: {filename}")
            except Exception as e:
                self.update_status(f"Error opening file: {e}")
        
        dialog.destroy()
    
    def on_save_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Save File", parent=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            start, end = self.text_buffer.get_bounds()
            text = self.text_buffer.get_text(start, end, False)
            
            try:
                with open(filename, 'w') as f:
                    f.write(text)
                    self.update_status(f"Saved file: {filename}")
            except Exception as e:
                self.update_status(f"Error saving file: {e}")
        
        dialog.destroy()
    
    def on_save_as_clicked(self, widget):
        self.on_save_clicked(widget)
    
    def on_theme_clicked(self, widget, theme_name):
        self.apply_theme(theme_name)
    
    def on_font_clicked(self, widget):
        font_dialog = Gtk.FontChooserDialog(title="Select Font", parent=self)
        font_dialog.set_font(self.config.font)
        
        response = font_dialog.run()
        if response == Gtk.ResponseType.OK:
            font = font_dialog.get_font()
            self.config.font = font
            self.config.save_config()
            self.update_font()
            self.update_status(f"Font updated to: {font}")
        
        font_dialog.destroy()
    
    def on_find_clicked(self, widget):
        self.update_status("Find selected")
        # Implement find functionality (simplified for this example)
    
    def on_replace_clicked(self, widget):
        self.update_status("Replace selected")
        # Implement replace functionality (simplified for this example)
    
    def on_bulk_replace_clicked(self, widget):
        self.bulk_replace_dialog = BulkReplaceDialog(self)
        self.bulk_replace_dialog.show_all()
    
    def replace_bulk(self, replacements, direction="forward"):
        if not replacements:
            self.update_status("No replacements defined")
            return
        
        # Get all text
        start, end = self.text_buffer.get_bounds()
        text = self.text_buffer.get_text(start, end, False)
        
        # Remove all previous highlights
        self.text_buffer.remove_tag(self.highlight_tag, start, end)
        
        count = 0
        
        # Choose what to replace based on direction
        if direction == "forward":
            # Replace keys with values
            for key, value in replacements.items():
                # Create a case-insensitive pattern for the key
                import re
                pattern = re.compile(r'\b' + re.escape(key) + r'\b', re.IGNORECASE)
                
                # Find all matches and their positions
                matches = list(pattern.finditer(text))
                
                # Replace and highlight from the end to avoid offset issues
                for match in reversed(matches):
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Replace text
                    iter_start = self.text_buffer.get_iter_at_offset(start_pos)
                    iter_end = self.text_buffer.get_iter_at_offset(end_pos)
                    self.text_buffer.delete(iter_start, iter_end)
                    self.text_buffer.insert(iter_start, value)
                    
                    # Update end iterator after insertion
                    new_end_pos = start_pos + len(value)
                    iter_start = self.text_buffer.get_iter_at_offset(start_pos)
                    iter_end = self.text_buffer.get_iter_at_offset(new_end_pos)
                    
                    # Apply highlight
                    self.text_buffer.apply_tag(self.highlight_tag, iter_start, iter_end)
                    
                    count += 1
                    
            self.replacement_direction = "reverse"
        else:
            # Replace values with keys
            for key, value in replacements.items():
                import re
                pattern = re.compile(r'\b' + re.escape(value) + r'\b')
                
                # Find all matches and their positions
                matches = list(pattern.finditer(text))
                
                # Replace and highlight from the end to avoid offset issues
                for match in reversed(matches):
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Replace text
                    iter_start = self.text_buffer.get_iter_at_offset(start_pos)
                    iter_end = self.text_buffer.get_iter_at_offset(end_pos)
                    self.text_buffer.delete(iter_start, iter_end)
                    self.text_buffer.insert(iter_start, key)
                    
                    # Update end iterator after insertion
                    new_end_pos = start_pos + len(key)
                    iter_start = self.text_buffer.get_iter_at_offset(start_pos)
                    iter_end = self.text_buffer.get_iter_at_offset(new_end_pos)
                    
                    # Apply highlight
                    self.text_buffer.apply_tag(self.highlight_tag, iter_start, iter_end)
                    
                    count += 1
            
            self.replacement_direction = "forward"
        
        self.update_status(f"Replaced {count} occurrences")


class BulkReplaceDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(
            self, title="Bulk Replace", transient_for=parent, flags=0
        )
        self.parent = parent
        self.set_default_size(
            parent.config.bulk_dialog_x, 
            parent.config.bulk_dialog_y
        )
        
        # Copy replacements from config
        self.replacements = parent.config.replacements.copy()
        
        # Create UI
        box = self.get_content_area()
        
        # Input fields
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(input_box, False, False, 5)
        
        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("Key")
        input_box.pack_start(self.key_entry, True, True, 5)
        
        self.value_entry = Gtk.Entry()
        self.value_entry.set_placeholder_text("Value")
        input_box.pack_start(self.value_entry, True, True, 5)
        
        add_button = Gtk.Button.new_with_label("Add")
        add_button.connect("clicked", self.on_add_clicked)
        input_box.pack_start(add_button, False, False, 5)
        
        # List of replacements
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(parent.config.MAX_LIST_ROWS * 30)
        box.pack_start(scroll, True, True, 5)
        
        # List store: key, value
        self.list_store = Gtk.ListStore(str, str)
        self.update_list_store()
        
        self.tree_view = Gtk.TreeView(model=self.list_store)
        
        # Key column
        renderer_key = Gtk.CellRendererText()
        column_key = Gtk.TreeViewColumn("Key", renderer_key, text=0)
        self.tree_view.append_column(column_key)
        
        # Value column
        renderer_value = Gtk.CellRendererText()
        column_value = Gtk.TreeViewColumn("Value", renderer_value, text=1)
        self.tree_view.append_column(column_value)
        
        scroll.add(self.tree_view)
        
        # Remove button beside the list
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(button_box, False, False, 5)
        
        # Spacer to push Remove button to the right
        button_box.pack_start(Gtk.Label(""), True, True, 0)
        
        remove_button = Gtk.Button.new_with_label("Remove")
        remove_button.connect("clicked", self.on_remove_clicked)
        button_box.pack_start(remove_button, False, False, 5)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(action_box, False, False, 5)
        
        save_button = Gtk.Button.new_with_label("Save")
        save_button.connect("clicked", self.on_save_clicked)
        action_box.pack_start(save_button, True, True, 5)
        
        cancel_button = Gtk.Button.new_with_label("Cancel")
        cancel_button.connect("clicked", self.on_cancel_clicked)
        action_box.pack_start(cancel_button, True, True, 5)
        
        replace_button = Gtk.Button.new_with_label("Replace")
        replace_button.connect("clicked", self.on_replace_clicked)
        action_box.pack_start(replace_button, True, True, 5)
        
        self.show_all()
    
    def update_list_store(self):
        self.list_store.clear()
        for key, value in self.replacements.items():
            self.list_store.append([key, value])
    
    def on_add_clicked(self, widget):
        key = self.key_entry.get_text()
        value = self.value_entry.get_text()
        
        if key and value:
            self.replacements[key] = value
            self.update_list_store()
            self.key_entry.set_text("")
            self.value_entry.set_text("")
    
    def on_remove_clicked(self, widget):
        selection = self.tree_view.get_selection()
        model, treeiter = selection.get_selected()
        
        if treeiter is not None:
            key = model[treeiter][0]
            if key in self.replacements:
                del self.replacements[key]
                self.update_list_store()
    
    def on_save_clicked(self, widget):
        self.parent.config.replacements = self.replacements.copy()
        self.parent.config.save_config()
        self.parent.update_status("Replacements saved")
        self.destroy()
    
    def on_cancel_clicked(self, widget):
        self.destroy()
    
    def on_replace_clicked(self, widget):
        self.parent.replace_bulk(self.replacements, self.parent.replacement_direction)


def main():
    editor = TextEditor()
    Gtk.main()

if __name__ == "__main__":
    main()
