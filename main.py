import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, filedialog
import json
import os

class BibleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bible App")

        # Initialize UI components
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
        self.text_area.pack(padx=10, pady=10)

        self.text_area.bind("<Button-3>", self.show_context_menu)

        self.menu = tk.Menu(root)
        root.config(menu=self.menu)
        self.bookmark_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="Bookmarks", menu=self.bookmark_menu)
        self.version_menu = tk.Menu(self.menu)
        self.menu.add_cascade(label="Version", menu=self.version_menu)
        self.menu.add_command(label="Search", command=self.search_text)
        self.menu.add_command(label="Save Bookmarks", command=self.save_bookmarks)
        self.menu.add_command(label="Load Bookmarks", command=self.load_bookmarks)

        # Context menu for bookmarks
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="View Bookmark", command=self.view_bookmark)
        self.context_menu.add_command(label="Edit Bookmark", command=self.edit_bookmark)
        self.context_menu.add_command(label="Remove Bookmark", command=self.remove_bookmark)

        # Buttons for bookmarks
        self.add_bookmark_button = tk.Button(root, text="Add Bookmark", command=self.add_bookmark)
        self.add_bookmark_button.pack(pady=5)

        self.go_to_bookmark_button = tk.Button(root, text="Go to Bookmark", command=self.go_to_bookmark)
        self.go_to_bookmark_button.pack(pady=5)

        self.search_entry = tk.Entry(root, width=50)
        self.search_entry.pack(pady=5)
        self.search_button = tk.Button(root, text="Search", command=self.search_text)
        self.search_button.pack(pady=5)

        self.bookmarks = {}
        self.last_position = {"line": None, "column": None}
        self.current_file = None
        self.current_bookmark_name = None

        self.load_version_menu()
        self.load_bookmarks()

    def load_version_menu(self):
        """Add menu items to select different Bible versions."""
        self.version_menu.add_command(label="Load Bible Version", command=self.load_version)

    def load_version(self):
        """Open a file dialog to select a Bible version."""
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.load_bible(file_path)

    def load_bible(self, file_path):
        """Load the selected Bible version."""
        self.current_file = file_path
        try:
            with open(file_path, "r") as file:
                content = file.read()
                self.text_area.delete(1.0, tk.END)  # Clear existing content
                self.text_area.insert(tk.END, content)
        except FileNotFoundError:
            self.text_area.insert(tk.END, "Bible file not found.")

        # Restore last position
        if self.last_position["line"] and self.current_file == self.last_position["file"]:
            self.go_to_position(self.last_position["line"], self.last_position["column"])

        # Highlight bookmarked lines
        self.highlight_bookmarked_lines()

    def save_bookmarks(self):
        """Save bookmarks and last position to a file."""
        with open("bookmarks.json", "w") as file:
            json.dump({
                "bookmarks": self.bookmarks,
                "last_position": self.last_position,
                "current_file": self.current_file
            }, file)

    def load_bookmarks(self):
        """Load bookmarks and last position from a file."""
        if os.path.exists("bookmarks.json"):
            with open("bookmarks.json", "r") as file:
                data = json.load(file)
                self.bookmarks = data.get("bookmarks", {})
                self.last_position = data.get("last_position", {"line": None, "column": None})
                self.current_file = data.get("current_file", None)
                self.update_bookmark_menu()
                self.highlight_bookmarked_lines()  # Ensure bookmarks are highlighted

    def update_bookmark_menu(self):
        """Update the bookmark menu."""
        self.bookmark_menu.delete(0, tk.END)
        for name in self.bookmarks:
            self.bookmark_menu.add_command(label=name, command=lambda name=name: self.go_to_bookmark(name))

    def add_bookmark(self):
        """Add a bookmark at a specified text position."""
        if not self.current_file:
            messagebox.showerror("Error", "No Bible version loaded.")
            return

        # Prompt user to enter bookmark details
        name = simpledialog.askstring("Bookmark Name", "Enter bookmark name:")
        if not name:
            return

        line = simpledialog.askstring("Bookmark Line", "Enter the line number for the bookmark (e.g., 5):")
        if not line or not line.isdigit():
            messagebox.showerror("Error", "Invalid line number.")
            return

        description = simpledialog.askstring("Bookmark Description", "Enter bookmark description:")

        # Convert line to string
        line = str(int(line))  # Ensure line number is an integer

        # Save bookmark
        if name in self.bookmarks:
            messagebox.showinfo("Bookmark Exists", "Bookmark with this name already exists.")
            return
        self.bookmarks[name] = {"line": line, "description": description}
        self.update_bookmark_menu()
        self.highlight_bookmarked_lines()  # Update highlighting after adding a bookmark
        self.save_bookmarks()

    def view_bookmark(self):
        """View the selected bookmark's details."""
        if self.current_bookmark_name and self.current_bookmark_name in self.bookmarks:
            bookmark = self.bookmarks[self.current_bookmark_name]
            messagebox.showinfo("Bookmark Details", f"Name: {self.current_bookmark_name}\nLine: {bookmark['line']}\nDescription: {bookmark['description']}")
        else:
            messagebox.showerror("Error", "No bookmark selected.")

    def edit_bookmark(self):
        """Edit the selected bookmark."""
        if self.current_bookmark_name and self.current_bookmark_name in self.bookmarks:
            bookmark = self.bookmarks[self.current_bookmark_name]
            new_description = simpledialog.askstring("Edit Bookmark", f"Edit description for bookmark '{self.current_bookmark_name}':", initialvalue=bookmark['description'])
            if new_description is not None:
                self.bookmarks[self.current_bookmark_name]['description'] = new_description
                self.save_bookmarks()
        else:
            messagebox.showerror("Error", "No bookmark selected.")

    def remove_bookmark(self):
        """Remove the selected bookmark."""
        if self.current_bookmark_name and self.current_bookmark_name in self.bookmarks:
            del self.bookmarks[self.current_bookmark_name]
            self.update_bookmark_menu()
            self.highlight_bookmarked_lines()  # Update highlighting after removing a bookmark
            self.save_bookmarks()
        else:
            messagebox.showerror("Error", "No bookmark selected.")

    def go_to_bookmark(self, name=None):
        """Go to a bookmarked position."""
        if name is None:
            name = simpledialog.askstring("Go to Bookmark", "Enter bookmark name:")
        if name in self.bookmarks:
            line = self.bookmarks[name]["line"]
            self.go_to_position(line, 0)
        else:
            messagebox.showerror("Error", "Bookmark not found.")

    def go_to_position(self, line, column):
        """Move cursor to a specific line and column and scroll the view."""
        self.text_area.mark_set(tk.INSERT, f"{line}.{column}")
        self.text_area.see(tk.INSERT)
        self.last_position = {"line": line, "column": column, "file": self.current_file}
        self.save_bookmarks()

    def highlight_bookmarked_lines(self):
        """Highlight all lines with bookmarks."""
        self.text_area.tag_delete("bookmark")  # Remove existing highlights
        for name, details in self.bookmarks.items():
            line = details["line"]
            self.text_area.tag_add("bookmark", f"{line}.0", f"{line}.end")
        self.text_area.tag_configure("bookmark", background="lightblue")

    def search_text(self):
        """Search for text in the Bible."""
        search_term = self.search_entry.get()
        if not search_term:
            messagebox.showwarning("Search", "Please enter a search term.")
            return

        content = self.text_area.get(1.0, tk.END)
        start_index = content.find(search_term)
        if start_index == -1:
            messagebox.showinfo("Search", "Text not found.")
            return

        # Highlight search term
        self.text_area.tag_delete("highlight")
        start_index = "1.0"
        while True:
            start_index = self.text_area.search(search_term, start_index, stopindex=tk.END)
            if not start_index:
                break
            end_index = f"{start_index}+{len(search_term)}c"
            self.text_area.tag_add("highlight", start_index, end_index)
            self.text_area.tag_configure("highlight", background="yellow")
            start_index = end_index

    def show_context_menu(self, event):
        """Show context menu when right-clicking in the text area."""
        index = self.text_area.index("@%s,%s" % (event.x, event.y))
        line = index.split('.')[0]
        if line in [str(bookmark["line"]) for bookmark in self.bookmarks.values()]:
            self.current_bookmark_name = self.get_bookmark_name_by_line(line)
            self.context_menu.post(event.x_root, event.y_root)
        else:
            self.current_bookmark_name = None

    def get_bookmark_name_by_line(self, line):
        """Get bookmark name by line number."""
        for name, details in self.bookmarks.items():
            if details["line"] == line:
                return name
        return None

    def on_closing(self):
        """Save bookmarks and last position on closing."""
        self.save_bookmarks()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BibleApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Save bookmarks and last position on closing
    root.mainloop()
