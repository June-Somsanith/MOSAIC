import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def create_stressor_heatmap():
    print("\nGENERATING VISUAL ANALYTICS FOR MOSAIC")

    # 1. Load data

    file_path = "outputs/comparison_report.csv"
    if not os.path.exists(file_path):
        print("Error: Run comparison_summary.py first to generate the CSV")
        return

    df = pd.read_csv(file_path)

    # 2. Bar chart

    plt.figure(figsize = (10,6))
    sns.set_theme(style = "whitegrid")

    ax = sns.countplot(data = df, x = 'Primary Focus (Top Tag)', hue = 'Organism')

    plt.title('MOSAIC: Primary Biological Focus by Organism', fontsize = 15)
    plt.xlabel('AI Classified Stressor', fontsize = 12)
    plt.ylabel('Study Count', fontsize = 12)
    plt.xticks(rotation = 45)

    # 3. Save figure

    output_img = "outputs/stressor_chart.png"
    plt.tight_layout()
    plt.savefig(output_img)
    print(f"SUCCESS: VISUALIZATION SAVED TO {output_img}")

if __name__ == "__main__":
    create_stressor_heatmap()
