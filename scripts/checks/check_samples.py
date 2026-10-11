#!/usr/bin/env python3
"""Sample check: every sampled transaction is real.

Every row in outputs/samples/*.csv and every row ID printed in audit-program.md
must exist in outputs/analytics-full/spend-clean.csv, and at that sheet row of
the council's workbook in data/spend/ (sheet "Data to publish") with the same
supplier and the same amount. The workbook is read with the standard library.
"""
import re
import xml.etree.ElementTree as ET
import zipfile

import common as c

NAME = "samples"
SHEET = "Data to publish"


def amount(value):
    try:
        return round(float(str(value).replace(",", "")), 2)
    except ValueError:
        return None


def read_sheet(path, sheet):
    """Rows of one sheet of an .xlsx as {excel_row: {column_letters: value}}, standard library only."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
          "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
    with zipfile.ZipFile(path) as z:
        book = ET.fromstring(z.read("xl/workbook.xml"))
        rid = next((s.get(f"{{{ns['r']}}}id") for s in book.iterfind("m:sheets/m:sheet", ns)
                    if s.get("name") == sheet), None)
        if rid is None:
            return None
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels.iterfind("p:Relationship", ns) if r.get("Id") == rid)
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iterfind("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
        out = {}
        for row in ET.fromstring(z.read(target)).iterfind("m:sheetData/m:row", ns):
            cells = {}
            for cell in row.iterfind("m:c", ns):
                column = re.match(r"[A-Z]+", cell.get("r", "")).group(0)
                kind, v = cell.get("t"), cell.find("m:v", ns)
                if kind == "inlineStr":
                    cells[column] = "".join(t.text or "" for t in cell.iter(f"{{{ns['m']}}}t"))
                elif v is not None and v.text is not None:
                    cells[column] = shared[int(v.text)] if kind == "s" else v.text
            out[int(row.get("r"))] = cells
        return out


class Workbooks:
    def __init__(self, folder):
        self.folder, self.cache = folder, {}

    def row(self, name, sheet_row):
        """(supplier, amount) at an Excel row, or an error string."""
        if name not in self.cache:
            path = self.folder / name
            if not path.is_file():
                self.cache[name] = f"workbook {path} not found"
            else:
                try:
                    data = read_sheet(path, SHEET)
                except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
                    data, self.cache[name] = False, f"{name} could not be read as a workbook ({exc})"
                if data is None:
                    self.cache[name] = f"{name} has no sheet '{SHEET}'"
                elif data is not False:
                    head = next((cells for _, cells in sorted(data.items())
                                 if str(cells.get("A", "")).strip() == "Service"), None)
                    names = {str(v).strip(): k for k, v in (head or {}).items()}
                    if "Supplier name" not in names or "Net amount" not in names:
                        self.cache[name] = f"{name}: header row with 'Supplier name' and 'Net amount' not found"
                    else:
                        self.cache[name] = (data, names["Supplier name"], names["Net amount"])
        book = self.cache[name]
        if isinstance(book, str):
            return book
        data, c_supplier, c_amount = book
        if sheet_row not in data:
            return f"{name} has no sheet row {sheet_row}"
        cells = data[sheet_row]
        return str(cells.get(c_supplier, "")).strip(), amount(cells.get(c_amount, ""))


def run(outputs, data):
    items = []
    spend = {r["row_id"]: r for r in c.rows(outputs / "analytics-full/spend-clean.csv")}
    program = c.text(outputs / "audit-program.md")
    samples_dir = outputs / "samples"
    files = sorted(samples_dir.glob("*.csv")) if samples_dir.is_dir() else []
    wanted = {}                                   # row_id -> [(where, supplier or None, amount or None)]
    for path in files:
        for n, row in enumerate(c.rows(path), 2):
            wanted.setdefault(row.get("row_id", ""), []).append(
                (f"samples/{path.name}:{n}", row.get("Supplier name"), amount(row.get("Net amount"))))
    for rid in sorted(set(c.ROW_ID.findall(program))):
        wanted.setdefault(rid, []).append(("audit-program.md", None, None))
    books = Workbooks(data / "spend")
    for rid in sorted(wanted):
        where = wanted[rid][0][0]
        clean = spend.get(rid)
        if not clean:
            items.append(f"{rid} ({where}) is not in spend-clean.csv")
            continue
        supplier, value = clean["Supplier name"].strip(), amount(clean["Net amount"])
        for place, s, a in wanted[rid]:
            if s is not None and (s.strip() != supplier or a != value):
                items.append(f"{rid} ({place}) shows {s!r} {a}; spend-clean.csv has {supplier!r} {value}")
        name, _, sheet_row = rid.rpartition(":")
        found = books.row(name, int(sheet_row))
        if isinstance(found, str):
            items.append(f"{rid} ({where}): {found}")
        elif found != (supplier, value):
            items.append(f"{rid} ({where}): workbook row has {found[0]!r} {found[1]}; "
                         f"spend-clean.csv has {supplier!r} {value}")
    in_program = len(set(c.ROW_ID.findall(program)))
    return items, (f"{len(wanted)} distinct transactions from {len(files)} sample file(s) and {in_program} row IDs in "
                   f"audit-program.md, each traced to spend-clean.csv and the workbook")


if __name__ == "__main__":
    c.main(NAME, run, __doc__)
