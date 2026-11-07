"""Enrichit l'article Radar 393 : aperçu en bref, frise SVG, cartes par profil. Faits repris de l'article seulement."""
import re
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
html = src.read_text(encoding='utf-8')
assert 'radar-bref' not in html, 'déjà enrichi'

SAP, ODOO, EXT, TRANS, S4 = '#0369a1', '#714B67', '#d97706', '#64748b', '#059669'


def icon(path, color, size=30):
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex:none">{path}</svg>')


I_CAL = '<rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4M8 14h3"/>'
I_SHIELD = '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M12 8v4l2.5 1.5"/>'
I_PEN = '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>'
I_BUILD = '<path d="M4 21V5l8-2v18M12 8h8v13M2 21h20M7 8h2M7 12h2M7 16h2M15 12h2M15 16h2"/>'
I_MOVE = '<path d="M4 8h13l-3-3M20 16H7l3 3"/>'
I_HAND = '<path d="M8 12l3 3 5-6"/><circle cx="12" cy="12" r="9"/>'
I_CODE = '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>'

CSS = """
  .radar-bref { margin: .5rem 0 1.5rem; }
  .radar-carte { border: 1px solid #e2e8f0; border-radius: 10px; padding: .9rem 1rem; height: 100%; background: #fff; }
  .radar-carte .radar-carte-tete { display: flex; align-items: center; gap: .6rem; margin-bottom: .35rem; }
  .radar-carte .radar-date { font-weight: 700; font-size: 1.05rem; white-space: nowrap; }
  .radar-carte p { margin: 0; font-size: .95rem; line-height: 1.5; }
  .radar-frise { margin: 1.5rem 0 .5rem; }
  .radar-frise-defil { overflow-x: auto; }
  @media (max-width: 575px) { .radar-frise svg { min-width: 700px; } }
  .radar-frise svg {  max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.08); background: #fff; }
  .radar-legende { font-size: .9rem; color: #475569; }
  .radar-profil { border-left: 4px solid #cbd5e1; }
"""
html = html.replace('</style>', CSS + '</style>', 1)


def carte(ic, color, titre, texte, extra=''):
    return (f'<div class="col-md-4 mb-3"><div class="radar-carte"{extra}><div class="radar-carte-tete">{icon(ic, color)}'
            f'<span class="radar-date" style="color:{color}">{titre}</span></div><p>{texte}</p></div></div>')


bref = ('\n        <div class="radar-bref"><h2 class="h5 mb-3">En bref</h2><div class="row">'
        + carte(I_CAL, SAP, '31 déc. 2027', 'Fin de la maintenance standard de SAP Business Suite 7, dont SAP ERP 6.0 (SAP).')
        + carte(I_SHIELD, EXT, '31 déc. 2030', 'Fin de la maintenance étendue optionnelle, des accords bases tierces et Java, et des outils de conversion (SAP).')
        + carte(I_PEN, ODOO, '21 oct. 2026', 'Odoo SA publie « Odoo ou SAP ? » et affirme qu\'une migration depuis SAP est possible.')
        + '</div></div>')
m = re.search(r'(<p class="radar-chapeau">.*?</p>)', html, re.S)
html = html[:m.end()] + bref + html[m.end():]

# --- frise chronologique -------------------------------------------------------------------------
PTS = [(2020, 70), (2021, 130), (2026, 190), (2028, 430), (2031, 610), (2034, 770), (2035, 830), (2041, 950)]


def x(t):
    for (t0, x0), (t1, x1) in zip(PTS, PTS[1:]):
        if t0 <= t <= t1:
            return round(x0 + (x1 - x0) * (t - t0) / (t1 - t0), 1)
    raise ValueError(t)


AX = 150
s = ['<svg viewBox="0 0 1000 400" xmlns="http://www.w3.org/2000/svg" role="img" '
     'aria-label="Frise : échéances de SAP Business Suite 7 de 2020 à 2040, et publication du billet Odoo du 21 octobre 2026" '
     'style="max-width:100%;height:auto" font-family="Liberation Sans, Arial, sans-serif">',
     '<rect width="1000" height="400" fill="#ffffff"/>',
     '<text x="30" y="34" font-size="23" font-weight="700" fill="#0f172a">SAP Business Suite 7 : le calendrier publié par SAP</text>',
     f'<line x1="40" y1="{AX}" x2="975" y2="{AX}" stroke="#94a3b8" stroke-width="2"/>']
for xb in (x(2023.5), x(2034.5)):  # coupures d'échelle
    s.append(f'<path d="M{xb-7} {AX+9} l7 -18 M{xb+1} {AX+9} l7 -18" stroke="#94a3b8" stroke-width="2"/>'
             f'<rect x="{xb-4}" y="{AX-3}" width="8" height="6" fill="#fff"/>')
for yr in (2020, 2026, 2028, 2031, 2034, 2041):
    lab = yr if yr not in (2028, 2031, 2034, 2041) else yr - 1
    lab_txt = {2028: 'fin 2027', 2031: 'fin 2030', 2034: 'fin 2033', 2041: 'fin 2040'}.get(yr, str(lab))
    s.append(f'<line x1="{x(yr)}" y1="{AX-6}" x2="{x(yr)}" y2="{AX+6}" stroke="#64748b" stroke-width="2"/>'
             f'<text x="{x(yr)}" y="{AX+27}" font-size="17" fill="#334155" text-anchor="middle" font-weight="600">{lab_txt}</text>')
