import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from tkinter import ttk
from PIL import Image, ImageTk
from filesystem import FileSystem  # 自定义文件系统模块


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

        # 加载图标（确保当前目录有 folder.png 和 file.png）
        self.folder_icon = ImageTk.PhotoImage(Image.open("folder.png").resize((16, 16)))
        self.file_icon = ImageTk.PhotoImage(Image.open("file.png").resize((16, 16)))

        # 左侧面板
        self.left = tk.Frame(master, bg="#e6f2ff", padx=10, pady=10)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.path_label = tk.Label(self.left, text=self.fs.get_current_path(),
                                   font=("Helvetica", 12, "bold"), bg="#e6f2ff", fg="#003366")
        self.path_label.pack(pady=(0, 10))

        # Treeview：多列+树形结构，第一列用于图标和名称
        self.dir_tree = ttk.Treeview(self.left, show="tree headings", selectmode="browse", height=35,
                                     columns=("physical_addr", "length"))
        self.dir_tree.pack(fill=tk.BOTH, expand=True)

        # 设置列标题
        self.dir_tree.heading("#0", text="名称")  # #0列用于显示图标和名称
        self.dir_tree.heading("physical_addr", text="物理地址")
        self.dir_tree.heading("length", text="长度/目录项数")

        # 设置列宽度
        self.dir_tree.column("#0", width=160, anchor="w")
        self.dir_tree.column("physical_addr", width=80, anchor="center")
        self.dir_tree.column("length", width=100, anchor="center")

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

        if len(self.fs.path) > 1:
            self.dir_tree.insert("", "end", text="...", image=self.folder_icon,
                                 values=("", ""), tags=("folder",))

        for item in self.fs.list_dir():
            try:
                self.fs.change_dir(item)
                self.fs.change_dir("..")
                size, blocks, physical_addr = self.fs.get_file_info(item)
                self.dir_tree.insert("", "end", text=item,
                                     image=self.folder_icon,
                                     values=(physical_addr if physical_addr is not None else "",
                                             size if size else ""),
                                     tags=("folder",))
            except:
                size, blocks, physical_addr = self.fs.get_file_info(item)
                self.dir_tree.insert("", "end", text=item,
                                     image=self.file_icon,
                                     values=(physical_addr if physical_addr is not None else "",
                                             size if size else ""),
                                     tags=("file",))

        self.path_label.config(text=self.fs.get_current_path())

    def on_double_click(self, event):
        item_id = self.dir_tree.selection()
        if not item_id:
            return
        selection = item_id[0]
        name = self.dir_tree.item(selection, "text")

        if name == "...":
            try:
                self.fs.change_dir("..")
                self.update_dir_list()
            except Exception as e:
                messagebox.showerror("错误", str(e))
        else:
            tags = self.dir_tree.item(selection, "tags")
            if "folder" in tags:
                try:
                    self.fs.change_dir(name)
                    self.update_dir_list()
                except Exception as e:
                    messagebox.showerror("错误", str(e))
            else:
                try:
                    content = self.fs.read_file(name)
                    self.output.insert(tk.END, f"[读取] {name}:\n{content}\n\n")
                except Exception as e:
                    messagebox.showerror("错误", str(e))

    def get_selected(self):
        item_id = self.dir_tree.selection()
        if not item_id:
            return None
        return self.dir_tree.item(item_id[0], "text")

    def create_dir(self):
        name = simpledialog.askstring("创建目录", "目录名称：")
        if name:
            try:
                self.fs.make_dir(name)
                self.update_dir_list()
                self.output.insert(tk.END, f"创建目录 {name} 成功\n")
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def delete_dir(self):
        name = self.get_selected()
        if not name:
            messagebox.showinfo("提示", "请先选择目录")
            return
        try:
            self.fs.delete_dir(name)
            self.update_dir_list()
            self.output.insert(tk.END, f"删除目录 {name} 成功\n")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def change_dir(self, name=None):
        if not name:
            name = self.get_selected()
        if not name:
            messagebox.showinfo("提示", "请先选择目录")
            return
        try:
            self.fs.change_dir(name)
            self.update_dir_list()
            self.output.insert(tk.END, f"进入目录 {name}\n")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def create_file(self):
        name = simpledialog.askstring("创建文件", "文件名称：")
        if name:
            try:
                self.fs.create_file(name)
                self.update_dir_list()
                self.output.insert(tk.END, f"创建文件 {name} 成功\n")
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def delete_file(self):
        name = self.get_selected()
        if not name:
            messagebox.showinfo("提示", "请先选择文件")
            return
        try:
            self.fs.delete_file(name)
            self.update_dir_list()
            self.output.insert(tk.END, f"删除文件 {name} 成功\n")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def write_file(self):
        name = self.get_selected()
        if not name:
            messagebox.showinfo("提示", "请先选择文件")
            return
        data = simpledialog.askstring("写文件", "写入内容：")
        if data is not None:
            try:
                self.fs.write_file(name, data)
                self.output.insert(tk.END, f"写入文件 {name} 成功\n")
            except Exception as e:
                messagebox.showerror("错误", str(e))
        self.update_dir_list()

    def read_file(self):
        name = self.get_selected()
        if not name:
            messagebox.showinfo("提示", "请先选择文件")
            return
        try:
            content = self.fs.read_file(name)
            self.output.insert(tk.END, f"[读取] {name}:\n{content}\n\n")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def format_disk(self):
        if messagebox.askyesno("格式化", "确定格式化？所有数据将丢失！"):
            self.fs.format()
            self.update_dir_list()
            self.output.insert(tk.END, "磁盘格式化成功\n")

    def save_disk(self):
        self.fs.save()
        self.output.insert(tk.END, "数据已保存\n")

    def on_closing(self):
        self.save_disk()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FileSystemGUI(root)
    root.mainloop()
