#
# import io
# import re
# from typing import List, Optional, Iterator, Union
# from collections import namedtuple
# from pdfminer.pdfparser import PDFParser
# from pdfminer.pdfdocument import PDFDocument, PDFPasswordIncorrect, PDFSyntaxError
# from pdfminer.layout import LAParams
# from pdfminer.converter import PDFPageAggregator
# from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
# from pdfminer.pdfpage import PDFPage
# from pdfminer.layout import LTTextBoxHorizontal, LTTextBoxVertical
# InvestorInfo = namedtuple("InvestorInfo", ["name", "email", "address", "mobile"])
# PartialCASData = namedtuple("PartialCASData", ["file_type", "investor_info", "lines"])
# from casparser.enums import FileType
# from casparser.exceptions import CASParseError, IncorrectPasswordError
# # from .utils import is_close, InvestorInfo, PartialCASData
# def is_close(a0, a1, tol=1.0e-4):
#     """
#     Check if two elements are almost equal with a tolerance.

#     :param a0: number to compare
#     :param a1: number to compare
#     :param tol: The absolute tolerance
#     :return: Returns boolean value if the values are almost equal
#     """
#     return abs(a0 - a1) < tol

# def parse_investor_info(layout, width, height) -> InvestorInfo:
#     """Parse investor info."""
#     text_elements = sorted(
#         [
#             x
#             for x in layout
#             if isinstance(x, LTTextBoxHorizontal) and x.x1 < width / 1.5 and x.y1 > height / 2
#         ],
#         key=lambda x: -x.y1,
#     )
#     email_found = False
#     address_lines = []
#     email = None
#     mobile = None
#     name = None
#     for el in text_elements:
#         txt = el.get_text().strip()
#         if txt == "":
#             continue
#         if not email_found:
#             if m := re.search(r"^\s*email\s+id\s*:\s*(.+?)(?:\s|$)", txt, re.I):
#                 email = m.group(1).strip()
#                 email_found = True
#             continue
#         if name is None:
#             name = txt
#         else:
#             if (
#                 re.search(r"Date\s+Transaction|Folio\s+No|^Date\s*$", txt, re.I | re.MULTILINE)
#                 or mobile is not None
#             ):
#                 return InvestorInfo(
#                     email=email, name=name, mobile=mobile or "", address="\n".join(address_lines)
#                 )
#             elif m := re.search(r"mobile\s*:\s*([+\d]+)(?:s|$)", txt, re.I):
#                 mobile = m.group(1).strip()
#             address_lines.append(txt)
#     raise CASParseError("Unable to parse investor data")


# def detect_pdf_source(document) -> FileType:
#     """
#     Try to infer pdf source (CAMS/KFINTECH) from the pdf metadata.

#     :param document: PDF document object
#     :return: FileType
#     """
#     file_type = FileType.UNKNOWN
#     for info in document.info:
#         producer = info.get("Producer", b"").decode("utf8", "ignore").replace("\x00", "")
#         if "Data Dynamics ActiveReports" in producer:
#             file_type = FileType.KFINTECH
#         elif "Stimulsoft Reports" in producer:
#             file_type = FileType.CAMS
#         if file_type != FileType.UNKNOWN:
#             break
#     return file_type


# def group_similar_rows(elements_list: List[Iterator[LTTextBoxHorizontal]]):
#     """
#     Group `LTTextBoxHorizontal` elements having similar rows, with a tolerance.

#     :param elements_list: List of elements from each page
#     """
#     lines = []
#     for elements in elements_list:
#         sorted_elements = list(sorted(elements, key=lambda x: (-x.y1, x.x0)))
#         if len(sorted_elements) == 0:
#             continue
#         y0, y1 = sorted_elements[0].y0, sorted_elements[0].y1
#         items = []
#         for el in sorted_elements:
#             if len(items) > 0 and not (is_close(el.y1, y1, tol=3) or is_close(el.y0, y0, tol=3)):
#                 line = "\t\t".join(
#                     [x.get_text().strip() for x in sorted(items, key=lambda x: x.x0)]
#                 )
#                 if line.strip():
#                     lines.append(line)
#                 items = []
#                 y0, y1 = el.y0, el.y1
#             items.append(el)
#     return lines


# def cas_pdf_to_text(filename: Union[str, io.IOBase], password) -> PartialCASData:
#     """
#     Parse CAS pdf and returns line data.

#     :param filename: CAS pdf file (CAMS or Kfintech)
#     :param password: CAS pdf password
#     :return: array of lines from the CAS.
#     """
#     file_type: Optional[FileType] = None

