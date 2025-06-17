import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkhtmlview import HTMLLabel
import markdown
import pdfkit
import ttkbootstrap as tb
from ttkbootstrap.tooltip import ToolTip

class MarkdownEditor:
    def __init__(self, root):
        self.root = root
        self.style = tb.Style("flatly")
        self.root.title("Markdown Editor")
        self.root.geometry("1000x600")
        self.current_theme = "flatly"
        self.current_file = None

        self.icons = {
            "bold": tk.PhotoImage(file="assets/bold.png"),
            "italic": tk.PhotoImage(file="assets/italic.png"),
            "heading": tk.PhotoImage(file="assets/heading.png"),
            "subheading": tk.PhotoImage(file="assets/sub-heading.png"),
            "new": tk.PhotoImage(file="assets/new.png"),
            "open": tk.PhotoImage(file="assets/open.png"),
            "save": tk.PhotoImage(file="assets/save.png"),
            "html": tk.PhotoImage(file="assets/html.png"),
            "pdf": tk.PhotoImage(file="assets/pdf.png"),
            # "theme": tk.PhotoImage(file="assets/theme.png"),
        }

        self.create_toolbar()

        self.pane = tk.PanedWindow(self.root, sashrelief=tk.RAISED, sashwidth=4)
        self.pane.pack(fill=tk.BOTH, expand=1)

        # Sidebar for file browsing
        self.sidebar = tb.Frame(self.pane, width=200, bootstyle="secondary")
        self.sidebar.pack_propagate(False)
        self.tree = tb.Treeview(self.sidebar, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.load_selected_file)
        self.populate_sidebar()
        self.pane.add(self.sidebar)

        # Markdown editor text area
        self.text_area = tk.Text(self.root, wrap='word', font=("Segoe UI", 10), undo=True)
        self.pane.add(self.text_area)

        self.text_area.tag_configure("divider", background="#f0f0f0", foreground="gray", font=("Segoe UI", 8, "italic"))

        # Markdown preview
        self.preview = HTMLLabel(self.root, html="", background="white")
        self.pane.add(self.preview)

        self.text_area.bind("<<Modified>>", self.update_preview)

    def create_toolbar(self):
        self.toolbar = tb.Frame(self.root, padding=5)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.add_toolbar_button("New", self.new_file, self.icons["new"], "New File")
        self.add_toolbar_button("Open", self.open_file, self.icons["open"], "Open File")
        self.add_toolbar_button("Save", self.save_file, self.icons["save"], "Save File")
        self.add_toolbar_button("Bold", lambda: self.insert_markdown("**", "**"), self.icons["bold"], "**Bold**")
        self.add_toolbar_button("Italic", lambda: self.insert_markdown("*", "*"), self.icons["italic"], "*Italic*")
        self.add_toolbar_button("Heading", lambda: self.insert_markdown("# ", ""), self.icons["heading"], "# Heading")
        self.add_toolbar_button("Subheading", lambda: self.insert_markdown("## ", ""), self.icons["subheading"], "## Subheading")
        self.add_toolbar_button("HTML", self.export_html, self.icons["html"], "Export as HTML")
        self.add_toolbar_button("PDF", self.export_pdf, self.icons["pdf"], "Export as PDF")
        # self.add_toolbar_button("Theme", self.toggle_theme, self.icons["theme"], "Toggle Light/Dark Theme")

    def add_toolbar_button(self, text, command, image=None, tooltip=None):
        btn = tb.Button(self.toolbar, image=image, command=command, bootstyle="secondary", width=30)
        btn.pack(side=tk.LEFT, padx=3)
        if tooltip:
            ToolTip(btn, text=tooltip)

    def insert_markdown(self, prefix, suffix):
        try:
            start = self.text_area.index("sel.first")
            end = self.text_area.index("sel.last")
            selected_text = self.text_area.get(start, end)
            self.text_area.delete(start, end)
            self.text_area.insert(start, f"{prefix}{selected_text}{suffix}")
        except tk.TclError:
            self.text_area.insert(tk.INSERT, f"{prefix}{suffix}")
        self.update_preview()

    def new_file(self):
        filename = "README.md"
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("")
        else:
            messagebox.showwarning("File Exists", f"{filename} already exists.")
            return
        self.text_area.delete("1.0", tk.END)
        self.current_file = filename
        self.root.title(f"Markdown Editor - {filename}")
        messagebox.showinfo("New File", f"Created {filename}")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Markdown files", "*.md")])
        if path:
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
            self.update_preview()
            self.current_file = path
            self.root.title(f"Markdown Editor - {os.path.basename(path)}")

    def save_file(self):
        if self.current_file:
            with open(self.current_file, 'w', encoding='utf-8') as file:
                file.write(self.text_area.get("1.0", tk.END))
            messagebox.showinfo("Saved", f"File saved: {self.current_file}")
        else:
            messagebox.showwarning("Warning", "No file open")

    def export_html(self):
        if self.current_file:
            html = markdown.markdown(self.text_area.get("1.0", tk.END))
            html_file = self.current_file.replace(".md", ".html")
            with open(html_file, "w", encoding="utf-8") as file:
                file.write(html)
            messagebox.showinfo("Exported", f"HTML saved to {html_file}")

    def export_pdf(self):
        if self.current_file:
            html = markdown.markdown(self.text_area.get("1.0", tk.END))
            pdf_file = self.current_file.replace(".md", ".pdf")
            try:
                pdfkit.from_string(html, pdf_file)
                messagebox.showinfo("Exported", f"PDF saved to {pdf_file}")
            except Exception as e:
                messagebox.showerror("PDF Export Error", str(e))

    def update_preview(self, event=None):
        self.text_area.edit_modified(False)
        self.text_area.tag_remove("divider", "1.0", tk.END)  # Clear existing tags

        md_text = self.text_area.get("1.0", tk.END)
        lines = md_text.splitlines()

        for idx, line in enumerate(lines):
            if line.strip() == "---":
                tag_start = f"{idx+1}.0"
                tag_end = f"{idx+1}.end"
                self.text_area.tag_add("divider", tag_start, tag_end)

        html = markdown.markdown(md_text)
        html = f"""
        <div style='
            font-size: 10px;
            font-family: Segoe UI, sans-serif;
            color: #333;
            line-height: 1.6;
            padding: 8px;
        '>
        {html}
        </div>
        """

        self.preview.set_html(html)


    def toggle_theme(self):
        new_theme = "darkly" if self.current_theme == "flatly" else "flatly"
        self.style.theme_use(new_theme)
        self.current_theme = new_theme

    def populate_sidebar(self, directory="."):
        self.tree.delete(*self.tree.get_children())
        for file in os.listdir(directory):
            if file.endswith(".md"):
                abspath = os.path.abspath(os.path.join(directory, file))
                self.tree.insert("", "end", text=file, values=(abspath,))

    def load_selected_file(self, event):
        item = self.tree.focus()
        if not item:
            return
        file_path = self.tree.item(item)["values"][0]
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
            self.update_preview()
            self.current_file = file_path
            self.root.title(f"Markdown Editor - {os.path.basename(file_path)}")

if __name__ == "__main__":
    app = MarkdownEditor(tb.Window(themename="flatly"))
    app.root.mainloop()
