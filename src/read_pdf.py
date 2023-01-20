from obj import *    

def main():
    if len(sys.argv) < 2: # python3 はargvに含まれないらしい
        print("Usage: $ python3 make_pdf.py [incomplete pdf file name]\n")
        sys.exit()
    
    target = sys.argv[1]
    with open(target, "rb") as binf:
        data = binf.read()
        if (data[:7] != b"%PDF-1."):
            print("This file is not PDF.")
            sys.exit()
        pdf_ver = data[5:8]
        pdf_len = len(data)
        print(f"PDF version is {pdf_ver.decode()}")

        trailer_dict = TrailerDict(data)
        print(trailer_dict.size)
        print(trailer_dict.root)
        print(trailer_dict.info)


        startxref_offset = data.rfind(b"startxref")
        if startxref_offset == -1:
            print("This file is not complaiant with PDF format.")
            sys.exit()
        xref_offset = int(re.search(rb"[0-9]+", data[startxref_offset:]).group())
        
        xref_start , xref_end = map(int, re.search(rb"[0-9]+ [0-9]+", data[xref_offset:]).group().split())
        print(f"xref is from {xref_start} to {xref_end}")

        # xrefs[i] is xref data about the i-th object
        xrefs: list[Xref] = [None for _ in range(xref_end)]
        xref_idx = xref_start
        for line in re.findall(rb"[0-9]{10} [0-9]{5} [a-z]", data[xref_offset:]):
            offset_s, index_s, state = line.split()
            offset = int(offset_s)
            index = int(index_s)
            xrefs[xref_idx] = Xref(offset, index, state)
            xref_idx += 1
        
        print(data[xrefs[1].offset:xrefs[1].offset+30])


            
        


if __name__ == "__main__":
    main()

