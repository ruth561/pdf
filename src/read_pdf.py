from obj import *    

if len(sys.argv) < 2: # python3 はargvに含まれないらしい
    print("Usage: $ python3 make_pdf.py [pdf file name]\n")
    sys.exit()

target = sys.argv[1]
with open(target, "rb") as binf:
    pdf_data = binf.read()
    pdf = PDF(pdf_data)
