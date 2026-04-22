import pandas as pd
from graphviz import Digraph
import os
import html

# --- CONFIGURATION ---
SHAREPOINT_FOLDER = r"C:\Users\libsystems\american.edu\Python Script Scheduler - Documents"
DIRECTORY_FILE = os.path.join(SHAREPOINT_FOLDER, "library_staff_directory.csv")
ORG_DATA_FILE = os.path.join(SHAREPOINT_FOLDER, "Library Org Chart - Library Data.csv")

DEPT_HEADS = [
    "Leslie Nellis",
    "Robert Alonso",
    "Michael Piller",
    "Robert Kelshian",
    "Gwendolyn Reece",
    "Alayne Mundt"
]

# Ensure Python can find Graphviz
os.environ["PATH"] += os.pathsep + r'C:\Program Files\Graphviz\bin'


def get_all_reports(manager_name, df, gathered_nodes=None):
    if gathered_nodes is None:
        gathered_nodes = set()

    # Matching logic to handle names in "Name - Title" format
    reports = df[df['Manager'].str.contains(manager_name, na=False, case=False)]

    for _, row in reports.iterrows():
        child_name = str(row['Full name']).split(' - ')[0].strip()
        if child_name not in gathered_nodes:
            gathered_nodes.add(child_name)
            get_all_reports(child_name, df, gathered_nodes)
    return gathered_nodes


def create_department_chart(head_name, df_org, staff_info):
    print(f"Generating exact format chart for {head_name}...")

    dept_staff = get_all_reports(head_name, df_org)
    dept_staff.add(head_name)

    # 1. Setup Graphviz Visuals for the "Zip File" Style
    dot = Digraph(format='png')
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.6', ranksep='0.6')

    # Node Style: Sharp corners, specific border color
    dot.attr('node',
             shape='rect',
             style='filled',
             fillcolor='#ffffff',
             color='#2c3e50',  # Dark blue/grey border
             fontname='Helvetica-Bold',
             fontsize='11')

    # Edge Style: Square paths
    dot.attr('edge', color='#7f8c8d', penwidth='1.2', arrowhead='none')

    for _, row in df_org.iterrows():
        child_name = str(row['Full name']).split(' - ')[0].strip()
        manager_name = str(row['Manager']).split(' - ')[0].strip()

        if child_name in dept_staff:
            info = staff_info.get(child_name, {})
            title = html.escape(str(info.get('Title', 'Staff')))
            email = html.escape(str(info.get('Email', '')))

            # 2. HTML Table for specific formatting
            # Header row (Blue text for name), Body row (Grey for title/email)
            label_html = f'''<
                <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3">
                    <TR><TD><B><FONT COLOR="#004a99" POINT-SIZE="12">{html.escape(child_name)}</FONT></B></TD></TR>
                    <TR><TD><FONT COLOR="#2c3e50" POINT-SIZE="10">{title}</FONT></TD></TR>'''

            if email and email != "nan" and email.strip() != "":
                label_html += f'<TR><TD><FONT COLOR="#666666" POINT-SIZE="9">{email}</FONT></TD></TR>'

            label_html += '</TABLE>>'

            dot.node(child_name, label=label_html)

            if manager_name in dept_staff:
                dot.edge(manager_name, child_name)

    output_path = os.path.join(SHAREPOINT_FOLDER, f"OrgChart_{head_name.replace(' ', '_')}")
    dot.render(output_path, cleanup=True)


def main():
    try:
        # Load data
        df_directory = pd.read_csv(DIRECTORY_FILE)
        df_org = pd.read_csv(ORG_DATA_FILE)
        staff_info = df_directory.set_index('Name').to_dict('index')

        for head in DEPT_HEADS:
            create_department_chart(head, df_org, staff_info)

        print("\nAll six charts have been generated in your SharePoint folder.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()