from casparser.parsers.pdfminer import cas_pdf_to_text
from casparser.process.cas_detailed import process_detailed_text
with open("pwd.txt") as file_in:
    lines = []
    for line in file_in:
        lines.append(line)

pwd = lines[0]
raw = cas_pdf_to_text("test.pdf", pwd)
txt = "\u2029".join(raw.lines)

print(process_detailed_text(txt))