#     if isinstance(filename, str):
#         fp = open(filename, "rb")
#     elif hasattr(filename, "read") and hasattr(filename, "close"):  # file-like object
#         fp = filename
#     else:
#         raise CASParseError("Invalid input. filename should be a string or a file like object")

#     with fp:
#         pdf_parser = PDFParser(fp)
#         try:
#             document = PDFDocument(pdf_parser, password=password)
#         except PDFPasswordIncorrect:
#             raise IncorrectPasswordError("Incorrect PDF password!")
#         except PDFSyntaxError:
#             raise CASParseError("Unhandled error while opening file")

#         line_margin = {FileType.KFINTECH: 0.1, FileType.CAMS: 0.2}.get(
#             detect_pdf_source(document), 0.2
#         )

#         rsrc_mgr = PDFResourceManager()
#         laparams = LAParams(line_margin=line_margin, detect_vertical=True)
#         device = PDFPageAggregator(rsrc_mgr, laparams=laparams)
#         interpreter = PDFPageInterpreter(rsrc_mgr, device)

#         pages: List[Iterator[LTTextBoxHorizontal]] = []

#         investor_info = None
#         for page in PDFPage.create_pages(document):
#             interpreter.process_page(page)
#             layout = device.get_result()
#             text_elements = filter(lambda x: isinstance(x, LTTextBoxHorizontal), layout)
#             if file_type is None:
#                 for el in filter(lambda x: isinstance(x, LTTextBoxVertical), layout):
#                     if re.search("CAMSCASWS", el.get_text()):
#                         file_type = FileType.CAMS
#                     if re.search("KFINCASWS", el.get_text()):
#                         file_type = FileType.KFINTECH
#             if investor_info is None:
#                 investor_info = parse_investor_info(layout, *page.mediabox[2:])
#             pages.append(text_elements)

