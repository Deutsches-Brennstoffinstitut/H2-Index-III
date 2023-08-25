import re
from collections import namedtuple
import string

def col2num(col):
    num = 0
    for c in col:
        if c in string.ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
    return num

def num2col(num):
    col = ''
    while num >= 0:
        num_sep = (num-1) % 26
        num = int((num-1) / 26)
        col = chr(ord('A') + num_sep) + col
        if num == 0:
            break

    return col


class ExcelCoordinate(namedtuple("ExcelCoordinate", "column, row")):
    @classmethod
    def from_string(cls, cell):
        cell = re.match('^([A-Za-z]+)(\d+)$', cell)
        if cell is None:
            raise ValueError("no cell value")
        return cls(col2num(cell.group(1)), int(cell.group(2)))

    def __str__(self):
        return '%s%d' %(col2num(self.column), self.row)


class ExcelArea(namedtuple("ExcelArea", "upper_left, lower_right")):
    @classmethod
    def from_string(cls, area):
        ul, lr = area.split(':')
        return cls(ExcelCoordinate.from_string(ul),ExcelCoordinate.from_string(lr))

    def __str__(self):
        return '%s:%s' %(self.ul, self.lr)