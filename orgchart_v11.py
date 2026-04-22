"""
org_chart_v11.py — matplotlib org chart with pixel-precise layout.
Replaces Graphviz entirely. Output: PNG (web-ready; also embeds cleanly in PDF).

Data format — nested dict:
    {
        'name':    str,
        'title':   str  (optional, shown in coloured header band),
        'color':   str  (optional hex, inherited by reports if omitted),
        'reports': list of child dicts (same structure, recursive),
    }

Current layout handles: root -> single VP -> N directors -> leaf reports.
"""

import matplotlib
matplotlib.use('Agg')          # file output, no GUI required
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import textwrap

# ── Visual constants (all in inches; figure rendered at DPI below) ─────────────
DPI        = 150
CARD_W     = 1.35    # leaf / director card width
CARD_H_HDR = 0.46    # coloured title band (tall enough for 2-line wrap)
CARD_H_NAM = 0.30    # white name band
CARD_H     = CARD_H_HDR + CARD_H_NAM   # 0.76 total

COL_GAP    = 0.18    # gap between the two leaf columns under one director
ROW_GAP    = 0.13    # vertical gap between leaf rows in same column
LEVEL_GAP  = 0.52    # vertical clearance between card-bottom and next card-top
DIR_GAP    = 0.28    # horizontal gap between adjacent director subtrees

EDGE_CLR   = '#7f8c8d'
EDGE_LW    = 1.3

# Width each director's 2-column leaf block occupies (fixed for all directors)
SUBTREE_W  = CARD_W * 2 + COL_GAP   # ≈ 2.88 inches


# ── Utilities ──────────────────────────────────────────────────────────────────

def _wrap(text, chars):
    return '\n'.join(textwrap.wrap(str(text), chars))


def _leaf_rows(n):
    return (n + 1) // 2


def leaf_grid_h(n):
    rows = _leaf_rows(n)
    return rows * CARD_H + max(0, rows - 1) * ROW_GAP


# ── Drawing primitives ─────────────────────────────────────────────────────────

def draw_card(ax, x, y_top, w, name, title=None,
              header_color='#1a5fa0', tall=False):
    """
    Draw a card with top-left corner at (x, y_top).
    Axis is inverted so y increases downward.
    title present -> 2-band card (coloured header + white name row).
    title absent  -> 1-band full-colour card (used for header-only nodes).
    tall=True     -> name band 1.5× taller (lone odd leaf filler).
    """
    h_nam = CARD_H_NAM * 1.5 if tall else CARD_H_NAM
    chars = max(18, int(w * 16))       # wrap chars ≈ 16 per inch
    bdr   = dict(linewidth=0.7, edgecolor='#999999', zorder=2)

    if title:
        # Coloured title band
        ax.add_patch(patches.Rectangle(
            (x, y_top), w, CARD_H_HDR,
            facecolor=header_color, **bdr))
        ax.text(x + w / 2, y_top + CARD_H_HDR / 2,
                _wrap(title, chars),
                ha='center', va='center',
                fontsize=6.2, fontweight='bold',
                color='white', linespacing=1.15, zorder=3)
        # White name band
        ax.add_patch(patches.Rectangle(
            (x, y_top + CARD_H_HDR), w, h_nam,
            facecolor='white', **bdr))
        ax.text(x + w / 2, y_top + CARD_H_HDR + h_nam / 2,
                name,
                ha='center', va='center',
                fontsize=6.8, color='#2c3e50', zorder=3)
    else:
        # Single full-colour band
        ax.add_patch(patches.Rectangle(
            (x, y_top), w, CARD_H,
            facecolor=header_color, **bdr))
        ax.text(x + w / 2, y_top + CARD_H / 2,
                _wrap(name, chars),
                ha='center', va='center',
                fontsize=7, fontweight='bold',
                color='white', linespacing=1.15, zorder=3)


def _vl(ax, x, y1, y2):
    ax.plot([x, x], [y1, y2],
            color=EDGE_CLR, lw=EDGE_LW, zorder=1, solid_capstyle='butt')


def _hl(ax, x1, x2, y):
    ax.plot([x1, x2], [y, y],
            color=EDGE_CLR, lw=EDGE_LW, zorder=1, solid_capstyle='butt')


def edge_single(ax, px, py_bot, cx, cy_top):
    """Straight vertical or L-shaped orthogonal edge."""
    if abs(px - cx) < 0.001:
        _vl(ax, px, py_bot, cy_top)
    else:
        mid = (py_bot + cy_top) / 2
        _vl(ax, px, py_bot, mid)
        _hl(ax, px, cx, mid)
        _vl(ax, cx, mid, cy_top)


