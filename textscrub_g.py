#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import os
import json
import re

class EditorConfig:
    def __init__(self):
        self.window_x = 1000
        self.window_y = 800
        self.bulk_dialog_x = 600
        self.bulk_dialog_y = 400
        self.config_dir = os.path.expanduser("~/.config/textscrub")
        self.config_file = os.path.join(self.config_dir, "textscrub-prefs.json")
        self.theme = "default"
        self.bulk_replace_dict = {}
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.theme = config.get('theme', 'default')
                    self.bulk_replace_dict = config.get('bulk_replace_dict', {})
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        config = {
            'theme': self.theme,
            'bulk_replace_dict': self.bulk_replace_dict
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

class ThemeManager:
    def __init__(self, config):
        self.config = config
        
        # Define theme colors
        self.themes = {
            "default": {
                "use_system": True
            },
            "solarized-light": {
                "use_system": False,
                "bg_color": "#fdf6e3",
                "fg_color": "#657b83",
                "menu_bg": "#eee8d5",
                "menu_fg": "#073642",
                "status_bg": "#eee8d5",
                "status_fg": "#073642",
                "selection_bg": "#d33682",
                "selection_fg": "#fdf6e3",
                "highlight_bg": "#ffff00",
                "highlight_fg": "#000000"
            },
            "solarized-dark": {
                "use_system": False,
                "bg_color": "#002b36",
                "fg_color": "#839496",
                "menu_bg": "#073642",
                "menu_fg": "#93a1a1",
                "status_bg": "#073642",
                "status_fg": "#93a1a1",
                "selection_bg": "#d33682",
                "selection_fg": "#fdf6e3",
                "highlight_bg": "#ffff00",
                "highlight_fg": "#000000"
            }
        }
    
    def get_current_theme(self):
        return self.themes.get(self.config.theme, self.themes["default"])
    
    def apply_theme(self, window, text_view, status_bar):
        theme = self.get_current_theme()
        
        # Create CSS provider
        provider = Gtk.CssProvider()
        
        if theme["use_system"]:
            # Reset to system theme
            screen = Gdk.Screen.get_default()
            style_context = window.get_style_context()
            Gtk.StyleContext.remove_provider_for_screen(screen, provider)
            
            # Reset text view to default
            text_view.override_background_color(Gtk.StateFlags.NORMAL, None)
            text_view.override_color(Gtk.StateFlags.NORMAL, None)
            
            # Reset status bar to default
            status_bar.override_background_color(Gtk.StateFlags.NORMAL, None)
            status_bar.override_color(Gtk.StateFlags.NORMAL, None)
        else:
            # Apply custom theme
            css = f"""
            menubar {{
                background-color: {theme["menu_bg"]};
                color: {theme["menu_fg"]};
            }}
            menuitem {{
                background-color: {theme["menu_bg"]};
                color: {theme["menu_fg"]};
            }}
            menu {{
                background-color: {theme["menu_bg"]};
                color: {theme["menu_fg"]};
            }}
            """
            
            provider.load_from_data(bytes(css.encode()))
            screen = Gdk.Screen.get_default()
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
            # Set text view colors
            bg_color = Gdk.RGBA()
            bg_color.parse(theme["bg_color"])
            fg_color = Gdk.RGBA()
            fg_color.parse(theme["fg_color"])
            
            text_view.override_background_color(Gtk.StateFlags.NORMAL, bg_color)
            text_view.override_color(Gtk.StateFlags.NORMAL, fg_color)
            
            # Set status bar colors
            status_bg = Gdk.RGBA()
            status_bg.parse(theme["status_bg"])
            status_fg = Gdk.RGBA()
            status_fg.parse(theme["status_fg"])
            
            status_bar.override_background_color(Gtk.StateFlags.NORMAL, status_bg)
            status_bar.override_color(Gtk.StateFlags.NORMAL, status_fg)

class BulkReplaceDialog(Gtk.Dialog):
    def __init__(self, parent, config, theme_manager):
        super().__init__(title="Bulk Replace", transient_for=parent, flags=0)
        self.config = config
        self.theme_manager = theme_manager
        self.set_default_size(config.bulk_dialog_x, config.bulk_dialog_y)
        
        # Dictionary to track changes
        self.replace_dict = self.config.bulk_replace_dict.copy()
        self.MAX_LIST_ROWS = 8
        
        # Main container
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_border_width(10)
        
        # Input area
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(input_box, False, False, 0)
        
        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("Key")
        self.value_entry = Gtk.Entry()
        self.value_entry.set_placeholder_text("Value")
        
        add_button = Gtk.Button(label="Add")
        add_button.connect("clicked", self.on_add_clicked)
        
        input_box.pack_start(self.key_entry, True, True, 0)
        input_box.pack_start(self.value_entry, True, True, 0)
        input_box.pack_start(add_button, False, False, 0)
        
        # List box with scrolling
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(self.MAX_LIST_ROWS * 30)  # Approximate height for rows
        box.pack_start(scroll, True, True, 0)
        
        list_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Dictionary items list
        self.list_store = Gtk.ListStore(str, str)
        self.tree_view = Gtk.TreeView(model=self.list_store)
        
        renderer_key = Gtk.CellRendererText()
        column_key = Gtk.TreeViewColumn("Key", renderer_key, text=0)
        self.tree_view.append_column(column_key)
        
        renderer_value = Gtk.CellRendererText()
        column_value = Gtk.TreeViewColumn("Value", renderer_value, text=1)
        self.tree_view.append_column(column_value)
        
        scroll.add(self.tree_view)
        
        # Remove button next to the list
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        remove_button = Gtk.Button(label="Remove")
        remove_button.connect("clicked", self.on_remove_clicked)
        button_box.pack_start(remove_button, False, False, 0)
        
        list_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        list_area.pack_start(scroll, True, True, 0)
        list_area.pack_start(button_box, False, False, 0)
        box.pack_start(list_area, True, True, 0)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(action_box, False, False, 0)
        
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.on_save_clicked)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self.on_cancel_clicked)
        
        replace_button = Gtk.Button(label="Replace")
        replace_button.connect("clicked", self.on_replace_clicked)
        
        action_box.pack_start(save_button, False, False, 0)
        action_box.pack_start(cancel_button, False, False, 0)
        action_box.pack_start(replace_button, False, False, 0)
        
        # Populate the list with existing entries
        self.populate_list()
        
        self.show_all()
    
    def populate_list(self):
        self.list_store.clear()
        for key, value in self.replace_dict.items():
            self.list_store.append([key, value])
    
    def on_add_clicked(self, button):
        key = self.key_entry.get_text()
        value = self.value_entry.get_text()
        
        if key and value:
            self.replace_dict[key] = value
            self.populate_list()
            self.key_entry.set_text("")
            self.value_entry.set_text("")
    
    def on_remove_clicked(self, button):
        selection = self.tree_view.get_selection()
        model, iter = selection.get_selected()
        
        if iter:
            key = model[iter][0]
            if key in self.replace_dict:
                del self.replace_dict[key]
                self.populate_list()
    
    def on_save_clicked(self, button):
        self.config.bulk_replace_dict = self.replace_dict.copy()
        self.config.save_config()
        self.response(Gtk.ResponseType.OK)
    
    def on_cancel_clicked(self, button):
        self.response(Gtk.ResponseType.CANCEL)
    
    def on_replace_clicked(self, button):
        self.response(Gtk.ResponseType.APPLY)

