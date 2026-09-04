"""Report translation progress for all .ts files under data/pmg_qt/i18n/<lang>."""
import xml.etree.ElementTree as ET
import glob
import os
import sys

lang = sys.argv[1] if len(sys.argv) > 1 else 'zh_CN'
pattern = os.path.join('data', 'pmg_qt', 'i18n', lang, '*.ts')

total, done = 0, 0
rows = []
for f in sorted(glob.glob(pattern)):
    try:
        root = ET.parse(f).getroot()
    except Exception as e:
        rows.append((os.path.basename(f), 'PARSE ERROR: %s' % e, ''))
        continue
    c_total, c_done, c_untr, c_van = 0, 0, 0, 0
    for msg in root.iter('message'):
        c_total += 1
        src = msg.findtext('source') or ''
        tr = msg.find('translation')
        # Whitespace-only sources are passthrough (translation == source);
        # count them as done when a finished translation is present.
        is_done = (tr is not None and tr.get('type') != 'unfinished'
                   and (bool((tr.text or '').strip()) or not src.strip()))
        if is_done:
            c_done += 1
        else:
            c_untr += 1
    total += c_total
    done += c_done
    rows.append((os.path.basename(f), c_total, c_untr))

for row in rows:
    if len(row) == 2:
        print('%-35s %s' % row)
    else:
        name, tt, uu = row
        pct = '' if not tt else ' (%3d%%)' % (100 * (tt - uu) // max(tt, 1))
        print('%-35s total=%-6s unfinished=%s%s' % (name, tt, uu, pct))

print('-' * 60)
if total:
    print('TOTAL: %d strings, %d translated, %d remaining (%.1f%%)'
          % (total, done, total - done, 100.0 * done / total))