# jalons au-dessus de l'axe
for t, c, l1, l2, dx, y1, anchor in ((2020.1, SAP, '4 févr. 2020', 'SAP annonce fin 2027', 0, 62, 'start'),
                                     (2026.77, SAP, '7 oct. 2026', 'SAP confirme les dates', -10, 108, 'end'),
                                     (2026.81, ODOO, '21 oct. 2026', 'Odoo publie « Odoo ou SAP ? »', 40, 62, 'start')):
    xx = x(t) + dx
    xt = xx + (6 if anchor == 'start' else -6)
    s.append(f'<line x1="{x(t)}" y1="{AX}" x2="{xx}" y2="{y1+12}" stroke="{c}" stroke-width="1.5" stroke-dasharray="3 3"/>'
             f'<circle cx="{x(t)}" cy="{AX}" r="6" fill="{c}"/>'
             f'<text x="{xt}" y="{y1}" font-size="16" font-weight="700" fill="{c}" text-anchor="{anchor}">{l1}</text>'
             f'<text x="{xt}" y="{y1+19}" font-size="16" fill="#334155" text-anchor="{anchor}">{l2}</text>')
# barres sous l'axe
BARS = ((2020, 2028, SAP, 'Maintenance standard', 'jusqu\'au 31 déc. 2027', 1),
        (2028, 2031, EXT, 'Maintenance étendue optionnelle', '2028-2030, deux points de plus', 1),
        (2031, 2034, TRANS, 'Transition Option (grands clients)', '2031-2033, sous conditions', 0.75),
        (2028, 2041, S4, 'SAP S/4HANA : au moins une version maintenue', 'jusqu\'à fin 2040', 1))
for i, (a, b, c, l1, l2, op) in enumerate(BARS):
    y = 212 + i * 46
    dash = ' stroke-dasharray="6 4"' if c == TRANS else ''
    s.append(f'<rect x="{x(a)}" y="{y}" width="{x(b)-x(a)}" height="16" rx="8" fill="{c}" fill-opacity="{0.9*op}" stroke="{c}"{dash}/>')
    tx, anchor = (x(a), 'start') if c not in (SAP, TRANS) else (x(b), 'end')
    s.append(f'<text x="{tx}" y="{y-7}" font-size="16" text-anchor="{anchor}" fill="#0f172a" paint-order="stroke" stroke="#fff" stroke-width="4"><tspan font-weight="700">{l1}</tspan>'
             f'<tspan fill="#475569"> · {l2}</tspan></text>')
s.insert(4, '<line x1="{0}" y1="76" x2="{0}" y2="385" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="4 4"/>'.format(x(2031)))
for k, l in enumerate(('Fin 2030 : accords bases tierces et Java', 'expirés, conversion vers S/4HANA ou Cloud ERP', 'en nouvelle implémentation seulement')):
    s.append(f'<text x="{x(2031)+8}" y="{62+k*18}" font-size="15" fill="#b91c1c">{l}</text>')
s.append('</svg>')
svg = ''.join(s)

frise = ('\n        <figure class="radar-frise"><div class="radar-frise-defil">' + svg + '</div>' +
         '<figcaption class="radar-legende mt-2">Frise établie d\'après la page de stratégie de maintenance de SAP '
         '(annonce du 4 février 2020) et le billet du SAP News Center du 7 octobre 2026. L\'échelle est coupée '
         'entre 2021 et 2026, puis après 2033. Sur mobile, faites défiler la frise.</figcaption></figure>\n'
         '        <p>La frise se lit de gauche à droite. La barre bleue s\'arrête fin 2027 : c\'est la première date à retenir. '
         'La barre orange, optionnelle et payante, mène à fin 2030, où plusieurs accords expirent ensemble (trait rouge). '
         'La Transition Option, en pointillés, ne concerne que les plus grands clients. En vert, l\'engagement de SAP '
         'sur SAP S/4HANA jusqu\'à fin 2040. En violet, le billet d\'Odoo, publié deux semaines après le rappel de SAP.</p>')
m = re.search(r'<h2>Le contexte</h2>.*?(\n\s*</div></div></div>\s*\n</section>)', html, re.S)
html = html[:m.start(1)] + frise + html[m.start(1):]

# --- cartes par profil ---------------------------------------------------------------------------
PROFILS = ((I_BUILD, SAP, 'Pour une PME ou une ETI sur SAP ERP 6.0.'), (I_MOVE, ODOO, 'Pour une entreprise qui envisage Odoo.'),
           (I_HAND, S4, 'Pour un intégrateur Odoo.'), (I_CODE, EXT, 'Pour un développeur Odoo.'))
cartes = []
for ic, c, lead in PROFILS:
    m = re.search(r'\s*<p><strong>' + re.escape(lead) + r'</strong>\s*(.*?)</p>', html, re.S)
    assert m, lead
    html = html[:m.start()] + ('@@PROFILS@@' if not cartes else '') + html[m.end():]
    cartes.append(f'<div class="col-md-6 mb-3"><div class="radar-carte radar-profil" style="border-left-color:{c}">'
                  f'<div class="radar-carte-tete">{icon(ic, c, 26)}<strong>{lead[:-1]}</strong></div><p>{m.group(1)}</p></div></div>')
html = html.replace('@@PROFILS@@', '\n        <div class="row">' + ''.join(cartes) + '</div>', 1)
out.write_text(html, encoding='utf-8')
mots_av = len(re.sub(r'<[^>]+>', ' ', re.sub(r'<(style|svg).*?</\1>', ' ', src.read_text(), flags=re.S)).split())
mots_ap = len(re.sub(r'<[^>]+>', ' ', re.sub(r'<(style|svg).*?</\1>', ' ', html, flags=re.S)).split())
print('OK', mots_av, '->', mots_ap, 'mots')
