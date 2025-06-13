import pickle
import os

BLOCK_SIZE = 64
BLOCK_COUNT = 1024
DISK_FILE = 'disk.data'


class Block:
    def __init__(self):
        self.data = ""


class File:
    def __init__(self, name):
        self.name = name
        self.length = 0
        self.blocks = []

    def write(self, data, blocks, bitmap):
        # 先释放旧数据块
        for i in self.blocks:
            bitmap[i] = 0
        self.blocks.clear()

        while data:
            for i in range(len(bitmap)):
                if bitmap[i] == 0:
                    bitmap[i] = 1
                    blocks[i].data = data[:BLOCK_SIZE]
                    self.blocks.append(i)
                    data = data[BLOCK_SIZE:]
                    break
            else:
                raise Exception("磁盘已满")

        self.length = sum(len(blocks[i].data) for i in self.blocks)

    def read(self, blocks):
        return ''.join(blocks[i].data for i in self.blocks)


class Directory:
    def __init__(self, name):
        self.name = name
        self.entries = {}  # name -> File or Directory


class FileSystem:
    def __init__(self):
        self.blocks = [Block() for _ in range(BLOCK_COUNT)]
        self.bitmap = [0] * BLOCK_COUNT
        self.root = Directory('/')
        self.current = self.root
        self.path = ['/']

    def format(self):
        self.__init__()

    def get_current_path(self):
        return '/' if self.current is self.root else '/' + '/'.join(self.path[1:])

    def create_file(self, name):
        if name in self.current.entries:
            raise Exception("文件已存在")
        self.current.entries[name] = File(name)

    def delete_file(self, name):
        if name not in self.current.entries or not isinstance(self.current.entries[name], File):
            raise Exception("文件不存在")
        file = self.current.entries.pop(name)
        for i in file.blocks:
            self.bitmap[i] = 0

    def write_file(self, name, data):
        if name not in self.current.entries or not isinstance(self.current.entries[name], File):
            raise Exception("文件不存在")
        self.current.entries[name].write(data, self.blocks, self.bitmap)

    def read_file(self, name):
        if name not in self.current.entries or not isinstance(self.current.entries[name], File):
            raise Exception("文件不存在")
        return self.current.entries[name].read(self.blocks)

    def make_dir(self, name):
        if name in self.current.entries:
            raise Exception("目录已存在")
        self.current.entries[name] = Directory(name)

    def delete_dir(self, name):
        if name not in self.current.entries or not isinstance(self.current.entries[name], Directory):
            raise Exception("目录不存在")
        if self.current.entries[name].entries:
            raise Exception("目录非空")
        del self.current.entries[name]

    def change_dir(self, name):
        if name == "..":
            if len(self.path) > 1:
                self.path.pop()
                self.current = self.root
                for p in self.path[1:]:
                    self.current = self.current.entries[p]
        elif name in self.current.entries and isinstance(self.current.entries[name], Directory):
            self.current = self.current.entries[name]
            self.path.append(name)
        else:
            raise Exception("目录不存在")

    def list_dir(self):
        return list(self.current.entries.keys())

    def get_file_info(self, name):
        """
        返回文件大小和占用块数，供GUI显示
        """
        if name not in self.current.entries:
            raise Exception("文件不存在")
        entry = self.current.entries[name]
        if isinstance(entry, File):
            size = entry.length
            blocks = len(entry.blocks)
            # 物理地址：第一个块号，没有块则为 None
            physical_addr = entry.blocks[0] if entry.blocks else None
            return size, blocks, physical_addr
        elif isinstance(entry, Directory):
            # 目录没有数据块，物理地址显示 None，长度为目录项数
            size = len(entry.entries)
            blocks = 0
            physical_addr = None
            return size, blocks, physical_addr
        return None, None, None

    def save(self):
        with open(DISK_FILE, 'wb') as f:
            pickle.dump((self.blocks, self.bitmap, self.root), f)

    def load(self):
        if os.path.exists(DISK_FILE):
            with open(DISK_FILE, 'rb') as f:
                self.blocks, self.bitmap, self.root = pickle.load(f)
            self.current = self.root
            self.path = ['/']