#         lines = group_similar_rows(pages)
#         return PartialCASData(file_type=file_type, investor_info=investor_info, lines=lines)
# # print(cas_pdf_to_text("teststatement.pdf", "get123"))
raw = '''Consolidated Account Statement 01-Apr-2021 To 21-Oct-2021 Email Id: SHIVAH4@GMAIL.COM		This Consolidated Account Statement is brought to you as an investor
friendly initiative by CAMS and KFintech, and lists the transactions,
balances and valuation of Mutual Funds in which you are holding
investments. The consolidation has been carried out based on the email id
entered by you. If you have not entered a PAN Number and if the email id
is common to several members of your family, this statement will
consolidate all those investments as well. SHIVANAND HIREMATH 6 COURTLANDSAVENUE
LANGLEY
SLOUGH
SLOUGH - SL37LE
Berkshire
UNITED KINGDOM
Phone Res: 8867130398
Mobile: 8867130398 If you find any folios missing from this consolidation, you have not
registered your email id against those folios. Date		Transaction		Amount		Units		Price		Unit (INR)		(INR)		Balance Canara Robeco Mutual Fund Folio No: 18816743125 / 0		PAN: AAXPH4499R		KYC: OK  PAN: OK 101LCGPG-Canara Robeco Blue Chip Equity Fund - Regular Growth(Advisor: ARN-0155)		Registrar :
KFINTECH Opening Unit Balance: 4,727.636 *** No transactions during this statement period *** Closing Unit Balance: 4,727.636		NAV on 20-Oct-2021: INR 43.19		Valuation on 20-Oct-2021: INR 204,186.60 Current Load Structure : Entry Load : For all investment amounts - Lumpsum/SIP/STP: NIL. Exit Load : w.e.f.20/08/2010 - For all investment amounts -
Lumpsum/SIP/STP: 1% if reedemed / switched out within one year from the date of allotment and NIL after one year. Folio No: 18816743125 / 0		PAN: AAXPH4499R		KYC: OK  PAN: OK 101GBOEG-Canara Robeco Equity Hybrid Fund - Regular Growth(Advisor: ARN-0155)		Registrar :
KFINTECH Opening Unit Balance: 1,683.080 27-Apr-2021		Systematic Investment (1)		10,000.50		47.353		211.19		1,730.433 27-Apr-2021		*** Stamp Duty ***		0.50 27-May-2021		Systematic Investment (1)		10,000.50		45.527		219.66		1,775.960 27-May-2021		*** Stamp Duty ***		0.50 25-Jun-2021		Systematic Investment (1)		10,000.50		44.026		227.15		1,819.986 25-Jun-2021		*** Stamp Duty ***		0.50 27-Jul-2021		Systematic Investment (1)		10,000.50		43.409		230.38		1,863.395 27-Jul-2021		*** Stamp Duty ***		0.50 26-Aug-2021		Systematic Investment (1)		10,000.50		42.214		236.90		1,905.609 26-Aug-2021		*** Stamp Duty ***		0.50 28-Sep-2021		Systematic Investment (1)		10,000.50		40.499		246.93		1,946.108 28-Sep-2021		*** Stamp Duty ***		0.50 Closing Unit Balance: 1,946.108		NAV on 20-Oct-2021: INR 250.43		Valuation on 20-Oct-2021: INR 487,363.83 W.e.f.18/06/2018, Entry Load : NIL. For any redemption / switch out upto 10% of units within 1 Year from the date of allotment – Nil; For any redemption / switch
out more than 10% ofunits within 1 Year from the date of allotment - 1%; For any redemption / switch out after 1 Year from the date of allotment - Nil Franklin Templeton Mutual Fund Folio No: 19809529 / 0		PAN: AAXPH4499R		KYC: OK  PAN: OK FTI272-Franklin India Focused Equity Fund - IDCW# - Payout(Advisor: ARN-0155)		Registrar : CAMS Opening Unit Balance: 0.000 *** No transactions during this statement period *** Closing Unit Balance: 0.000		NAV on 20-Oct-2021: INR 31.3624		Valuation on 20-Oct-2021: INR 0.00 As per Rule 4 of the STT Rules 2004, where the STT payable is 50 paise and above, it is rounded off to the nearest rupee. Thereby, where the amount of STT payable
is lower than 50 paise, no STT is deducted. Long-term capital gains arising on transfer of units of an equity oriented fund chargeable to Securities Transaction tax
(STT) are subject to tax in accordance with the provisions of section 112A of the Income-tax Act, 1961. Therefore, as per provisions of the Act, if STT payable is NIL
due to rounding off, the long term capital gain shall be chargeable to tax in accordance with the provisions of section 112A W.e.f 11/12/2017 Entry Load - Nil; Exit Load: 1% if redeemed/switched-out within 1 year from the date of allotment: For SIP/STP, basis registration date ICICI Prudential Mutual Fund Folio No: 7994328 / 72		PAN: AMMPH4785R		KYC: OK  PAN: OK PDFD-ICICI Prudential Value Discovery Fund - IDCW# - Payout(Advisor: ARN-0155)		Registrar : CAMS Opening Unit Balance: 0.000 *** No transactions during this statement period *** Consolidated Account Statement 01-Apr-2021 To 21-Oct-2021 Date		Transaction		Amount		Units		Price		Unit (INR)		(INR)		Balance Closing Unit Balance: 0.000		NAV on 20-Oct-2021: INR 33.49		Valuation on 20-Oct-2021: INR 0.00 Current : Entry Load - Nil. Exit Load w.e.f 07-May-2013 [including SIP,STP,SWP&Micro(SIP) wherever available] - If redeemed or switched out upto 12 months - 1.0%, >
12 months - Nil. For lumpsum investment/switch in, the applicable load will be based on the load structure as on the date of investment/applicable NAV date. For
SIP/STP transactions, load for each transaction is based on the applicable load structure as on the registration date. For details, please refer to SID and Addenda
available on www.icicipruamc.com. Invesco Mutual Fund Folio No: 3101588416 / 0		KYC: NOT OK  PAN: NOT OK 120CFGPG-Invesco India Contra Fund - Growth(Advisor: ARN-0155)		Registrar :
KFINTECH Opening Unit Balance: 105.463 *** No transactions during this statement period *** Closing Unit Balance: 105.463		NAV on 20-Oct-2021: INR 79.69		Valuation on 20-Oct-2021: INR 8,404.35 Entry Load - NIL, Exit Load: (a) If upto 10% of units allotted are redeemed (or) switched out within 1 year from the date of allotment - NIL. (b) Any redemption (or)
switch-out of units in excess of 10% of units allotted - 1%.(c) If units are redeemed (or) switched out after 1 year from the date of allotment - NIL. The above exit load
is not applicable for purchases made through IDCW Transfer Plan (DTP). No load after 1 year from the date of allotment.Please Note that prevailing exit load
structure at the time of investment will be applicable for redemption/switch-out. Kotak Mutual Fund Folio No: 3471519 / 42		PAN: AAXPH4499R		KYC: OK  PAN: OK K190-Kotak Credit Risk Fund - Growth (Regular Plan) (Erstwhile Kotak Income Opp.) (Advisor: ARN-0155)		Registrar : CAMS Opening Unit Balance: 0.000 18-Aug-2021 ***Change of Gender*** Closing Unit Balance: 0.000		NAV on 20-Oct-2021: INR 24.2456		Valuation on 20-Oct-2021: INR 0.00 Entry Load  - Nil, Exit Load (w.e.f. 13-May-2020) - For redemption/switch out of units upto 6% of the initial investment amount (limit) purchased or switched-in within
1 year from the date of allotment - NIL.  If Units redeemed or switched out are in excess of the limit within 1 year from the date of allotment : 1%.  If units redeemed
or switched out on or after 1 year from the date of allotment: NIL. Mirae Asset Mutual Fund Folio No: 70414324164 / 0		PAN: AAXPH4499R		KYC: OK  PAN: OK 117IORGG-Mirae Asset Large Cap Fund - Regular Growth Plan(Advisor: ARN-146822)		Registrar :
KFINTECH Opening Unit Balance: 10,335.063 *** No transactions during this statement period *** Closing Unit Balance: 10,335.063		NAV on 20-Oct-2021: INR 82.286		Valuation on 20-Oct-2021: INR 850,430.99 Entry Load: Nil and Exit Load :  For SWP 15% of the units allotted (including Switch-in/STP-in) on or before completion of 365 days from the date of allotment of units
is NIL. Any redemption in excess of such limit, on FIFO basis, or other redemptionsof investor who have not opted for SWP(Inc Switch out, STP out) and If redeemed
within 1 year (365 Days) from the date of allotment Exit load is 1%  and after 365 days from the date of allotment Exit load is NIL . SBI Mutual Fund Folio No: 15025623		PAN: AMMPH4785R		KYC: OK  PAN: OK L24-SBI Equity Hybrid Fund - Regular Plan - IDCW# (formerly SBI Magnum Balanced Fund) - Payout(Advisor: ARN0155)		Registrar : CAMS Opening Unit Balance: 0.000 *** No transactions during this statement period *** Closing Unit Balance: 0.000		NAV on 20-Oct-2021: INR 44.1159		Valuation on 20-Oct-2021: INR 0.00 "Entry Load: N.A;  Exit Load (w.e.f. 16-OCT-2015): NIL for 10% of investment and 1.00% exit load for remaining investment if redeemed/switched within 12 month
from the date of investment; NIL if redeemed/switched after 12 month from the date of investment.  For applicability of load structure, please refer to SAI/SID/
KIM/Addendum issued from time to time.**Scheme name of """SBI Magnum Balanced Fund"""  has been changed to """SBI Equity Hybrid Fund"""  with effect from 16th
May 2018.W.e.f. 1st July 2020, Stamp Duty @ 0.005% is applicable on allotment of units.  As per SEBI guidelines, w.e.f. February 01, 2021, applicable NAV for
allotment of units shall be based on time of receipt of transaction and funds available for utilization upto the cut-off time" Folio No: 15025624		PAN: AAXPH4499R		KYC: OK  PAN: OK L017-SBI Large & Midcap Fund - Regular Plan - IDCW# (formerly SBI Magnum Multiplier Fund) - Payout(Advisor: ARN0155)		Registrar : CAMS Opening Unit Balance: 0.000 *** No transactions during this statement period *** Closing Unit Balance: 0.000		NAV on 20-Oct-2021: INR 166.3678		Valuation on 20-Oct-2021: INR 0.00 "Entry Load : N.A.; Exit Load - W.e.f. 15-Jan-2019: 0.10% if redeemed/switched within 30 Calendar days from the date of investment;ÿ NIL if redeemed/switched
after 30 Calendar days from the date of investment. STT @ 0.001% is applicable at the time of redemption / switch. For applicability of exit load structure for specific
transaction, please refer to Addendum issued from time to time.**Scheme name of """""SBI Magnum Multiplier Fund"""""  has been changed to """""SBI Large & Midcap
Fund"""""  with effect from 16th May 2018."                                                                                                                                             W.e.f. 1st July 2020, Stamp
Duty @ 0.005% is applicable on allotment of units.  As per SEBI guidelines, w.e.f. February 01, 2021, applicable NAV for allotment of units shall be based on time of
receipt of transaction and funds available for utilization upto the cut-off time #IDCW - Income Distribution cum Capital Withdrawal'''