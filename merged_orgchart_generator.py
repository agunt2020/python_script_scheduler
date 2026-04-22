import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import html

# --- CONFIGURATION ---
SHAREPOINT_FOLDER = r"C:\Users\libsystems\american.edu\Python Script Scheduler - Documents"
DIRECTORY_FILE = os.path.join(SHAREPOINT_FOLDER, "library_staff_directory.csv")
ORG_DATA_FILE = os.path.join(SHAREPOINT_FOLDER, "Library Org Chart - Library Data.csv")

DEPT_HEADS = [
    {"name": "Leslie Nellis", "color": "#2c3e50"},  # Dark Slate
    {"name": "Robert Alonso", "color": "#004a99"},  # AU Blue
    {"name": "Michael Piller", "color": "#e67e22"},  # Orange
    {"name": "Robert Kelshian", "color": "#27ae60"},  # Green
    {"name": "Gwendolyn Reece", "color": "#8e44ad"},  # Purple
    {"name": "Alayne Mundt", "color": "#c0392b"}  # Red
]

# Card Dimensions (Inches)
CARD_W = 2.0
CARD_H_HDR = 0.4  # Title/Dept band
CARD_H_NAM = 0.5  # Name/Email band
CARD_H = CARD_H_HDR + CARD_H_NAM


def build_hierarchy(manager_name, df_org, staff_info):
    """Recursively builds a nested dictionary for the Matplotlib plotter."""
    node_name = manager_name.split(' - ')[0].strip()
    info = staff_info.get(node_name, {})

    node = {
        'name': node_name,
        'title': info.get('Title', 'Staff'),
        'email': info.get('Email', ''),
        'reports': []
    }

    # Find anyone who reports to this person
    reports = df_org[df_org['Manager'].str.contains(manager_name, na=False, case=False)]
    for _, row in reports.iterrows():
        child_full = str(row['Full name'])
        node['reports'].append(build_hierarchy(child_full, df_org, staff_info))

    return node


def draw_card(ax, x, y, name, title, email, color):
    """Draws the professional header-band style card."""
    # Header (Title)
    ax.add_patch(patches.Rectangle((x, y + CARD_H_NAM), CARD_W, CARD_H_HDR, facecolor=color, edgecolor='none'))
    # Body (Name/Email)
    ax.add_patch(patches.Rectangle((x, y), CARD_W, CARD_H_NAM, facecolor='white', edgecolor=color, linewidth=1))

    # Text
    ax.text(x + CARD_W / 2, y + CARD_H_NAM + CARD_H_HDR / 2, title, color='white',
            ha='center', va='center', fontsize=7, weight='bold', wrap=True)
    ax.text(x + CARD_W / 2, y + 0.3, name, color='black',
            ha='center', va='center', fontsize=9, weight='bold')
    ax.text(x + CARD_W / 2, y + 0.12, email, color='#555555',
            ha='center', va='center', fontsize=7)


def plot_dept(node, x, y, ax, color, level_gap=1.2):
    """Simple vertical recursive plotter."""
    draw_card(ax, x, y, node['name'], node['title'], node['email'], color)

    if node['reports']:
        child_y = y - level_gap
        # Center children under parent
        total_width = len(node['reports']) * (CARD_W + 0.5)
        start_x = x - (total_width / 4)

        for i, report in enumerate(node['reports']):
            child_x = start_x + (i * (CARD_W + 0.5))
            # Draw connection line
            ax.plot([x + CARD_W / 2, child_x + CARD_W / 2], [y, child_y + CARD_H], color='#cccccc', lw=1, zorder=0)
            plot_dept(report, child_x, child_y, ax, color)


def generate_charts():
    # Load Data
    df_dir = pd.read_csv(DIRECTORY_FILE)
    df_org = pd.read_csv(ORG_DATA_FILE)
    staff_info = df_dir.set_index('Name').to_dict('index')

    for head in DEPT_HEADS:
        name = head['name']
        color = head['color']

        # 1. Build Data Structure
        hierarchy = build_hierarchy(name, df_org, staff_info)

        # 2. Setup Plot
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_xlim(-5, 15)
        ax.set_ylim(-10, 2)
        ax.axis('off')

        # 3. Draw
        plot_dept(hierarchy, 5, 0, ax, color)

        # 4. Save
        out_file = os.path.join(SHAREPOINT_FOLDER, f"Professional_OrgChart_{name.replace(' ', '_')}.png")
        plt.savefig(out_file, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Generated: {out_file}")


if __name__ == "__main__":
    generate_charts()