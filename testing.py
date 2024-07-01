from casparser.parsers.pdfminer import cas_pdf_to_text
from casparser.process.cas_detailed import parse_transaction, get_transaction_type, process_detailed_text
with open("pwd.txt") as file_in:
    lines = []
    for line in file_in:
        lines.append(line)

pwd = lines[0]
raw = cas_pdf_to_text("test.pdf", pwd)
txt = "\u2029".join(raw.lines)
# print(txt)
parsed_txn = parse_transaction("18-Aug-2021 ***Change of ADDRESS***")
desc = parsed_txn.description.strip()
units = parsed_txn.units
print(get_transaction_type(desc, units))
# print(process_detailed_text(txt))