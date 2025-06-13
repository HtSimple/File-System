import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from tkinter import ttk
from PIL import Image, ImageTk
from filesystem import FileSystem

class FileSystemGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("简易文件系统")
        self.master.configure(bg="#e6f2ff")
        self.fs = FileSystem()

        try:
            self.fs.load()
        except:
            self.fs.format()

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 图标
        self.folder_icon = ImageTk.PhotoImage(Image.open("folder.png").resize((16, 16)))
        self.file_icon = ImageTk.PhotoImage(Image.open("file.png").resize((16, 16)))

        # 左侧面板
        self.left = tk.Frame(master, bg="#e6f2ff", padx=10, pady=10)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.path_label = tk.Label(self.left, text=self.fs.get_current_path(),
                                   font=("Helvetica", 12, "bold"), bg="#e6f2ff", fg="#003366")
        self.path_label.pack(pady=(0, 10))

        self.dir_tree = ttk.Treeview(self.left, show="tree", selectmode="browse", height=35)
        self.dir_tree.pack(fill=tk.BOTH, expand=True)
        self.dir_tree.bind("<Double-1>", self.on_double_click)

        # 右侧面板
        self.right = tk.Frame(master, bg="#ffffff", padx=10, pady=10)
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.command_frame = tk.Frame(self.right, bg="#ffffff")
        self.command_frame.pack(pady=5)

        self.output = scrolledtext.ScrolledText(self.right, wrap=tk.WORD, height=20,
                                                font=("Consolas", 10), bg="#f9f9f9", relief=tk.FLAT)
        self.output.pack(fill=tk.BOTH, expand=True, pady=10)

        buttons = [
            ("刷新", self.update_dir_list),
            ("创建目录", self.create_dir),
            ("删除目录", self.delete_dir),
            ("进入目录", self.change_dir),
            ("返回上级", lambda: self.change_dir("..")),
            ("创建文件", self.create_file),
            ("删除文件", self.delete_file),
            ("写文件", self.write_file),
            ("读文件", self.read_file),
            ("格式化", self.format_disk),
            ("保存", self.save_disk)
        ]

        for (label, cmd) in buttons:
            b = tk.Button(self.command_frame, text=label, command=cmd,
                          font=("Helvetica", 10), bg="#cce6ff", fg="#003366",
                          relief=tk.RAISED, width=10)
            b.pack(side=tk.LEFT, padx=3, pady=2)

        self.update_dir_list()

    def update_dir_list(self):
        self.dir_tree.delete(*self.dir_tree.get_children())
        self.dir_tree.insert("", "end", text="...", iid="...", tags=("folder",))

        for item in self.fs.list_dir():
            try:
                self.fs.change_dir(item)
                self.fs.change_dir("..")
                self.dir_tree.insert("", "end", text=item, image=self.folder_icon, iid=item, tags=("folder",))
            except:
                self.dir_tree.insert("", "end", text=item, image=self.file_icon, iid=item, tags=("file",))

        self.path_label.config(text=self.fs.get_current_path())

    def on_double_click(self, event):
        item_id = self.dir_tree.selection()
        if not item_id:
            return
        selection = item_id[0]

        if selection == "...":
            try:
                self.fs.change_dir("..")
                self.update_dir_list()
            except Exception as e:
                messagebox.showerror("错误", str(e))
        elif "folder" in self.dir_tree.item(selection, "tags"):
            try:
                self.fs.change_dir(selection)
                self.update_dir_list()
            except Exception as e:
                messagebox.showerror("错误", str(e))
        else:
            try:
                content = self.fs.read_file(selection)
                self.output.insert(tk.END, f"[读取] {selection}:\n{content}\n\n")
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def get_selected(self):
        item_id = self.dir_tree.selection()
        return item_id[0] if item_id else None

    def create_file(self):
        name = simpledialog.askstring("创建文件", "文件名:")
        if name:
            try:
                self.fs.create_file(name)
                self.update_dir_list()
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def delete_file(self):
        name = self.get_selected()
        if not name or name == "..." or "folder" in self.dir_tree.item(name, "tags"):
            messagebox.showinfo("提示", "请选择一个文件进行删除。")
            return
        try:
            self.fs.delete_file(name)
            self.update_dir_list()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def write_file(self):
        name = self.get_selected()
        if not name or name == "..." or "folder" in self.dir_tree.item(name, "tags"):
            messagebox.showinfo("提示", "不能对目录写入。")
            return
        data = simpledialog.askstring("写入文件", "内容:")
        if data is not None:
            try:
                self.fs.write_file(name, data)
                self.output.insert(tk.END, f"[写入成功] {name}:\n{data}\n\n")
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def read_file(self):
        name = self.get_selected()
        if not name or name == "..." or "folder" in self.dir_tree.item(name, "tags"):
            messagebox.showinfo("提示", "不能读取目录。")
            return
        try:
            content = self.fs.read_file(name)
            self.output.insert(tk.END, f"[读取] {name}:\n{content}\n\n")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def create_dir(self):
        name = simpledialog.askstring("创建目录", "目录名:")
        if name:
            try:
                self.fs.make_dir(name)
                self.update_dir_list()
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def delete_dir(self):
        name = self.get_selected()
        if not name or name == "..." or "folder" not in self.dir_tree.item(name, "tags"):
            messagebox.showinfo("提示", "请选择一个目录进行删除。")
            return
        try:
            self.fs.delete_dir(name)
            self.update_dir_list()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def change_dir(self, name=None):
        if not name:
            name = self.get_selected()
            if not name or "folder" not in self.dir_tree.item(name, "tags"):
                messagebox.showinfo("提示", "请选择一个目录。")
                return
        try:
            self.fs.change_dir(name)
            self.update_dir_list()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def format_disk(self):
        if messagebox.askyesno("确认", "确认格式化？所有数据将丢失"):
            self.fs.format()
            self.update_dir_list()
            self.output.insert(tk.END, "[系统] 已格式化磁盘。\n\n")

    def save_disk(self):
        try:
            self.fs.save()
            messagebox.showinfo("提示", "已保存到磁盘")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def on_closing(self):
        try:
            self.fs.save()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1500x700")
    app = FileSystemGUI(root)
    root.mainloop()
