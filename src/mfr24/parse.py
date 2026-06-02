from __future__ import annotations

from bs4 import BeautifulSoup

from mfr24.models import Flight


def parse_iata(html: object) -> str:
    if not isinstance(html, str) or not html.strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("a", class_="show-hovercard")
    if link:
        return link.get_text(strip=True)
    span = soup.find("span", class_="tooltip")
    if span:
        return span.get_text(strip=True)
    return soup.get_text(strip=True)


def parse_date(html: object) -> str:
    if not isinstance(html, str) or not html.strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")
    span = soup.find("span", class_="inner-date")
    return span.get_text(strip=True) if span else ""


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _flight(
    date_html: object,
    flight_raw: object,
    from_html: object,
    to_html: object,
    dep_raw: object,
    arr_raw: object,
) -> Flight:
    return Flight(
        date=parse_date(date_html),
        from_iata=parse_iata(from_html),
        to_iata=parse_iata(to_html),
        dep_time=_text(dep_raw),
        arr_time=_text(arr_raw),
        flight_number=_text(flight_raw) or None,
    )


def parse_api_row(row: list) -> Flight:
    def field(index: int) -> object:
        return row[index] if len(row) > index else None

    return _flight(field(0), field(1), field(2), field(3), field(5), field(6))


def parse_profile_rows(html: str) -> dict[int, Flight]:
    """Parse the server-rendered flights table keyed by ``data-row-number``.

    Row 0 (the newest flight) only ever appears here, never in the load-more API.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: dict[int, Flight] = {}
    for tr in soup.select("table.flight-list-original tbody tr[data-row-number]"):
        try:
            row_number = int(str(tr.get("data-row-number")))
        except (ValueError, TypeError):
            continue
        cells = tr.find_all("td")
        if len(cells) < 8:
            continue
        rows[row_number] = _flight(
            cells[0].decode_contents(),
            cells[1].get_text(strip=True),
            cells[3].decode_contents(),
            cells[4].decode_contents(),
            cells[6].get_text(strip=True),
            cells[7].get_text(strip=True),
        )
    return rows
