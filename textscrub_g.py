#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TextScrub - A simple GTK text editor for Linux
# Features: Theme switching, font selection, bulk replace functionality


import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, Gdk, GLib, Pango, GtkSource
import json
import os
import re

class EditorConfig:
    """Configuration settings for the editor."""
    def __init__(self):
        self.window_x = 1000
        self.window_y = 800
        self.bulk_dialog_x = 600
        self.bulk_dialog_y = 400
        self.MAX_LIST_ROWS = 8

        # Create config directory if it doesn't exist
        self.config_dir = os.path.expanduser("~/.config/textscrub")
        self.config_file = os.path.join(self.config_dir, "textscrub-prefs.json")
        os.makedirs(self.config_dir, exist_ok=True)

        # Default configuration
        self.config = {
            "theme": "default",
            "font": "Monospace 12",
            "bulk_replace_dict": {}
        }

        # Load configuration if exists
        self.load_config()

    def load_config(self):
        """Load configuration from file if it exists."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

class ThemeManager:
    """Manages the themes for the application."""
    def __init__(self, editor_app):
        self.editor_app = editor_app
        self.config = editor_app.config

        # Define themes
        self.themes = {
            "default": {
                "use_system": True,
            },
            "solarized-light": {
                "use_system": False,
                "bg_color": "#fdf6e3",
                "fg_color": "#657b83",
                "menu_bg": "#eee8d5",
                "menu_fg": "#586e75",
                "status_bg": "#eee8d5",
                "status_fg": "#586e75",
                "selection_bg": "#93a1a1",
                "selection_fg": "#002b36",
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
                "selection_bg": "#586e75",
                "selection_fg": "#fdf6e3",
                "highlight_bg": "#ffff00",
                "highlight_fg": "#000000"
            }
        }
        self.css_provider = None

    def apply_theme(self, theme_name=None):
        """Apply the specified theme to all widgets."""
        if theme_name is None:
            theme_name = self.config.config.get("theme", "default")

        # Save theme preference
        self.config.config["theme"] = theme_name
        self.config.save_config()

        # Get theme settings
        theme = self.themes.get(theme_name, self.themes["default"])

        if theme.get("use_system", True):
            # Use system theme
            settings = Gtk.Settings.get_default()
            settings.props.gtk_application_prefer_dark_theme = False
            
            # Clear any custom CSS to restore system theme
            self._clear_custom_css()
        else:
            # Apply custom theme
            self._apply_custom_theme(theme)

    def _apply_custom_theme(self, theme):
        """Apply a custom theme to all widgets."""
        # Create CSS provider
        self.css_provider = Gtk.CssProvider()

        # Define CSS
        css = f"""
        window, dialog {{
            background-color: {theme['bg_color']};
            color: {theme['fg_color']};
        }}

        menubar, menu {{
            background-color: {theme['menu_bg']};
            color: {theme['menu_fg']};
        }}

        menuitem {{
            background-color: {theme['menu_bg']};
            color: {theme['menu_fg']};
        }}

        textview {{
            background-color: {theme['bg_color']};
            color: {theme['fg_color']};
        }}

        textview text {{
            background-color: {theme['bg_color']};
            color: {theme['fg_color']};
        }}

        textview text selection {{
            background-color: {theme['selection_bg']};
            color: {theme['selection_fg']};
        }}

        statusbar {{
            background-color: {theme['status_bg']};
            color: {theme['status_fg']};
        }}

        entry {{
            background-color: {theme['bg_color']};
            color: {theme['fg_color']};
        }}

        button {{
            background-color: {theme['menu_bg']};
            color: {theme['menu_fg']};
        }}

        treeview {{
            background-color: {theme['bg_color']};
            color: {theme['fg_color']};
        }}
        """

        self.css_provider.load_from_data(css.encode())

        # Apply CSS to the application
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # For resetting theme to "default"
    def _clear_custom_css(self):
        """Clear any custom CSS to restore system theme."""
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        if self.css_provider:
            style_context.remove_provider_for_screen(screen, self.css_provider)
            self.css_provider = None

class BulkReplaceDialog(Gtk.Dialog):
    """Dialog for managing bulk replacement key-value pairs."""
    def __init__(self, parent, config, text_buffer):
        super().__init__(title="Bulk Replace", transient_for=parent, modal=True)
        self.set_default_size(config.bulk_dialog_x, config.bulk_dialog_y)
        self.parent = parent
        self.config = config
        self.text_buffer = text_buffer
        self.replace_dict = config.config.get("bulk_replace_dict", {}).copy()

        # Don't create the tags twice
        tag_table = self.text_buffer.get_tag_table()
        self.highlight_tag = tag_table.lookup("highlight")
        if not self.highlight_tag:
            self.highlight_tag = self.text_buffer.create_tag(
                "highlight",
                background="yellow",
                foreground="black"
            )

        self.replace_mode = False  # False for normal, True for reverse replacement

        # Create dialog widgets
        self._create_widgets()
        self._populate_list()

        # Show the dialog
        self.show_all()

    def _create_widgets(self):
        """Create and arrange dialog widgets."""
        content_area = self.get_content_area()
        content_area.set_spacing(6)

        # Create top section for key-value entry
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Key entry
        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("Key")

        # Value entry
        self.value_entry = Gtk.Entry()
        self.value_entry.set_placeholder_text("Value")

        # Add button
        add_button = Gtk.Button(label="Add")
        add_button.connect("clicked", self._on_add_clicked)

        # Pack entries and button
        entry_box.pack_start(self.key_entry, True, True, 0)
        entry_box.pack_start(self.value_entry, True, True, 0)
        entry_box.pack_start(add_button, False, False, 0)

        # Create a scrollable list view for key-value pairs
        list_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        # Create a scrollable TreeView
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # Create a list store and view
        self.list_store = Gtk.ListStore(str, str)
        self.tree_view = Gtk.TreeView(model=self.list_store)

        # Create columns
        key_renderer = Gtk.CellRendererText()
        key_column = Gtk.TreeViewColumn("Key", key_renderer, text=0)
        self.tree_view.append_column(key_column)

        value_renderer = Gtk.CellRendererText()
        value_column = Gtk.TreeViewColumn("Value", value_renderer, text=1)
        self.tree_view.append_column(value_column)

        # Add treeview to scrolled window
        scrolled_window.add(self.tree_view)

        # Create a remove button
        remove_button = Gtk.Button(label="Remove")
        remove_button.connect("clicked", self._on_remove_clicked)

        # Pack treeview and remove button
        list_box.pack_start(scrolled_window, True, True, 0)
        list_box.pack_start(remove_button, False, False, 0)

        # Add bottom buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self._on_save_clicked)
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self._on_cancel_clicked)
        replace_button = Gtk.Button(label="Replace")
        replace_button.connect("clicked", self._on_replace_clicked)

        action_box.pack_start(save_button, True, True, 0)
        action_box.pack_start(cancel_button, True, True, 0)
        action_box.pack_start(replace_button, True, True, 0)

        # Add all sections to dialog
        content_area.pack_start(entry_box, False, False, 0)
        content_area.pack_start(list_box, True, True, 0)
        content_area.pack_start(action_box, False, False, 0)

    def _populate_list(self):
        """Populate the list with the current replacement dictionary."""
        self.list_store.clear()
        for key, value in self.replace_dict.items():
            self.list_store.append([key, value])

    def _on_add_clicked(self, button):
        """Handle Add button click."""
        key = self.key_entry.get_text()
        value = self.value_entry.get_text()

        if key and value:
            self.replace_dict[key] = value
            self.list_store.append([key, value])
            self.key_entry.set_text("")
            self.value_entry.set_text("")

    def _on_remove_clicked(self, button):
        """Handle Remove button click."""
        selection = self.tree_view.get_selection()
        model, treeiter = selection.get_selected()

        if treeiter is not None:
            key = model[treeiter][0]
            if key in self.replace_dict:
                del self.replace_dict[key]
            model.remove(treeiter)

    def _on_save_clicked(self, button):
        """Handle Save button click."""
        self.config.config["bulk_replace_dict"] = self.replace_dict
        self.config.save_config()
        self.response(Gtk.ResponseType.OK)

    def _on_cancel_clicked(self, button):
        """Handle Cancel button click."""
        self.response(Gtk.ResponseType.CANCEL)

    def _on_replace_clicked(self, button):
        """Handle Replace button click."""
        self.replace_bulk()

    def replace_bulk(self):
        """Perform bulk replacement in the text buffer."""
        if not self.replace_dict:
            # Get the TextScrubApp instance from the window
            app = self.parent.get_application()
            app.update_status("No replacements defined")
            return
        
        # Get text content
        start_iter = self.text_buffer.get_start_iter()
        end_iter = self.text_buffer.get_end_iter()
        content = self.text_buffer.get_text(start_iter, end_iter, True)

        # Remove all existing highlight tags
        self.text_buffer.remove_tag(
            self.highlight_tag,
            self.text_buffer.get_start_iter(),
            self.text_buffer.get_end_iter()
        )

        replacement_count = 0

        if not self.replace_mode:
            # Normal replacement (keys to values)
            for key, value in self.replace_dict.items():
                # Create case-insensitive pattern but preserve case in replacement
                pattern = re.compile(re.escape(key), re.IGNORECASE)

                # Find all matches to highlight later
                matches = list(pattern.finditer(content))
                replacement_count += len(matches)

                # Replace in content
                content = pattern.sub(value, content)
        else:
            # Reverse replacement (values back to keys)
            for key, value in self.replace_dict.items():
                pattern = re.compile(re.escape(value), re.IGNORECASE)
                matches = list(pattern.finditer(content))
                replacement_count += len(matches)
                content = pattern.sub(key, content)

        # Set the modified text
        self.text_buffer.set_text(content)

        # Highlight all replacements
        for key, value in self.replace_dict.items():
            search_text = value if not self.replace_mode else key
            start_iter = self.text_buffer.get_start_iter()

            # Find and highlight each occurrence
            while True:
                match = start_iter.forward_search(
                    search_text,
                    Gtk.TextSearchFlags.CASE_INSENSITIVE,
                    None
                )
                if match is None:
                    break

                match_start, match_end = match
                self.text_buffer.apply_tag(self.highlight_tag, match_start, match_end)
                start_iter = match_end

        # Toggle replacement mode for next time
        self.replace_mode = not self.replace_mode

        # Update status using the application instance
        app = self.parent.get_application()
        mode_str = "reverse" if self.replace_mode else "normal"
        app.update_status(f"Performed {replacement_count} replacements (Mode: {mode_str})")

class SearchDialog(Gtk.Dialog):
    """Dialog for searching text in the document."""
    def __init__(self, parent_window, app, text_buffer):
        super().__init__(title="Search", transient_for=parent_window, modal=True)
        self.set_default_size(400, 100)
        self.parent_window = parent_window
        self.app = app
        self.text_buffer = text_buffer
        self.search_tag = self.text_buffer.create_tag(
            "search_highlight",
            background="lightblue",
            foreground="black"
        )
        self.current_match = 0
        self.matches = []

        # Create dialog widgets
        self._create_widgets()

        # Show the dialog
        self.show_all()

    def _create_widgets(self):
        """Create and arrange dialog widgets."""
        content_area = self.get_content_area()
        content_area.set_spacing(6)

        # Search entry
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        search_label = Gtk.Label(label="Search:")
        self.search_entry = Gtk.Entry()
        self.search_entry.set_width_chars(30)
        self.search_entry.connect("activate", self._on_search_activated)

        search_box.pack_start(search_label, False, False, 0)
        search_box.pack_start(self.search_entry, True, True, 0)

        # Option checkboxes
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.case_sensitive = Gtk.CheckButton(label="Case sensitive")
        self.whole_word = Gtk.CheckButton(label="Whole word")

        options_box.pack_start(self.case_sensitive, True, True, 0)
        options_box.pack_start(self.whole_word, True, True, 0)

        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        search_button = Gtk.Button(label="Search")
        search_button.connect("clicked", self._on_search_activated)

        next_button = Gtk.Button(label="Next")
        next_button.connect("clicked", self._on_next_clicked)

        prev_button = Gtk.Button(label="Previous")
        prev_button.connect("clicked", self._on_prev_clicked)

        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self._on_close_clicked)

        button_box.pack_start(search_button, True, True, 0)
        button_box.pack_start(next_button, True, True, 0)
        button_box.pack_start(prev_button, True, True, 0)
        button_box.pack_end(close_button, True, True, 0)

        # Add all sections to dialog
        content_area.pack_start(search_box, False, False, 0)
        content_area.pack_start(options_box, False, False, 0)
        content_area.pack_start(button_box, False, False, 0)

    def _on_search_activated(self, widget):
        """Handle search request."""
        search_text = self.search_entry.get_text()
        if not search_text:
            return

        # Remove existing highlights
        start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        self.text_buffer.remove_tag(self.search_tag, start, end)

        # Get buffer text
        text = self.text_buffer.get_text(start, end, True)

        # Find matches
        self.matches = []
        case_sensitive = self.case_sensitive.get_active()
        whole_word = self.whole_word.get_active()

        # Prepare regex pattern
        if whole_word:
            pattern = r'\b' + re.escape(search_text) + r'\b'
        else:
            pattern = re.escape(search_text)

        flags = 0 if case_sensitive else re.IGNORECASE
        matches = list(re.finditer(pattern, text, flags))

        # Store matches and highlight them
        if matches:
            self.matches = matches
            self.current_match = 0
            self._highlight_matches()
            self._scroll_to_match(self.current_match)
            self.app.update_status(f"Found {len(matches)} matches")
        else:
            self.app.update_status("No matches found")

    def _highlight_matches(self):
        """Highlight all matches in the text buffer."""
        start_iter = self.text_buffer.get_start_iter()
        for match in self.matches:
            # Convert byte offsets to text iterators
            match_start = self.text_buffer.get_iter_at_offset(match.start())
            match_end = self.text_buffer.get_iter_at_offset(match.end())
            self.text_buffer.apply_tag(self.search_tag, match_start, match_end)


    def _scroll_to_match(self, match_index):
        """Scroll to the specified match."""
        if not self.matches or match_index >= len(self.matches):
            return
        match = self.matches[match_index]
        match_start = self.text_buffer.get_iter_at_offset(match.start())
        match_end = self.text_buffer.get_iter_at_offset(match.end())
        
        # Get the TextScrubApp instance from the window
        app = self.parent_window.get_application()
        
        # Select the text
        self.text_buffer.select_range(match_start, match_end)
        
        # Scroll the TextView to show the selection
        app.text_view.scroll_to_iter(
            match_start,
            0.0,  # within_margin
            False,  # use_align
            0.0,  # xalign
            0.3   # yalign - position at ~1/3 from the top
        )
    def _on_next_clicked(self, widget):
        """Move to the next match."""
        if not self.matches:
            return
        self.current_match = (self.current_match + 1) % len(self.matches)
        self._scroll_to_match(self.current_match)
        
        # Get the TextScrubApp instance from the window
        app = self.parent_window.get_application()
        
        # Update status using the application instance
        app.update_status(f"Match {self.current_match + 1} of {len(self.matches)}")

    def _on_prev_clicked(self, widget):
        """Move to the previous match."""
        if not self.matches:
            return

        self.current_match = (self.current_match - 1) % len(self.matches)
        self._scroll_to_match(self.current_match)
        app.update_status(f"Match {self.current_match + 1} of {len(self.matches)}")

    def _on_close_clicked(self, widget):
        """Close the search dialog."""
        self.response(Gtk.ResponseType.CLOSE)

class TextScrubApp(Gtk.Application):
    """Main application class."""
    def __init__(self):
        super().__init__(application_id="com.example.textscrub")
        self.config = EditorConfig()
        self.window = None
        self.text_buffer = None
        self.status_bar = None
        self.text_view = None
        self.theme_manager = None
        self.current_file = None
        self.connect("activate", self.on_activate)

        # track the replace mode in the replace dialog class
        self.replace_mode = False

        # Create an AccelGroup
        self.accel_group = Gtk.AccelGroup()

    def on_activate(self, app):
        """Initialize application window and components."""
        # Create window
        self.window = Gtk.ApplicationWindow(application=app, title="TextScrub Editor")
        self.window.set_default_size(self.config.window_x, self.config.window_y)

        # Add the AccelGroup to the window
        self.window.add_accel_group(self.accel_group)

        # Set up theme manager
        self.theme_manager = ThemeManager(self)

        # Create UI components
        self._create_ui()

        # Apply theme
        self.theme_manager.apply_theme()

        # Apply font
        self._apply_font(self.config.config.get("font", "Monospace 12"))

        # Apply word wrap setting from preferences
        word_wrap_state = self.config.config.get("word_wrap", True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD if word_wrap_state else Gtk.WrapMode.NONE)

        # Show window
        self.window.show_all()

    def _create_ui(self):
        """Create UI components."""
        # Create main layout box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(vbox)

        # Create menu bar
        menu_bar = self._create_menu_bar()
        vbox.pack_start(menu_bar, False, False, 0)

        # Create scrollable text view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # Use GtkSourceView for text editing
        self.text_view = GtkSource.View()
        self.text_buffer = self.text_view.get_buffer()
        self.text_buffer.connect("changed", self._on_text_changed)

        scrolled_window.add(self.text_view)
        vbox.pack_start(scrolled_window, True, True, 0)

        # Create status bar
        self.status_bar = Gtk.Statusbar()
        vbox.pack_start(self.status_bar, False, False, 0)

        # Set initial status message
        self.update_status("Ready")

    def _create_menu_bar(self):
        """Create menu bar with File, Edit, and Search menus."""
        # Create menu bar
        menu_bar = Gtk.MenuBar()

        # File menu
        file_menu = self._create_file_menu()
        menu_bar.append(file_menu)

        # Edit menu
        edit_menu = self._create_edit_menu()
        menu_bar.append(edit_menu)

        # Search menu
        search_menu = self._create_search_menu()
        menu_bar.append(search_menu)

        return menu_bar

    def _create_file_menu(self):
        """Create the File menu with its items."""
        file_item = Gtk.MenuItem(label="File")
        file_menu = Gtk.Menu()
        file_item.set_submenu(file_menu)

        # New
        new_item = Gtk.MenuItem(label="New")
        new_item.connect("activate", self._on_new_clicked)
        new_item.add_accelerator("activate", self.accel_group, ord('N'),
                                 Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        file_menu.append(new_item)

        # Open
        open_item = Gtk.MenuItem(label="Open")
        open_item.connect("activate", self._on_open_clicked)
        open_item.add_accelerator("activate", self.accel_group, ord('O'),
                                  Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        file_menu.append(open_item)

        # Save
        save_item = Gtk.MenuItem(label="Save")
        save_item.connect("activate", self._on_save_clicked)
        save_item.add_accelerator("activate", self.accel_group, ord('S'),
                                  Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        file_menu.append(save_item)

        # Save As
        save_as_item = Gtk.MenuItem(label="Save As")
        save_as_item.connect("activate", self._on_save_as_clicked)
        save_as_item.add_accelerator("activate", self.accel_group, ord('S'),
                                    Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
                                    Gtk.AccelFlags.VISIBLE)
        file_menu.append(save_as_item)

        # Separator
        file_menu.append(Gtk.SeparatorMenuItem())

        # Exit
        exit_item = Gtk.MenuItem(label="Exit")
        exit_item.connect("activate", self._on_exit_clicked)
        exit_item.add_accelerator("activate", self.accel_group, ord('Q'),
                                 Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        file_menu.append(exit_item)

        return file_item

    def _create_edit_menu(self):
        """Create the Edit menu with its items."""
        edit_item = Gtk.MenuItem(label="Edit")
        edit_menu = Gtk.Menu()
        edit_item.set_submenu(edit_menu)

        # Undo
        undo_item = Gtk.MenuItem(label="Undo")
        undo_item.connect("activate", self._on_undo_clicked)
        undo_item.add_accelerator("activate", self.accel_group, ord('Z'),
                                  Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        edit_menu.append(undo_item)

        # Redo
        redo_item = Gtk.MenuItem(label="Redo")
        redo_item.connect("activate", self._on_redo_clicked)
        redo_item.add_accelerator("activate", self.accel_group, ord('Y'),
                                  Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        edit_menu.append(redo_item)

        # Separator
        edit_menu.append(Gtk.SeparatorMenuItem())

        # Cut
        cut_item = Gtk.MenuItem(label="Cut")
        cut_item.connect("activate", self._on_cut_clicked)
        cut_item.add_accelerator("activate", self.accel_group, ord('X'),
                                Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        edit_menu.append(cut_item)

        # Copy
        copy_item = Gtk.MenuItem(label="Copy")
        copy_item.connect("activate", self._on_copy_clicked)
        copy_item.add_accelerator("activate", self.accel_group, ord('C'),
                                 Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        edit_menu.append(copy_item)

        # Paste
        paste_item = Gtk.MenuItem(label="Paste")
        paste_item.connect("activate", self._on_paste_clicked)
        paste_item.add_accelerator("activate", self.accel_group, ord('V'),
                                  Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        edit_menu.append(paste_item)

        # Separator
        edit_menu.append(Gtk.SeparatorMenuItem())

        # Theme
        theme_item = Gtk.MenuItem(label="Theme")
        theme_menu = Gtk.Menu()
        theme_item.set_submenu(theme_menu)

        # Default theme
        default_theme = Gtk.MenuItem(label="Default Theme")
        default_theme.connect("activate", self._on_theme_selected, "default")
        theme_menu.append(default_theme)

        # Solarized Light theme
        light_theme = Gtk.MenuItem(label="Solarized Light")
        light_theme.connect("activate", self._on_theme_selected, "solarized-light")
        theme_menu.append(light_theme)

        # Solarized Dark theme
        dark_theme = Gtk.MenuItem(label="Solarized Dark")
        dark_theme.connect("activate", self._on_theme_selected, "solarized-dark")
        theme_menu.append(dark_theme)

        edit_menu.append(theme_item)

        # Font
        font_item = Gtk.MenuItem(label="Font")
        font_item.connect("activate", self._on_font_clicked)
        edit_menu.append(font_item)

        # Bulk Replace
        bulk_replace_item = Gtk.MenuItem(label="Bulk Replace")
        bulk_replace_item.connect("activate", self._on_bulk_replace_clicked)
        edit_menu.append(bulk_replace_item)
        bulk_replace_item.add_accelerator("activate", self.accel_group, ord('B'), 
                                             Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        
        # CTRL+R for replace
        execute_replace_item = Gtk.MenuItem(label="Replace")
        execute_replace_item.connect("activate", self._on_bulk_replace_execute)
        execute_replace_item.add_accelerator("activate", self.accel_group, ord('R'), 
                                             Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        edit_menu.append(execute_replace_item)

        #bulk_replace_item.add_accelerator("activate", self.accel_group, ord('R'), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        # Separator
        edit_menu.append(Gtk.SeparatorMenuItem())

        # Word Wrap
        word_wrap_item = Gtk.CheckMenuItem(label="Word Wrap")
        word_wrap_item.set_active(True)  # Enable by default
        word_wrap_item.connect("toggled", self._on_word_wrap_toggled)
        edit_menu.append(word_wrap_item)

        return edit_item

    def _create_search_menu(self):
        """Create the Search menu with its items."""
        search_item = Gtk.MenuItem(label="Search")
        search_menu = Gtk.Menu()
        search_item.set_submenu(search_menu)

        # Find
        find_item = Gtk.MenuItem(label="Find")
        find_item.connect("activate", self._on_find_clicked)
        find_item.add_accelerator("activate", self.accel_group, ord('F'),
                                 Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        search_menu.append(find_item)

        return search_item

    def update_status(self, message):
        """Update status bar with a message."""
        context_id = self.status_bar.get_context_id("main")
        self.status_bar.pop(context_id)
        self.status_bar.push(context_id, message)

    def _on_text_changed(self, buffer):
        """Handle text changes."""
        # Update window title to show unsaved changes
        title = self.window.get_title()
        if not title.startswith("*") and not self.text_buffer.get_char_count() == 0:
            self.window.set_title("*" + title)

    def _on_new_clicked(self, widget):
        """Handle New menu item."""
        # Check for unsaved changes
        if self._check_unsaved_changes():
            return

        # Clear buffer
        self.text_buffer.set_text("")
        self.current_file = None
        self.window.set_title("TextScrub Editor")
        self.update_status("New document created")

    def _on_open_clicked(self, widget):
        """Handle Open menu item."""
        # Check for unsaved changes
        if self._check_unsaved_changes():
            return

        # Create file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Open File",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        # Add filters
        self._add_file_filters(dialog)

        # Show dialog
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            self._load_file(file_path)

        dialog.destroy()

    def _on_save_clicked(self, widget):
        """Handle Save menu item."""
        if self.current_file:
            self._save_file(self.current_file)
        else:
            self._on_save_as_clicked(widget)

    def _on_save_as_clicked(self, widget):
        """Handle Save As menu item."""
        # Create file chooser dialog
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

        # Add filters
        self._add_file_filters(dialog)

        # Show dialog
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            self._save_file(file_path)

        dialog.destroy()

    def _on_exit_clicked(self, widget):
        """Handle Exit menu item."""
        if self._check_unsaved_changes():
            return

        self.quit()

    def _on_undo_clicked(self, widget):
        """Handle Undo menu item."""
        if self.text_buffer.can_undo():
            self.text_buffer.undo()
            self.update_status("Undo operation performed")
        else:
            self.update_status("Nothing to undo")

    def _on_redo_clicked(self, widget):
        """Handle Redo menu item."""
        if self.text_buffer.can_redo():
            self.text_buffer.redo()
            self.update_status("Redo operation performed")
        else:
            self.update_status("Nothing to redo")

    def _on_cut_clicked(self, widget):
        """Handle Cut menu item."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.cut_clipboard(clipboard, True)
        self.update_status("Cut selection to clipboard")

    def _on_copy_clicked(self, widget):
        """Handle Copy menu item."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.copy_clipboard(clipboard)
        self.update_status("Copied selection to clipboard")

    def _on_paste_clicked(self, widget):
        """Handle Paste menu item."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.text_buffer.paste_clipboard(clipboard, None, True)
        self.update_status("Pasted from clipboard")

    def _on_theme_selected(self, widget, theme_name):
        """Handle theme selection."""
        self.theme_manager.apply_theme(theme_name)
        self.update_status(f"Theme changed to {theme_name}")

    def _on_font_clicked(self, widget):
        """Handle Font menu item."""
        font_dialog = Gtk.FontChooserDialog(title="Select Font", parent=self.window)

        # Set current font
        current_font = self.config.config.get("font", "Monospace 12")
        font_dialog.set_font(current_font)

        response = font_dialog.run()
        if response == Gtk.ResponseType.OK:
            font = font_dialog.get_font()
            if font:
                self._apply_font(font)
                self.config.config["font"] = font
                self.config.save_config()
                self.update_status(f"Font changed to {font}")

        font_dialog.destroy()

    def _on_bulk_replace_clicked(self, widget):
        """Handle Bulk Replace menu item."""
        dialog = BulkReplaceDialog(self.window, self.config, self.text_buffer)            
        dialog.run()
        dialog.destroy()

    def _on_bulk_replace_execute(self, widget):
        """Execute bulk replace without showing the dialog."""
        if self.config.config.get("bulk_replace_dict", {}):
            # Create dialog just to access replace_bulk functionality
            dialog = BulkReplaceDialog(self.window, self.config, self.text_buffer)
            
            # Pass the current mode to the dialog
            dialog.replace_mode = self.replace_mode
            dialog.replace_bulk()

            # save the mode
            self.replace_mode = dialog.replace_mode
            dialog.destroy()
        else:
            self.update_status("No replacements defined. Set up replacements first.")
            
    def _on_word_wrap_toggled(self, widget):
        """Handle Word Wrap checkbox toggle."""
        wrap_mode = Gtk.WrapMode.WORD if widget.get_active() else Gtk.WrapMode.NONE
        self.text_view.set_wrap_mode(wrap_mode)
        status = "enabled" if widget.get_active() else "disabled"
        self.update_status(f"Word wrap {status}")

        # Save the word wrap state to preferences
        self.config.config["word_wrap"] = widget.get_active()
        self.config.save_config()

    def _on_find_clicked(self, widget):
        """Handle Find menu item."""
        search_dialog = SearchDialog(self.window, self, self.text_buffer)
        search_dialog.run()
        search_dialog.destroy()

    def _load_file(self, file_path):
        """Load a file into the text buffer."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            self.text_buffer.set_text(content)
            self.current_file = file_path
            self.window.set_title(f"TextScrub Editor - {os.path.basename(file_path)}")
            self.update_status(f"Loaded {file_path}")

            # Reset the modified state
            self.text_buffer.set_modified(False)

            # Apply word wrap setting from preferences
            word_wrap_state = self.config.config.get("word_wrap", True)
            self.text_view.set_wrap_mode(Gtk.WrapMode.WORD if word_wrap_state else Gtk.WrapMode.NONE)

        except Exception as e:
            self.update_status(f"Error loading file: {e}")

    def _save_file(self, file_path):
        """Save text buffer to a file."""
        try:
            start_iter = self.text_buffer.get_start_iter()
            end_iter = self.text_buffer.get_end_iter()
            content = self.text_buffer.get_text(start_iter, end_iter, True)

            with open(file_path, 'w') as f:
                f.write(content)

            self.current_file = file_path
            self.window.set_title(f"TextScrub Editor - {os.path.basename(file_path)}")
            self.update_status(f"Saved to {file_path}")

            # Reset the modified state
            self.text_buffer.set_modified(False)

        except Exception as e:
            self.update_status(f"Error saving file: {e}")

    def _check_unsaved_changes(self):
        """Check for unsaved changes and prompt user if needed.

        Returns:
            bool: True if the operation should be cancelled, False otherwise.
        """
        if self.text_buffer.get_modified():
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Unsaved Changes"
            )
            dialog.format_secondary_text(
                "Do you want to save changes before closing?"
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)

            response = dialog.run()
            dialog.destroy()

            if response == Gtk.ResponseType.YES:
                self._on_save_clicked(None)
                return False
            elif response == Gtk.ResponseType.NO:
                return False
            else:  # CANCEL
                return True

        return False

    def _add_file_filters(self, dialog):
        """Add file filters to a file dialog."""
        # Text files filter
        text_filter = Gtk.FileFilter()
        text_filter.set_name("Text files")
        text_filter.add_mime_type("text/plain")
        dialog.add_filter(text_filter)

        # All files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)

    def _apply_font(self, font_string):
        """Apply font to text view using proper CSS syntax."""
        # Convert Pango font string to CSS font properties
        try:
            # Parse the font description
            font_desc = Pango.FontDescription.from_string(font_string)
            
            # Extract font properties
            family = font_desc.get_family() or "Monospace"
            size_pts = font_desc.get_size() / Pango.SCALE
            weight = "normal"
            style = "normal"
            
            if font_desc.get_weight() >= Pango.Weight.BOLD:
                weight = "bold"
            
            if font_desc.get_style() == Pango.Style.ITALIC:
                style = "italic"
            
            # Create CSS with proper syntax
            css = f"""
            textview {{
                font-family: "{family}";
                font-size: {size_pts}pt;
                font-weight: {weight};
                font-style: {style};
            }}
            """
            
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(css.encode())
            
            context = self.text_view.get_style_context()
            context.add_provider(
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Error applying font: {e}")
            # Fallback - set a basic monospace font
            fallback_css = """
            textview {
                font-family: "Monospace";
                font-size: 12pt;
            }
            """
            fallback_provider = Gtk.CssProvider()
            fallback_provider.load_from_data(fallback_css.encode())
            self.text_view.get_style_context().add_provider(
                fallback_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )


if __name__ == "__main__":
    app = TextScrubApp()
    app.run()
