import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai_tagger import AITaggerServices

def run_batch_check():
    print("\n" + "="*60)
    print("MOSAIC: AI BATCH HEALTH CHECK (5 SCENARIOS)")
    print("="*60)

    # Scenarios representing hte bredth of NASA OSDR data
    
    scenarios = [
        # 1. Radiation (tuned for; GLDS-379)
        "In the Rodent Research Reference Mission (RRRM-1), forty female BALB/cAnNTac mice "
        "were flown on the International Space Station. This dataset features ribodepleted "
        "total RNA-seq data from livers dissected from young and old mice to assess "
        "differences in outcomes due to age and spaceflight effects.",

        # 2. Muscle atrophy (GLDS-665)
        "The objective of the Rodent Research-23 mission (RR-23) was to better understand the "
        "effects of spaceflight on the eyes, specifically on the arteries, veins, and lymphatic "
        "vessels. This dataset features transcriptional profiling of right extensor digitorum "
        "longus muscle from mice maintained in microgravity for 38 days.",

        # 3. Plant biology (GLDS-137)
        "The Rodent Research-3 (RR-3) mission studied the loss of muscle and bone mass in "
        "female BALB/c mice housed on the ISS for 42 days. This specific dataset features "
        "multi-omic analysis (transcriptomic, proteomic, and epigenomic) of liver tissues "
        "to investigate lipid dysregulation and metabolic shifts in spaceflight.",

        # 4. Rotifers in Space (OSD-824)
        "This study analyzes transcriptomic changes in the bdelloid rotifer Adineta vaga "
        "aboard the ISS. Results revealed significant differential expression in 18.61% "
        "of genes, including those involved in DNA repair and Horizontal Gene Transfer (HGT), "
        "suggesting these foreign genes play a role in adaptability to microgravity.",

        # 5. Ground Study (OSD-782)
        "To characterize the response to low-dose ionizing radiation (IR) as might occur "
        "during spaceflight, Arabidopsis thaliana plants were exposed to acute gamma "
        "radiation (10 cGy and 100 cGy). Results indicate a coordinated response through "
        "induction of the ethylene signaling pathway and abiotic stress genes.",
    ]

    print(f"Sending {len(scenarios)} abstracts to the GPU for batch processing...")

    try:
        # passing hte list to tag_text

        results = AITaggerServices.tag_text(scenarios)

        for i, res in enumerate(results):
            print(f"\n[Scenario {i + 1}]: {scenarios[i][:70]}...")
            print(f" > Top Tag: {res['top_tag']}")
            print(f" > Confirmed Tags (Score >= 0.60): {res['tags']}")

            if not res['tags']:
                print(" ! WARNING: No tags passed the 0.60 threshold.")

    except Exception as e:
        print(f"Batch processing failed: {e}")

if __name__ == "__main__":
    run_batch_check()