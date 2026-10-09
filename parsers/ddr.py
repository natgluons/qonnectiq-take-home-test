"""Parser for the multi-page Daily Drilling / Daily Operation Report template."""
from __future__ import annotations

import re
from pathlib import Path
import fitz
from .common import clean, date_iso, normalized_pages, number, search, segment, source_record, chunk


def extract_status(text: str, field: str, next_field: str) -> str | None:
    # Layout includes wrap-around descriptions; match from one label to the next.
    regex = rf"(?im)^\s*{re.escape(field)}\s*:\s*(.*?)(?=^\s*{re.escape(next_field)}\s*:|\Z)"
    match = re.search(regex, text, re.S | re.M | re.I)
    return clean(match.group(1)) if match else None


def parse_ddr(path: str | Path) -> dict:
    path = Path(path)
    with fitz.open(path) as pdf:
        pages = normalized_pages(pdf)
        first = pages[0]["text"]
        if "DAILY OPERATION REPORT" not in first.upper():
            raise ValueError(f"Not a DDR report: {path.name}")
        report_number_str = search(first, r"Report\s+no\.?:\s*(\d+)")
        report_date = date_iso(search(first, r"Report\s+date:\s*(\d{2}/\d{2}/\d{4})"))
        daily_npt = number(search(first, r"Daily\s+NPT\s*:\s*([\d.]+)"))
        cumulative_npt = number(search(first, r"Cumm\s+NPT\s*:\s*([\d.]+)"))
        fields = {
            "well_name": search(first, r"Well:\s*([\w-]+)"),
            "rig_name": search(first, r"Rig\s+Name:\s*([\w-]+)"),
            "block": search(first, r"Block:\s*([\w-]+)"),
            "water_depth_m": number(search(first, r"Water\s+Depth:\s*([\d.]+)")),
            "measured_depth_m": number(search(first, r"\bMD\s*:\s*([\d,.]+)")),
            "true_vertical_depth_m": number(search(first, r"\bTVD\s*:\s*([\d,.]+)")),
            "daily_cost_usd": number(search(first, r"Daily\s+Cost\s*:\s*([\d,.]+)")),
            "cumulative_cost_usd": number(search(first, r"Cumm\s+Cost\s*:\s*([\d,.]+)")),
            "afe_cost_usd": number(search(first, r"AFE\s+Cost\s*:\s*([\d,.]+)")),
            "daily_npt_hours": daily_npt,
            "cumulative_npt_hours": cumulative_npt,
            "current_status": extract_status(first, "Current status", "24 hr summary"),
            "last_24h_operation": extract_status(first, "24 hr summary", "24 hr forecast"),
            "next_24h_operation": extract_status(first, "24 hr forecast", "Incident / Accident"),
            "incident_accident": extract_status(first, "Incident / Accident", "Remarks"),
        }
        data = source_record(
            path, "DDR", pages,
            report_number=int(report_number_str) if report_number_str else None,
            report_date=report_date,
            **fields,
        )
        for title in ("current_status", "last_24h_operation", "next_24h_operation", "incident_accident"):
            if data.get(title):
                data["sections"].append(segment(title, data[title]))
        # Each page stays attributable to its source page. Paginated operation
        # notes can span pages; adjacent chunks remain accessible to retrieval.
        for page in pages:
            for i, item in enumerate(chunk(page["text"], max_chars=1900)):
                if len(item) >= 12:
                    data["sections"].append(segment(f"page_{page['page']}_part_{i+1}", item, page["page"]))
        return data
