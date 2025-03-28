import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import keyboard
import threading
import time

class TextExpander:
    def __init__(self, root):
        self.root = root
        self.root.title("TextExpander")
        self.root.geometry("700x500")

        #  App icon and theme setup
        # if os.path.exists('icon.ico'):
        #     self.root.iconbitmap("icon.ico")
        self.root.iconbitmap("icon.ico") if os.path.exists("icon.ico") else None
        self.setup_ui_style()

        self.macros_file = "text_macros.json"
        self.macros = self.load_macros()

        # Creating  UI elements
        self.create_ui()

        # Start keyboard listener in a separate thread
        self.listener_active = True
        self.listener_thread = threading.Thread(target=self.keyboard_listener)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def setup_ui_style(self):
        # Configure the style
        style = ttk.Style()
        style.theme_use("clam")  # Look through themes to choose a cool one.

        # Configure colors and styles
        style.configure("TFrame",background="F5F5F5")
        style.configure("TButton", background="#4CAF50", foreground="black",
                        borderwidth=1, focusthickness=3, focuscolor='none')
        style.map('TButton', background=[('active', '#45a049')])
        style.configure("TLabel", background="#f5f5f5", font=('Arial', 10))
        style.configure("TEntry", font=('Arial', 10))
        style.configure("Heading.TLabel", font=('Arial', 12, 'bold'))

    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel = Macro list
        list_frame = ttk.Frame(main_frame, padding="5")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Title for macro list
        ttk.Label(list_frame, text="Your Text Macros", style="Heading.TLabel").pack(pady=5, anchor=tk.W)

        # Search box
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="Search").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_macro_list)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # List of macros with scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.macro_listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set, font=('Arial', 10),
                                        selectbackground="#4CAF50", selectforeground="#FFFFFF")
        self.macro_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.macro_listbox.yview)

        self.macro_listbox.bind('<<ListboxSelect>>', self.on_macro_select)

        # Buttons for list management
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="New", command=self.new_macro).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_macro).pack(side=tk.LEFT, padx=5)

        # Right panel - Macro editor
        editor_frame = ttk.Frame(main_frame, padding="5")
        editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Title for macro editor
        ttk.Label(editor_frame, text="Edit Macro", style="Heading.TLabel").pack(pady=5, anchor=tk.W)


        #Trigger input
        trigger_frame = ttk.Frame(editor_frame)
        trigger_frame.pack(fill=tk.X, pady=5)
        ttk.Label(trigger_frame, text="Trigger:").pack(side=tk.LEFT, padx=5)
        self.trigger_var = tk.StringVar()
        ttk.Entry(trigger_frame, textvariable=self.trigger_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Expanded text
        ttk.Label(editor_frame, text="Expanded Text:").pack(anchor=tk.W, pady=5, padx=5)
        self.text_editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.WORD, font=('Arial', 10), height=10)
        self.text_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Save button
        ttk.Button(editor_frame, text="Save Macro", command=self.save_current_macro).pack(pady=10)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief= tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Populate the listbox
        self.update_macro_list()


    def update_macro_list(self, *args):
        """Update the listbox with macro triggers, optionally filtered by search"""
        self.macro_listbox.delete(0, tk.END)
        search_text = self.search_var.get().lower()

        for trigger in sorted(self.macros.keys()):
            if search_text in trigger.lower():
                self.macro_listbox.insert(tk.END, trigger)

    def on_macro_select(self, event):
        """Handle selection of a macro in the listbox"""
        selection = self.macro_listbox.curselection()
        if selection:
            trigger = self.macro_listbox.get(selection[0])
            self.trigger_var.set(trigger)
            self.text_editor.delete(1.0, tk.END)
            self.text_editor.insert(tk.END, self.macros[trigger])
            self.status_var.set(f"Editing: {trigger}")

    def new_macro(self):
        """Creating a new macro"""
        self.trigger_var.set("")
        self.text_editor.delete(1.0, tk.END)
        self.status_var.set("Creating new macro")

    def save_current_macro(self):
        """Save the current macro from the editor"""
        trigger = self.trigger_var.get().strip()
        expanded_text = self.text_editor.get(1.0, tk.END).strip()

        # Error Handling for empty trigger and macro msg entries
        if not trigger:
            messagebox.showerror("Error", "Please enter a trigger text")
            return

        if not expanded_text:
            messagebox.showerror("Error", "Please enter expanded text msg")
            return

        old_trigger = None
        selection = self.macro_listbox.curselection()
        if selection:
            old_trigger = self.macro_listbox.get(selection[0])

        # If editing an existing trigger but changing the key
        if old_trigger and old_trigger != trigger:
            del self.macros[old_trigger]

        # Save the new/updated macro
        self.macros[trigger] = expanded_text
        self.save_macros()
        self.update_macro_list()

        # Select the new/edited item
        items = list(self.macro_listbox.get(0, tk.END))
        if trigger in items:
            index = items.index(trigger)
            self.macro_listbox.selection_clear(0, tk.END)
            self.macro_listbox.selection_set(index)
            self.macro_listbox.see(index)

        self.status_var.set(f"Saved: {trigger}")

    def delete_macro(self):
        """Delete the selected macro"""
        selection = self.macro_listbox.curselection()
        if selection:
            trigger = self.macro_listbox.get(selection[0])
            confirm = messagebox.askyesno("Confirm Delete",
                                          f"Are you sure you want to delete the macro: {trigger}?")
            if confirm:
                del self.macros[trigger]
                self.save_macro()
                self.update_macros_list()
                self.new_macro()
                self.status_var.set(f"Deleted: {trigger}")
            else:
                messagebox.showinfo("Info", "Please select a macro to delete")

    def load_macros(self):
        """Load macros from the JSON file"""
        if os.path.exists(self.macros_file):
            try:
                with open(self.macros_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_macros(self):
        """Save macros to JSON file"""
        with open(self.macros_file, 'w') as f:
            json.dump(self.macros, f, indent=2)

    def keyboard_listener(self):
        """Listen for key commands and expand them"""
        # Track what user has typed recently
        buffer = ""
        max_buffer_size = 50 # Maximum number of recent characters to track

        def callback(event):
            nonlocal buffer

            # For printable characters, add to buffer
            if hasattr(event, 'name') and len(event.name) == 1:
                buffer += event.name
            elif event.name == 'space':
                buffer += ' '
            elif event.name in ['enter', 'tab']:
                buffer += ' '  # Add a space as a separator for these keys

            # Keep buffer at max size
            if len(buffer) > max_buffer_size:
                buffer = buffer[:max_buffer_size]

            # Check if any macro trigger is in the buffer
            for trigger in self.macros:
                if trigger and buffer.endswith(trigger):
                    # Release all keys to avoid interference
                    keyboard.release('shift')
                    keyboard.release('ctrl')
                    keyboard.release('alt')

                    # Delete the trigger text
                    for _ in range(len(trigger)):
                        keyboard.send('backspace')

                    # Type the expanded text
                    keyboard.write(self.macros[trigger])

                    # Update the buffer
                    buffer = ""

                    # Update status
                    # We can't directly update the UI from another thread
                    # So we use after() to schedule the update on the main thread
                    self.root.after(0, lambda: self.status_var.set(f"Expanded: {trigger}"))

                    # Break to avoid checking other triggers
                    break

        # Hook the callback to all key presses
        keyboard.on_release(callback=callback)

        # Keep the thread alive until listener_active is False
        while self.listener_active:
            time.sleep(0.1)  # Sleep to reduce CPU

        # Unhook the callback when shutting down
        keyboard.unhook_all()


    def on_closing(self):
        """Handle window closing"""
        self.listener_active = False
        self.listener_thread.join(1.0) # Wait up to 1 second for thread to finish
        self.save_macros()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TextExpander(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

