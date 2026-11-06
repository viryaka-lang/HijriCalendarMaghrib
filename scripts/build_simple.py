"""Builds index.html, the easy-to-read calendar (the site's main page), from data/calendar.json.
The detailed forecast page with maps and model evidence is details.html (built by build_calendar.py).
Needs no maps and no extra packages:  python scripts/build_simple.py [output.html]
build_calendar.py runs it at the end, so both pages always match."""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEAD = ('<!doctype html>\n<html lang="ar" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n')


def simple_data():
    cal = json.load(open(ROOT / 'data' / 'calendar.json', encoding='utf-8'))
    months = []
    for m in cal['months']:
        if m['hy'] > 1460:  # Muharram 1461 is only the end anchor for the last month
            continue
        fc = m['status'] == 'forecast'
        months.append([m['hy'], m['hm'], m['start'], m['len'], 1 if fc else 0, m.get('dist') if fc else None])
    return dict(built=cal['today'], months=months)


def render(detail_link='details.html', standalone=True):
    """standalone=True: a complete HTML file for GitHub Pages (with the calendar-file download).
    standalone=False: the page body only, for hosts that add their own <head> and block downloads."""
    tpl = open(ROOT / 'scripts' / 'simple_template.html', encoding='utf-8').read()
    js = json.dumps(simple_data(), separators=(',', ':'), ensure_ascii=False)
    page = (tpl.replace('__SIMPLE_DATA__', js).replace('__DETAIL_LINK__', detail_link)
               .replace('__CAN_DOWNLOAD__', 'true' if standalone else 'false'))
    return (HEAD + page) if standalone else page


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'index.html'
    standalone = os.environ.get('STANDALONE', '1') == '1'
    link = os.environ.get('DETAIL_LINK', 'details.html')
    out.write_text(render(link, standalone), encoding='utf-8')
    print('wrote', out)
