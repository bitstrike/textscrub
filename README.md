# TextScrub: Bulk Replace Tool for Text Sanitization


## Overview
TextScrub is a simple text editor designed to aid in redacting text by bulk replacing specified keywords. This tool is particularly useful for preparing text to be pasted into AI chat by removing or replacing sensitive identifiers with more anonymous data. What makes this a little more handy than a regular text editor is that you define a list of key/value pairs for replacement in bulk rather than one word at a time. This list is saved to a json file in your home directory so it's available when you launch the editor again.

I lost some percentage of my eyesight while developing this due to the default white background and black text of the widgets so I added some simple coloring that sort of resembles theming. The submenu items and dialogs are still the default gray and I don't know why. I started to read some documentation on it and it reminded me of C++ and I closed my browser. Besides, this thing was 99% done with AI (I _am_ writing some of the README) and reading documentation takes the fun out of it.


## Features
- **Bulk Replace**: Replace multiple keywords with corresponding values throughout the document.
- **Themes**: Choose between different color themes (Standard, Dark, Light) to customize the editor's appearance.
- **Hotkeys**: Efficiently perform actions using keyboard shortcuts.
- **Preferences**: Save and load preferences, including themes and bulk replace pairs, for a consistent user experience.

## Hotkeys
- **File Menu**
  - New: `Ctrl+N` - Create a new document.
  - Open: `Ctrl+O` - Open an existing document.
  - Save: `Ctrl+S` - Save the current document.
  - Exit: `Alt+F4` - Exit the application.
- **Edit Menu**
  - Undo: `Ctrl+Z` - Undo the last action.
  - Redo: `Ctrl+Y` - Redo the last undone action.
  - Cut: `Ctrl+X` - Cut the selected text.
  - Copy: `Ctrl+C` - Copy the selected text.
  - Paste: `Ctrl+V` - Paste the copied text.
  - Select All: `Ctrl+A` - Select all text in the document.
  - ReplaceBulk: `Ctrl+R` - Replace all instances of specified keywords with corresponding values and highlight the changes.
- **Search Menu**
  - Find: `Ctrl+F` - Search for text within the document.
  - Bulk Replace: `Ctrl+B` - Open the bulk replace dialog to manage key-value pairs.
  - Reverse Replace: `Ctrl+R` - Perform a bulk reverse-replace of key-value pairs.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/blah/textscrub.git
   ```
2. Navigate to the project directory:
   ```bash
   cd textscrub
   ```
3. Run the application:
   ```bash
   ./textscrub.py
   ```

## Usage
1. **Launch the Application**: Run the script to start the editor.
2. **Set Up Bulk Replace**: Open the bulk replace dialog from the "Search" menu and add key-value pairs for replacement.
3. **Apply Theme**: Choose a theme from the "Edit" menu to customize the appearance (woah!).
4. **Perform Bulk Replace**: Use the `Ctrl+R` hotkey or select "ReplaceBulk" from the "Edit" menu to replace keywords and highlight changes.
5. **Shake the AI Sprinkles**: paste the redacted text into whichever probabilistec generative text munging turbo encabulator of your choice and appreciate that your sensitive data hasn't spilled into yet another crevasse of the internet.

## Preferences
The application saves preferences, including the selected theme and bulk replace pairs, to a JSON file located at `~/.config/ai-editor/ai-editor-prefs.json`. These preferences are loaded automatically when the application starts. They save when you close the dialog or choose File -> Exit from the menu.

## Contributing
Contributions are welcome, well, actually just fork it. I have enough merge conflicts at my day job.

## License
This project is licensed under the GNU GPLv3 License. See the LICENSE file for details.
