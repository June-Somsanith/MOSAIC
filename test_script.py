import torch
from app.services.ai_tagger import AITaggerServices

# Abstract snippet from NASA OSDR
test_abstract = (
    "In this study, Arabidopsis thaliana seeds were exposed to chronic gamma radiation "
    "during a 24-day growth period on the ISS. Results indicate significant DNA damage "
    "and activation of repair pathways compared to ground controls."
)

candidate_labels = ["Radiation", "Microgravity", "Oxidative Stress", "Immune Response"]

# Differentn asks of AI
test_templates = [
    "This text is about {}.",
    "The primary biological stressor in this spaceflight study is {}.",
    "This research investigates the cellular response to {}."
]

def run_tuning():
    print("STARTING HYPOTHESIS TUNING")

    try:
        classifier = AITaggerServices.get_classifier()

        for template in test_templates:
            print(f"\n[Testing Template]: '{template}'")

            # run raw classifier to compare scores
            results = classifier(
                test_abstract,
                candidate_labels,
                hypothesis_template = template,
                multi_label = True
            )

            # Sort and print

            paired_results = sorted(
                zip(results['labels'], results['scores']),
                key = lambda x: x[1],
                reverse = True
            )

            for label, score in paired_results:
                print(f" > {label:20}: {score:.4f}")

    except Exception as e:
        print(f"An error occured: {e}")

if __name__ == "__main__":
    run_tuning()