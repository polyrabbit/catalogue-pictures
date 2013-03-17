#!/usr/bin/env python
# coding:utf-8

from EXIF import process_file
from datetime import datetime
from shutil import copy2
import os
import sys
import glob
import re
import optparse
import distutils.file_util

img_patt = re.compile(r'\.(jpe?g|gif|bmp|png|tif)', re.I)

class ImgFile(object):
    def __init__(self, path):
        fd = open(path, 'rb')
        self.tags = process_file(fd, details=False)
        # print self.tags
        self.path = path

    @property
    def belongs_to(self):
        try:
        	return datetime.strptime(str(self.tags['EXIF DateTimeOriginal']), '%Y:%m:%d %H:%M:%S').strftime('%Y%m')
        except KeyError:
        	print 'cannot find DateTimeOriginal information in', self.path, 'use last-modified-time instead'
        	return datetime.fromtimestamp(os.stat(self.path).st_mtime).strftime('%Y%m')

    @property
    def camera(self):
        maker = self.tags.get('Image Make')
        model = self.tags.get('Image Model')
        if maker and model:
        	return '%s(%s)' % (maker, model)
        return str(maker or model or 'miscellaneous')
    tag = camera

class Directory(object):
    directories = {}

    def __init__(self, dname):
        # dname likes '201204', a relative path
		self.dname = dname
		self.files = []

    def add(self, fd):
        self.files.append(fd)

    def sync(self):
        tag_cnt = len(set((f.tag for f in self.files)))
        for f in self.files:
            dst_dir = self.dname
            if tag_cnt!=1:
                dst_dir = os.path.join(dst_dir, f.tag)
            Directory.ensure_exists(dst_dir)
            dst_name, copied = distutils.file_util.copy_file(f.path, dst_dir, update=1) 
            # copy2(f.path, dst_dir)
            if copied:
                print 'copied', f.path, 'to', dst_dir
            else:
                print dst_name, 'already exists'

    @staticmethod
    def ensure_exists(dir_path):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    @classmethod
    def iter(cls):
        return cls.directories.itervalues()

    @classmethod
    def get_instance(cls, dname):
		if dname in cls.directories:
			return cls.directories[dname]
		cls.directories[dname] = cls(dname)
		return cls.directories[dname]
		

def parse_arg():
    # os.path.dirname(__file__)  # python catalog_pics.py will return ''
    cwd = os.path.dirname(os.path.abspath(__file__))
    parser = optparse.OptionParser()
    parser.add_option('-s', '--src', dest='src_dir', default=cwd, metavar='source', help='directory where the disordered pictures lie in')
    parser.add_option('-t', '--target', dest='target', default=cwd, metavar='target', help='directory where to put the classified pictures')
    options = parser.parse_args()[0]
    return options.src_dir, options.target

def main():
    src_dir, dst_dir = parse_arg()

    while True: 
    	ans = raw_input('Catalog pictures from %s to %s, continue?[y/n]: ' % (src_dir, dst_dir))
    	if not ans: continue
    	if ans.lower() == 'y':
            break
        src_dir = raw_input('Source directory: ')
    	dst_dir = raw_input('Target directory: ')
        if src_dir and dst_dir:
            break

    is_img = lambda path: os.path.isfile(path) and img_patt.search(path)
    files = [os.path.join(src_dir, f) for f in os.listdir(src_dir)]

    for fpath in filter(is_img, files):
        fd = ImgFile(fpath)
        # print fd.belongs_to,
        dpath = os.path.join(dst_dir, fd.belongs_to)
        Directory.get_instance(dpath).add(fd)

    for new_dir in Directory.iter():
        new_dir.sync()

if __name__ == '__main__':
	main()