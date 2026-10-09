"""Parser for the one-page Daily Geological Operations Summary template.

Uses layout-relative windows to avoid duplicated overlay labels present in
these PDF forms. It also retains original page text for less common questions.
"""
from __future__ import annotations

import re
from pathlib import Path
import fitz
from .common import (
    clean, clipped_lines, date_iso, number, normalized_pages, search,
    segment, source_record, unique_lines,
)


def parse_operation(page: fitz.Page, y0: float, y1: float, label: str) -> str:
    # Source forms contain repeated "Last Ops Update" and "Next Update" overlays.
    ignored = {
        "current ops update", "last ops update", "next update",
        "npt", "current operation @ 0600 hrs :", "last 24 hrs operation",
        "next 24 hrs operation",
    }
    lines = clipped_lines(page, 0, y0, page.rect.width, y1)
    lines = [s for s in lines if s.lower() not in ignored and label.lower() not in s.lower() and s not in {"@", ":"}]
    return unique_lines(lines, ignored)


def parse_dgos(path: str | Path) -> dict:
    path = Path(path)
    with fitz.open(path) as pdf:
        pages = normalized_pages(pdf)
        page = pdf[0]
        body = pages[0]["text"]
        if "DAILY GEOLOGICAL OPERATIONS SUMMARY" not in body.upper():
            raise ValueError(f"Not a DGOS report: {path.name}")

        date_match = re.search(r"Current\s+Date.{0,70}?(\d{2}-\d{2}-\d{4})", body[:450], re.I | re.S)
        dates = re.findall(r"\d{2}-\d{2}-\d{4}", body[:750])
        report_date = date_iso(date_match.group(1) if date_match else (dates[0] if dates else None))
        # Some copies render `Report No:ReportReport72 No.No.`;
        # the page-coordinate region is more reliable than text pattern alone.
        header = clipped_lines(page, page.rect.width * .88, 80, page.rect.width, 115)
        report_number = next((int(s) for s in header if s.isdigit()), None)
        if report_number is None:
            m = re.search(r"Report\s*No\D*(\d{1,4})", body, re.I)
            report_number = int(m.group(1)) if m else None
        well_name = search(body, r"WELL NAME\s*:\s*([\w-]+)")
        # Field and unit labels can overlap, but nearby text uses consistent layout.
        country = search(body, r"COUNTRY\s*:\s*(?:[A-Z]{3}\s*\|\s*)?([A-Z][A-Z ]+?)(?=\s{2,}|\n)")
        if not country:
            country = "MALAYSIA" if "MALAYSIA" in body.upper() else None
        block = search(body, r"BLOCK\s*:\s*([\w-]+)")
        operator = search(body, r"OPERATOR\s*:\s*(PTT[^\n]+?)(?=\s{3,}|\n)")
        rig_name = search(body, r"RIG NAME\s*:\s*([\w-]+)")
        rig_type = search(body, r"RIG TYPE\s*:\s*([\w-]+)")

        current = parse_operation(page, 228, 269, "CURRENT OPERATION")
        previous = parse_operation(page, 287, 348, "LAST 24 HRS")
        next_ops = parse_operation(page, 381, 416, "NEXT 24 HRS")
        npt_lines = clipped_lines(page, 0, 345, page.rect.width, 371)
        npt_description = unique_lines(
            [x for x in npt_lines if x.lower() != "npt" and x.lower() != "npt:"],
        )
        npt_entries = []
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*hrs?\s+due\s+to\s+([^;,.]+)", npt_description, re.I):
            npt_entries.append({"hours": number(m.group(1)), "reason": clean(m.group(2))})
        npt_total = round(sum(x["hours"] for x in npt_entries), 3) if npt_entries else None

        # Progress row is a stable data area in this PDF template. Find numbers
        # by position, rather than using their concatenated text (2530.00MDDF).
        position_words = page.get_text("words")
        row_words = [w for w in position_words if 468 <= w[1] <= 502 and 490 <= w[0] <= 900]
        nums = [(w[0], number(w[4])) for w in row_words if re.fullmatch(r"\d+(?:\.\d+)?", w[4])]
        current_depth = next((n for x, n in nums if x >= page.rect.width * .80 and n is not None), None)
        phase = next((w[4] for w in row_words if re.fullmatch(r"[A-Z]\d+|FRM", w[4])), None)
        mud_words = [w for w in position_words if 532 <= w[1] <= 563 and 700 <= w[0] <= 790]
        mud_weight = next((number(w[4]) for w in mud_words if re.fullmatch(r"\d+(?:\.\d+)?", w[4])), None)
        mud_type = next((w[4] for w in mud_words if re.fullmatch(r"[A-Z]{3,}", w[4])), None)
        # Formation-top rows follow `FORMATION TOPS` near the lower middle of page.
        formation_rows = []
        formation_area = body.split("FORMATIONFORMATION TOPSTOPS SUMMARY", 1)[-1]
        formation_area = formation_area.split("GASGAS SHOWSSHOWS", 1)[0]
        for line in formation_area.splitlines():
            line = clean(line)
            m = re.match(r"^(Seabed|Top\s+[IJKL](?:-Shale)?|K-[\d/]+\*{0,2}|L-\d+\*{0,2}|FTD)\s+(.*)", line, re.I)
            if not m:
                continue
            # Retain full row text in addition to key numbers: table columns are dense.
            matches = re.findall(r"(?<![A-Za-z])[+-]?\d+(?:\.\d+)?(?![A-Za-z])", m.group(2))
            formation_rows.append({
                "formation": clean(m.group(1)),
                "row_text": line,
                "numbers_as_printed": [number(x) for x in matches],
            })

        remark_area = page.get_text("text", clip=fitz.Rect(0, 620, page.rect.width, 820), sort=True)
        # Remarks are numbered and are close to the header of drilling summary.
        remarks = []
        for line in remark_area.splitlines():
            m = re.match(r"^\s*([1-9])\s+(.+)", line)
            if m:
                remarks.append(clean(m.group(2)))

        data = source_record(
            path, "DGOS", pages,
            report_date=report_date, report_number=report_number,
            well_name=well_name, country=country, block=block,
            operator=operator, rig_name=rig_name, rig_type=rig_type,
            current_depth_mddf=current_depth,
            phase=phase,
            mud_weight_ppg=mud_weight,
            mud_type=mud_type,
            current_operation=current,
            last_24h_operation=previous,
            next_24h_operation=next_ops,
            npt_details=npt_entries,
            npt_total_hours=npt_total,
            npt_raw=npt_description,
            formation_tops=formation_rows,
            remarks=remarks,
        )
        for key in ("current_operation", "last_24h_operation", "next_24h_operation", "npt_raw"):
            if data.get(key):
                data["sections"].append(segment(key, data[key]))
        if formation_rows:
            data["sections"].append(segment("formation_tops", "\n".join(r["row_text"] for r in formation_rows)))
        if remarks:
            data["sections"].append(segment("remarks", "; ".join(remarks)))
        # Keep a full-page excerpt too, so arbitrary fields remain queryable.
        data["sections"].append(segment("full_report", body))
        return data
