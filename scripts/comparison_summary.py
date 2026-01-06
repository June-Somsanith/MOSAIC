import requests
import pandas as pd
from tabulate import tabulate
import os

BASE_URL = "http://127.0.0.1:8000"

def generate_comparison_report():
    print("\n" + "="*60)
    print("MOSAIC: COMPARATIVE BIOLOGY REPORT")
    print("=" * 60)

    study_ids = ["OSD-347", "OSD-245", "OSD-38", "OSD-37"]

    endpoint = f"{BASE_URL}/studies/batch_process"

    try:
        response = requests.post(endpoint, json=study_ids, timeout = 120)
        response.raise_for_status()
        data = response.json()

        report_data = []

        for study in data['studies']:
            sid = study.get('source_id')
            organism = study.get('organism', ["Unknown"])[0]
            ai = study.get('ai_analysis', {})
            top_tag = ai.get ('top_tag', "None")

            # We need to convert tags dictionary into a readable string

            tags_dict = ai.get('tags', {})
            tag_summary = ", ".join([f"{k} ({v})" for k, v in tags_dict.items()])
            if not tag_summary:
                tag_summary = "No tags above 0.50 threshold"

            report_data.append({
                "ID": sid,
                "Organism": organism,
                "Primary Focus (Top Tag)": top_tag, # May want ot rephrase this for genelab presentaions
                "Confident Indentifiers (>0.50)": tag_summary
            })

        # 2. Create DataFrames for printing

        df = pd.DataFrame(report_data)

        print("\n### Cross-Species Analysis Table")
        print(tabulate(df, headers = 'keys', tablefmt = 'fancy_grid', showindex = False)) # Change to any type of grid format: pretty, simple_outline, fancy_outline, etc.

        # Save to CSV
        output_path = "outputs/comparison_report.csv"
        os.makedirs("outputs", exist_ok = True)
        df.to_csv(output_path, index = False)
        print(f"\n Report saved to: {output_path}")

        # insight generation
        print("\n### System Insights")
        mouse_tags = [d['Primary Focus (Top Tag)'] for d in report_data if "Mus" in d['Organism']]
        rotifer_tags = [d['Primary Focus (Top Tag)'] for d in report_data if "Adineta" in d['Organism']]

        print(f"1. Mouse studies primarily cluster around: {set(mouse_tags)}")
        print(f"2. Rotifer studies primarily cluster around: {set(rotifer_tags)}")

    except Exception as e:
        print(f"Report Generation Error: {e}")

if __name__ == "__main__":
    generate_comparison_report()