import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from tkinter import ttk
from PIL import Image, ImageTk
from filesystem import FileSystem


class FileSystemGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("简易文件系统   2352835 夏弘泰")
        self.master.geometry("1000x600")
        self.master.configure(bg="#eaf6ff")
        self.fs = FileSystem()

        try:
            self.fs.load()
        except:
            self.fs.format()

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.folder_icon = ImageTk.PhotoImage(Image.open("folder.png").resize((16, 16)))
        self.file_icon = ImageTk.PhotoImage(Image.open("file.png").resize((16, 16)))

        self.default_font = ("Microsoft YaHei", 10)
        self.bold_font = ("Microsoft YaHei", 10, "bold")

        self.left = tk.Frame(master, bg="#eaf6ff", padx=10, pady=10)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.path_label = tk.Label(self.left, text=self.fs.get_current_path(),
                                   font=self.bold_font, bg="#eaf6ff", fg="#003366")
        self.path_label.pack(pady=(0, 10))

        style = ttk.Style()
        style.configure("Treeview.Heading", font=self.bold_font)
        style.configure("Treeview", font=self.default_font, rowheight=22)

        self.dir_tree = ttk.Treeview(self.left, show="tree headings", selectmode="browse", height=35,
                                     columns=("physical_addr", "length"))
        self.dir_tree.pack(fill=tk.BOTH, expand=True)
        self.dir_tree.heading("#0", text="名称")
        self.dir_tree.heading("physical_addr", text="物理地址")
        self.dir_tree.heading("length", text="长度/目录项数")
        self.dir_tree.column("#0", width=180, anchor="w")
        self.dir_tree.column("physical_addr", width=80, anchor="center")
        self.dir_tree.column("length", width=100, anchor="center")
        self.dir_tree.bind("<Double-1>", self.on_double_click)

        self.right = tk.Frame(master, bg="#ffffff", padx=10, pady=10)
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.command_frame_top = tk.Frame(self.right, bg="#ffffff")
        self.command_frame_top.pack(pady=3)
        self.command_frame_bottom = tk.Frame(self.right, bg="#ffffff")
        self.command_frame_bottom.pack(pady=3)

        self.output = scrolledtext.ScrolledText(self.right, wrap=tk.WORD, height=20,
                                                font=("Consolas", 10), bg="#fdfdfd", relief=tk.GROOVE,
                                                borderwidth=1)
        self.output.pack(fill=tk.BOTH, expand=True, pady=10)

        # 美化按钮样式（使用 ttk + style）
        self.ttk_style = ttk.Style()
        self.ttk_style.configure("RoundedButton.TButton",
                                 font=self.default_font,
                                 padding=6,
                                 relief="raised",
                                 background="#cce6ff",
                                 foreground="#003366")
        self.ttk_style.map("RoundedButton.TButton",
                           background=[("active", "#a3d1ff")],
                           relief=[("pressed", "sunken")])

        buttons = [
            ("刷新", self.update_dir_list),
            ("创建目录", self.create_dir),
            ("删除目录", self.delete_dir),
            ("进入目录", self.change_dir),
            ("返回上级", lambda: self.change_dir("..")),
            ("创建文件", self.create_file),
            ("修改文件", self.modify_file),
            ("删除文件", self.delete_file),
            ("读文件", self.read_file),
            ("格式化", self.format_disk),
        ]

        for i, (label, cmd) in enumerate(buttons):
            frame = self.command_frame_top if i < 5 else self.command_frame_bottom
            b = ttk.Button(frame, text=label, command=cmd, style="RoundedButton.TButton")
            b.pack(side=tk.LEFT, padx=5, pady=4)

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
                                     values=(str(physical_addr) if physical_addr is not None else "",
                                             str(size) if size is not None else ""),
                                     tags=("folder",))
            except:
                size, blocks, physical_addr = self.fs.get_file_info(item)
                self.dir_tree.insert("", "end", text=item,
                                     image=self.file_icon,
                                     values=(str(physical_addr) if physical_addr is not None else "",
                                             str(size) if size is not None else ""),
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

    def modify_file(self):
        name = self.get_selected()
        if not name:
            messagebox.showinfo("提示", "请先选择文件")
            return
        try:
            old_content = self.fs.read_file(name)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {e}")
            return

        editor = tk.Toplevel(self.master)
        editor.title(f"修改文件 - {name}")
        editor.geometry("500x400")

        text_area = scrolledtext.ScrolledText(editor, wrap=tk.WORD, font=("Consolas", 10))
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, old_content)

        def save_changes():
            new_content = text_area.get("1.0", tk.END).rstrip("\n")
            try:
                self.fs.write_file(name, new_content)
                self.output.insert(tk.END, f"修改文件 {name} 成功\n")
                editor.destroy()
                self.update_dir_list()
            except Exception as e:
                messagebox.showerror("错误", f"写入失败: {e}")

        save_btn = ttk.Button(editor, text="保存", command=save_changes, style="RoundedButton.TButton")
        save_btn.pack(pady=5)

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