class TextEditor:
    def __init__(self):
        self.config = EditorConfig()
        self.theme_manager = ThemeManager(self.config)
        self.highlighted_tags = []
        self.reverse_replace = False
        
        # Set up the window
        self.window = Gtk.Window(title="TextScrub")
        self.window.set_default_size(self.config.window_x, self.config.window_y)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(vbox)
        
        # Menu bar
        self.menubar = Gtk.MenuBar()
        vbox.pack_start(self.menubar, False, False, 0)
        
        # File menu
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_submenu(file_menu)
        
        new_item = Gtk.MenuItem(label="New")
        new_item.connect("activate", self.on_new)
        file_menu.append(new_item)
        
        open_item = Gtk.MenuItem(label="Open")
        open_item.connect("activate", self.on_open)
        file_menu.append(open_item)
        
        save_item = Gtk.MenuItem(label="Save")
        save_item.connect("activate", self.on_save)
        file_menu.append(save_item)
        
        save_as_item = Gtk.MenuItem(label="Save As")
        save_as_item.connect("activate", self.on_save_as)
        file_menu.append(save_as_item)
        
        file_menu.append(Gtk.SeparatorMenuItem())
        
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", Gtk.main_quit)
        file_menu.append(quit_item)
        
        self.menubar.append(file_item)
        
        # Edit menu
        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label="Edit")
        edit_item.set_submenu(edit_menu)
        
        cut_item = Gtk.MenuItem(label="Cut")
        cut_item.connect("activate", self.on_cut)
        edit_menu.append(cut_item)
        
        copy_item = Gtk.MenuItem(label="Copy")
        copy_item.connect("activate", self.on_copy)
        edit_menu.append(copy_item)
        
        paste_item = Gtk.MenuItem(label="Paste")
        paste_item.connect("activate", self.on_paste)
        edit_menu.append(paste_item)
        
        edit_menu.append(Gtk.SeparatorMenuItem())
        
        # Theme submenu
        theme_menu = Gtk.Menu()
        theme_item = Gtk.MenuItem(label="Theme")
        theme_item.set_submenu(theme_menu)
        
        default_theme = Gtk.MenuItem(label="Default")
        default_theme.connect("activate", self.on_theme_changed, "default")
        theme_menu.append(default_theme)
        
        light_theme = Gtk.MenuItem(label="Solarized Light")
        light_theme.connect("activate", self.on_theme_changed, "solarized-light")
        theme_menu.append(light_theme)
        
        dark_theme = Gtk.MenuItem(label="Solarized Dark")
        dark_theme.connect("activate", self.on_theme_changed, "solarized-dark")
        theme_menu.append(dark_theme)
        
        edit_menu.append(theme_item)
        
        bulk_replace_item = Gtk.MenuItem(label="Bulk Replace")
        bulk_replace_item.connect("activate", self.on_bulk_replace)
        edit_menu.append(bulk_replace_item)
        
        self.menubar.append(edit_item)
        
        # Search menu
        search_menu = Gtk.Menu()
        search_item = Gtk.MenuItem(label="Search")
        search_item.set_submenu(search_menu)
        
        find_item = Gtk.MenuItem(label="Find")
        find_item.connect("activate", self.on_find)
        search_menu.append(find_item)
        
        replace_item = Gtk.MenuItem(label="Replace")
        replace_item.connect("activate", self.on_replace)
        search_menu.append(replace_item)
        
        self.menubar.append(search_item)
        
        # Text view with scrolling
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scroll, True, True, 0)
        
        self.text_view = Gtk.TextView()
        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.connect("changed", self.on_text_changed)
        scroll.add(self.text_view)
        
        # Status bar
        self.statusbar = Gtk.Statusbar()
        vbox.pack_start(self.statusbar, False, False, 0)
        
        # Set up text tags for highlighting
        self.setup_tags()
        
        # Apply the theme
        self.theme_manager.apply_theme(self.window, self.text_view, self.statusbar)
        
        # Initialize current file
        self.current_file = None
        
        # Update status bar
        self.update_status("Ready")
        
        # Show all elements
        self.window.show_all()

    def setup_tags(self):
        self.text_buffer.create_tag("highlight", 
                                   background="#ffff00", 
                                   foreground="#000000")
    
    def update_status(self, message):
        context_id = self.statusbar.get_context_id("editor_status")
        self.statusbar.pop(context_id)
        self.statusbar.push(context_id, message)
    
    def on_new(self, widget):
        self.text_buffer.set_text("")
        self.current_file = None
        self.update_status("New file created")
    
    def on_open(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Open File",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
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
                    self.current_file = filename
                    self.update_status(f"Opened {filename}")
            except Exception as e:
                self.update_status(f"Error opening file: {e}")
        
        dialog.destroy()
    
    def on_save(self, widget):
        if self.current_file:
            self.save_file(self.current_file)
        else:
            self.on_save_as(widget)
    
    def on_save_as(self, widget):
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
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.save_file(filename)
        
        dialog.destroy()
    
    def save_file(self, filename):
        start, end = self.text_buffer.get_bounds()
        text = self.text_buffer.get_text(start, end, False)
        
        try:
            with open(filename, 'w') as f:
                f.write(text)
            self.current_file = filename
            self.update_status(f"Saved to {filename}")
        except Exception as e:
            self.update_status(f"Error saving file: {e}")
    
    def on_cut(self, widget):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.cut_clipboard(clipboard, True)
        self.update_status("Cut selection to clipboard")
    
    def on_copy(self, widget):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.copy_clipboard(clipboard)
        self.update_status("Copied selection to clipboard")
    
    def on_paste(self, widget):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.paste_clipboard(clipboard, None, True)
        self.update_status("Pasted from clipboard")
    
    def on_find(self, widget):
        # Simple find dialog
        dialog = Gtk.Dialog(
            title="Find",
            parent=self.window,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_FIND, Gtk.ResponseType.OK
        )
        
        box = dialog.get_content_area()
        box.set_spacing(6)
        
        label = Gtk.Label(label="Search for:")
        box.add(label)
        
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        box.add(entry)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            search_text = entry.get_text()
            if search_text:
                self.find_text(search_text)
        
        dialog.destroy()
    
    def find_text(self, search_text):
        text = self.text_buffer.get_text(
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter(),
            False
        )
        
        count = text.lower().count(search_text.lower())
        if count > 0:
            self.update_status(f"Found {count} occurrences of '{search_text}'")
        else:
            self.update_status(f"No matches found for '{search_text}'")
    
    def on_replace(self, widget):
        # Simple replace dialog
        dialog = Gtk.Dialog(
            title="Replace",
            parent=self.window,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_FIND_AND_REPLACE, Gtk.ResponseType.OK
        )
        
        box = dialog.get_content_area()
        box.set_spacing(6)
        
        find_label = Gtk.Label(label="Search for:")
        box.add(find_label)
        
        find_entry = Gtk.Entry()
        box.add(find_entry)
        
        replace_label = Gtk.Label(label="Replace with:")
        box.add(replace_label)
        
        replace_entry = Gtk.Entry()
        replace_entry.set_activates_default(True)
        box.add(replace_entry)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            find_text = find_entry.get_text()
            replace_text = replace_entry.get_text()
            if find_text:
                count = self.replace_text(find_text, replace_text)
                self.update_status(f"Replaced {count} occurrences")
        
        dialog.destroy()
    
    def replace_text(self, find_text, replace_text):
        text = self.text_buffer.get_text(
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter(),
            False
        )
        
        new_text = text.replace(find_text, replace_text)
        count = text.count(find_text)
        
        if new_text != text:
            self.text_buffer.set_text(new_text)
        
        return count
    
    def on_theme_changed(self, widget, theme_name):
        self.config.theme = theme_name
        self.config.save_config()
        self.theme_manager.apply_theme(self.window, self.text_view, self.statusbar)
        self.update_status(f"Theme changed to {theme_name}")
    
    def on_bulk_replace(self, widget):
        dialog = BulkReplaceDialog(self.window, self.config, self.theme_manager)
        response = dialog.run()
        
        if response == Gtk.ResponseType.APPLY:
            self.replace_bulk(dialog.replace_dict)
        
        dialog.destroy()
    
    def replace_bulk(self, replace_dict):
        # Remove existing highlights
        start, end = self.text_buffer.get_bounds()
        self.text_buffer.remove_tag_by_name("highlight", start, end)
        
        # Get the text
        text = self.text_buffer.get_text(start, end, False)
        new_text = text
        replacements = 0
        
        # Create a list to track replacements
        replacements_info = []
        
        if self.reverse_replace:
            # Replace values with keys
            for key, value in replace_dict.items():
                pattern = re.compile(re.escape(value))
                matches = pattern.finditer(new_text)
                for match in matches:
                    replacements_info.append((match.start(), match.end(), key))
                
                new_text = pattern.sub(key, new_text)
        else:
            # Replace keys with values
            for key, value in replace_dict.items():
                pattern = re.compile(re.escape(key), re.IGNORECASE)
                matches = pattern.finditer(new_text)
                for match in matches:
                    replacements_info.append((match.start(), match.end(), value))
                
                new_text = pattern.sub(value, new_text)
        
        # Set the new text
        self.text_buffer.set_text(new_text)
        
        # Apply highlights to replaced text
        for start_pos, end_pos, replacement in replacements_info:
            start_iter = self.text_buffer.get_iter_at_offset(start_pos)
            end_iter = self.text_buffer.get_iter_at_offset(start_pos + len(replacement))
            self.text_buffer.apply_tag_by_name("highlight", start_iter, end_iter)
            replacements += 1
        
        # Toggle for next time
        self.reverse_replace = not self.reverse_replace
        
        # Update status
        direction = "values to keys" if self.reverse_replace else "keys to values"
        self.update_status(f"Replaced {replacements} occurrences. Next replacement will be {direction}.")
    
    def on_text_changed(self, buffer):
        # This method can be expanded for more functionality
        pass

def main():
    editor = TextEditor()
    Gtk.main()

if __name__ == "__main__":
    main()