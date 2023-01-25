import sys
import re
from typing import Tuple, Dict
# Type of PDF object's reference
ObjRef = Tuple[int, int]

Delimiters = rb"[\(\)\<\>\[\]\{\}\/\%]"
WhiteSpaceChars = rb"[\x00\x09\x0a\x0c\x0d\x20]"

def error_func(message):
    print(f"[ ERROR ] {message}")
    exit()


class PdfObj:

    def __init__(self, raw_data: bytes):
        self.raw_data = raw_data
        self.raw_data = b"""6 0 obj
<< /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ] /ColorSpace << /Cs1 7 0 R
>> /Font << /G1 8 0 R >> /XObject << /Im1 9 0 R /HELLO#20WORLD#0aSEE#73YOU>> >>
endobj"""
        print(Delimiters)
        
        print(self.raw_data)
        self.num: int = None
        self.gen: int = None
        self.decode()
        print(self.num)
        print(self.gen)
        print(self.raw_data)
        pass

    def decode(self):
        # object number
        m_obj = re.search(rb"[0-9]+", self.raw_data)
        self.raw_data = self.raw_data[m_obj.end():]
        self.num = int(m_obj.group())
        # generation number
        m_obj = re.search(rb"[0-9]+", self.raw_data)
        self.raw_data = self.raw_data[m_obj.end():]
        self.gen = int(m_obj.group())

        self.raw_data = self.raw_data[self.raw_data.find(b"obj") + 3:]
        while True:
            m_obj = re.search(rb"(" + Delimiters + rb"|endobj)", self.raw_data)
            if m_obj == None:
                error_func("obj syntax error")

            self.raw_data = self.raw_data[m_obj.end():]
            print(m_obj.group())
            if m_obj.group() == b"endobj":
                break
            # elif m_obj.group() == b"<":

            elif m_obj.group() == b"/": # name object
                cnt, name = self.name_decode(self.raw_data)
                print("name:  ", name)
                self.raw_data = self.raw_data[cnt:]
                
        print("Finish decoding!!")

    # This function returns the size of name and name itself.
    def name_decode(self, data: bytes) -> Tuple[int, bytes]:
        res = b""
        i = 0
        while i < len(data):
            c = data[i:i+1]
            if c == b"#":
                res += bytes([int(data[i + 1: i + 3], 16)])
                i += 3
                continue
            elif re.match(WhiteSpaceChars, c): # end char
                break
            else:
                res += c
                i += 1
        return i, res



class TrailerDict:
    # text is expected to form b"<<...>>"" format 
    def __init__(self, pdf_data: bytes):
        self.size = None
        self.root: ObjRef = None
        self.info: ObjRef = None
        self.id   = None
        
        trailer_text = pdf_data[pdf_data.rfind(b"trailer"):]
        # <<から始まり、>>で終わる文字列の中で最短のものを返す。
        # python3では、.は「\n以外の文字全て」と決められているので、改行を含むように
        # 設定してあげる必要がある。
        trailer_dict_text = re.search(rb"\<\<(.|\n)*?\>\>", trailer_text).group()
        while match_obj := re.search(rb"/.*", trailer_dict_text):
            lst = list(match_obj.group().split())
            if lst[0] == b"/Size":
                self.size = int(lst[1])
            elif lst[0] == b"/Root":
                self.root = (int(lst[1]), int(lst[2]))
            elif lst[0] == b"/Info":
                self.info = (int(lst[1]), int(lst[2]))
            elif lst[0] == b"/ID":
                # TODO
                self.id = (lst[1], lst[2])
            else: 
                print(f"Error: trailer dict has invalid key {lst[0]}")
                exit()

            trailer_dict_text = trailer_dict_text[match_obj.end():]

        if self.size == None or self.root == None:
            print(f"Error: trailer dict is corropted.")
            exit()
        
class PDF:

    def __init__(self, raw_data: bytes):
        self.raw_data       = raw_data
        self.raw_data_len   = len(self.raw_data)
        self.version        = self.raw_data[5:8]
        self.trailer_dict   = TrailerDict(self.raw_data)
        print(self.trailer_dict.size)
        print(self.trailer_dict.root)
        print(self.trailer_dict.info)
        self.objs: Dict[ObjRef, PdfObj] = dict()
        self.xref_decode()
        # print(self.objs[self.trailer_dict.root].raw_data)
        # print(self.objs[self.trailer_dict.info].raw_data)

    def xref_decode(self):
        startxref_offset = self.raw_data.rfind(b"startxref")
        if startxref_offset == -1:
            print("[ Error ] Xref: This data is not complaiant with PDF format.")
            exit()
        xref_offset = int(re.search(rb"[0-9]+", self.raw_data[startxref_offset:]).group())
        
        self.start, self.end = map(int, re.search(rb"[0-9]+ [0-9]+", self.raw_data[xref_offset:]).group().split())
        xref_lines = re.findall(rb"[0-9]{10} [0-9]{5} [a-z]", self.raw_data[xref_offset:])
        for idx in range(self.start, self.end):
            line = xref_lines[idx - self.start]
            offset_s, gen_s, state = line.split()
            offset  = int(offset_s)
            gen     = int(gen_s)
            self.objs[(idx, gen)] = PdfObj(self.raw_data[offset:])

