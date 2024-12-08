import os
import zipfile

import py7zr
import rarfile


class UnCompress:  # 将所有函数封装成一个类，方便调用函数
    def __init__(self, file_path, output_path):
        self.file_path = (
            file_path  # 输入文件路径（这里不需要更改，最后几行代码会输入文件路径）
        )
        self.output_path = (
            output_path  # 输出文件路径（这里不需要更改，最后几行代码会输入文件路径）
        )

    # zip解压缩
    def unzip_file(self):
        try:
            zf = zipfile.ZipFile(file=self.file_path)  # zipfile 读取压缩文件对象
            zf.extractall(self.output_path)  # 压缩文件内全部文件解压到输入的文件夹中
            zf.close()  # 关闭 zipfile 对象
            return True  # 压缩完后返回的值（如果是批量解压文件的话，就不会返回）
        except Exception:
            return False  # 压缩报错后返回的值，如果返回false,则需要修改其他代码，可私信作者

    # 7z解压缩
    def un7z_file(self):
        try:
            py = py7zr.SevenZipFile(file=self.file_path)  # py7zr 读取压缩文件对象
            py.extractall(self.output_path)  # 压缩文件内全部文件解压到输入的文件夹中
            py.close()  # 关闭 py7zr 对象
            return True
        except Exception:
            return False

    # RAR解压缩
    def unrar_file(self):
        try:
            zf = rarfile.RarFile(file=self.file_path)  # rarfile 读取压缩文件对象
            zf.extractall(self.output_path)  # 压缩文件内全部文件解压到输入的文件夹中
            zf.close()  # 关闭 rarfile 对象
            return True
        except Exception:
            return False

    def run(
            self,
    ):  # 封装一个函数，判断读取的文件是属于什么类型的压缩文件，然后调用相应的文件
        file_state = False
        if not os.path.exists(self.file_path):
            return file_state
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        # zip解压缩
        if zipfile.is_zipfile(self.file_path):
            file_state = self.unzip_file()
        # 7z解压缩
        if py7zr.is_7zfile(self.file_path):
            file_state = self.un7z_file()

        # RAR解压缩
        if rarfile.is_rarfile(self.file_path):
            file_state = self.unrar_file()
        return file_state

    #  循环遍历文件夹


# 解压第一层文件夹
# w = UnCompress("DataA.rar", "DataA")  # 此处为你们要改的路径，前者为你需要的压缩文件夹路径，后者为你解压过后的文件保存的地址
# w.run()
# 解压第二层文件夹
path = r"D:\Dataset\RGBT2019"  # 此处为你刚刚解压文件夹过后保存的地址，也是你需要继续解压的多个文件夹
filenames = os.listdir(path)
for filename in filenames:
    filepath = os.path.join(path, filename)
    newfilepath = filepath.split(".", 1)[0]  # 以压缩文件的前缀为文件名
    if os.path.isdir(newfilepath):  # 根据获取的压缩文件的文件名建立相应的文件夹
        pass
    else:
        os.mkdir(newfilepath)
    w = UnCompress(filepath, newfilepath)
    w.run()