def edge_T(ax, px, py_bot, cxs, cy_top):
    """T-junction: one parent -> many children at the same y level."""
    mid = (py_bot + cy_top) / 2
    _vl(ax, px, py_bot, mid)
    _hl(ax, min(cxs), max(cxs), mid)
    for cx in cxs:
        _vl(ax, cx, mid, cy_top)


# ── Leaf grid renderer ────────────────────────────────────────────────────────

def render_leaf_grid(ax, dir_cx, dir_bot, reports, leaf_color):
    """
    Draw the 2-column leaf grid for one director and all its connector edges.

    Layout rules (matching the reference image):
      1 report  -> single card, centered below director
      2 reports -> side by side (row 0, both columns)
      3+ reports -> 2-column grid; even index = left col, odd = right col;
                    odd total -> left col one longer; last lone card is tall=True
    """
    n = len(reports)
    if n == 0:
        return

    grid_top = dir_bot + LEVEL_GAP

    # ── 1 report: single centred card ─────────────────────────────────────────
    if n == 1:
        cx = dir_cx
        draw_card(ax, cx - CARD_W / 2, grid_top, CARD_W,
                  reports[0]['name'], title=reports[0].get('title'),
                  header_color=leaf_color)
        edge_single(ax, dir_cx, dir_bot, cx, grid_top)
        return

    # ── 2+ reports: 2-column grid ──────────────────────────────────────────────
    is_odd_multi = (n % 2 == 1) and (n >= 3)
    left_x  = dir_cx - SUBTREE_W / 2
    right_x = left_x + CARD_W + COL_GAP
    left_cx  = left_x  + CARD_W / 2
    right_cx = right_x + CARD_W / 2

    # Draw cards
    for i, r in enumerate(reports):
        row    = i // 2
        col    = i % 2
        is_tall = is_odd_multi and (i == n - 1)
        card_x  = left_x if col == 0 else right_x
        card_y  = grid_top + row * (CARD_H + ROW_GAP)
        draw_card(ax, card_x, card_y, CARD_W,
                  r['name'], title=r.get('title'),
                  header_color=leaf_color, tall=is_tall)

    # Director -> T-bar -> tops of both columns
    edge_T(ax, dir_cx, dir_bot, [left_cx, right_cx], grid_top)

    # Vertical chains within each column (connecting consecutive rows)
    rows_l = _leaf_rows(n)
    rows_r = n // 2
    for r in range(rows_l - 1):
        y1 = grid_top + r * (CARD_H + ROW_GAP) + CARD_H
        y2 = grid_top + (r + 1) * (CARD_H + ROW_GAP)
        _vl(ax, left_cx, y1, y2)
    for r in range(rows_r - 1):
        y1 = grid_top + r * (CARD_H + ROW_GAP) + CARD_H
        y2 = grid_top + (r + 1) * (CARD_H + ROW_GAP)
        _vl(ax, right_cx, y1, y2)


# ── Main chart builder ────────────────────────────────────────────────────────

def build_chart(org_data, output_file='org_chart'):
    """
    Render and save the org chart as <output_file>.png.
    Expects: root -> one VP -> N directors -> leaf reports.
    """
    root = org_data
    vp   = root['reports'][0]
    dirs = vp.get('reports', [])
    n_d  = len(dirs)

    # ── Geometry ────────────────────────────────────────────────────────────
    # Total chart width driven by director columns
    total_w    = n_d * SUBTREE_W + (n_d - 1) * DIR_GAP
    # CEO/VP cards span the centre two director columns
    top_card_w = SUBTREE_W * 2 + DIR_GAP

    max_leaf_h = max((leaf_grid_h(len(d.get('reports', []))) for d in dirs),
                     default=0)
    total_h = (0.30          # top margin
               + CARD_H      # CEO
               + LEVEL_GAP
               + CARD_H      # VP
               + LEVEL_GAP
               + CARD_H      # directors row
               + LEVEL_GAP
               + max_leaf_h  # leaf grids
               + 0.30)       # bottom margin

    # ── Figure setup ─────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(total_w + 0.4, total_h))
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    ax.invert_yaxis()   # y=0 is top; y increases downward
    ax.axis('off')
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    chart_cx = total_w / 2

    # ── CEO card ──────────────────────────────────────────────────────────────
    ceo_top = 0.30
    ceo_x   = chart_cx - top_card_w / 2
    draw_card(ax, ceo_x, ceo_top, top_card_w,
              root['name'], title=root.get('title'),
              header_color=root.get('color', '#2c5282'))
    ceo_bot = ceo_top + CARD_H

    # ── VP card ───────────────────────────────────────────────────────────────
    vp_top = ceo_bot + LEVEL_GAP
    vp_x   = chart_cx - top_card_w / 2
    draw_card(ax, vp_x, vp_top, top_card_w,
              vp['name'], title=vp.get('title'),
              header_color=vp.get('color', '#6b4fa6'))
    vp_bot = vp_top + CARD_H
    edge_single(ax, chart_cx, ceo_bot, chart_cx, vp_top)

    # ── Director row ──────────────────────────────────────────────────────────
    dir_top = vp_bot + LEVEL_GAP
    dir_bot = dir_top + CARD_H
    dir_cxs = []

    for i, d in enumerate(dirs):
        x0   = i * (SUBTREE_W + DIR_GAP)
        d_cx = x0 + SUBTREE_W / 2
        dir_cxs.append(d_cx)
        draw_card(ax, x0, dir_top, SUBTREE_W,
                  d['name'], title=d.get('title'),
                  header_color=d.get('color', '#555555'))

    # VP -> directors
    if len(dir_cxs) == 1:
        edge_single(ax, chart_cx, vp_bot, dir_cxs[0], dir_top)
    else:
        edge_T(ax, chart_cx, vp_bot, dir_cxs, dir_top)

    # ── Leaf grids ────────────────────────────────────────────────────────────
    for i, d in enumerate(dirs):
        render_leaf_grid(ax, dir_cxs[i], dir_bot,
                         d.get('reports', []),
                         d.get('color', '#555555'))

    # ── Save ──────────────────────────────────────────────────────────────────
    out = f'{output_file}.png'
    plt.savefig(out, dpi=DPI, bbox_inches='tight',
                facecolor='white', pad_inches=0.15)
    plt.close(fig)
    print(f'Rendered -> {out}')


# ── Company data ───────────────────────────────────────────────────────────────

COMPANY_ORG = {
    'name': 'Brett McQuail',
    'title': 'President & CEO / Executive Producer',
    'color': '#2c5282',
    'reports': [{
        'name': 'Jeffrey Buson',
        'title': 'Vice President / Executive Producer',
        'color': '#6b4fa6',
        'reports': [
            {
                'name': 'Kevin Piccolo',
                'title': 'Art Director',
                'color': '#e07a3a',
                'reports': [
                    {'name': 'Anh Nguyen',       'title': 'Associate Artist'},
                    {'name': 'Brad Thompson',    'title': 'Concept Artist'},
                    {'name': 'Tom Quang',        'title': 'Artist'},
                    {'name': 'Thor Rosenheimer', 'title': 'Detail Artist'},
                    {'name': 'Todd Parkinson',   'title': 'Assistant Art Director'},
                    {'name': 'Christy Martin',   'title': 'Senior Artist'},
                    {'name': 'Hannah Rochelle',  'title': 'Artists'},
                    {'name': 'Marie LaBelle',    'title': 'Artist'},
                ],
            },
            {
                'name': 'Susan Parkins',
                'title': 'Office Manager',
                'color': '#4a8db7',
                'reports': [
                    {'name': 'Maly Lee', 'title': 'Executive Assistant'},
                ],
            },
            {
                'name': 'Rick Jamison',
                'title': 'Director of Technology / Lead Programmer',
                'color': '#b03060',
                'reports': [
                    {'name': 'Mary Kirkland',  'title': 'Art Technical Lead'},
                    {'name': 'Mike Sherlock',  'title': 'IT Manager'},
                    {'name': 'Scott Beam',     'title': 'Programmers'},
                    {'name': 'Anna Basie',     'title': 'Senior Programmer'},
                    {'name': 'Emilie Smith',   'title': 'Technical Writer'},
                    {'name': 'Nicholas Poe',   'title': 'Web Content Developer'},
                ],
            },
            {
                'name': 'Dave Gillerman',
                'title': 'Director of Operations / Producer',
                'color': '#7d8c9a',
                'reports': [
                    {'name': 'Vincent Forwards',  'title': 'Assistant Producer'},
                    {'name': 'Matt Cronkite',     'title': 'Senior Producer'},
                    {'name': 'Justin Hagan',      'title': 'Associate Game Designer'},
                    {'name': 'Son Lee',           'title': 'Game Designer'},
                    {'name': 'Shaun Burke',       'title': 'Senior Game Designer'},
                    {'name': 'Darrell Bickford',  'title': 'Game Designer'},
                    {'name': 'Jim Clover',        'title': 'Senior Game Designer'},
                    {'name': 'Amanda Elam',       'title': 'Game Designer'},
                    {'name': 'Marc Bowens',       'title': 'Associate Game Designer'},
                ],
            },
        ],
    }],
}


build_chart(COMPANY_ORG, output_file=r'C:\Users\senderak\Desktop\test_final')