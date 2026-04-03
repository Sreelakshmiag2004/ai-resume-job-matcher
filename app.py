import os
import pandas as pd
import sys  # FIXED: Moved to TOP level

from resume_parser import extract_resume_text
from jobs_loader import load_jobs
from matcher import rank_jobs_by_similarity
from whatsapp_notifier import send_whatsapp_message


def validate_csv(csv_path):
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return False

    try:
        df = pd.read_csv(csv_path)

        if df.empty:
            print("❌ CSV is empty")
            return False

        required_cols = ["title", "company", "semantic_score", "keyword_score", "final_score"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"❌ Missing columns in CSV: {missing_cols}")
            return False

        print(f"✅ CSV validated successfully: {len(df)} rows found")
        return True

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False


def main():
    # Command line argument support (NOW WORKS!)
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
        print(f"🎯 Using command line resume: {resume_path}")
    else:
        resume_path = "data/resume.pdf"
        print("📄 Using default resume: data/resume.pdf")

    jobs_path = "data/jobs.csv"
    output_path = "output/ranked_jobs.csv"

    print(f"\n📁 File paths:")
    print(f"   Resume: {resume_path}")
    print(f"   Absolute: {os.path.abspath(resume_path)}")
    print(f"   Exists: {os.path.exists(resume_path)}")
    print(f"   Jobs: {jobs_path}")

    if not os.path.exists(resume_path):
        print(f"❌ Resume file not found: {resume_path}")
        return

    if not os.path.exists(jobs_path):
        print(f"❌ Jobs CSV file not found: {jobs_path}")
        return

    print("\n🔍 Extracting resume text...")
    resume_text = extract_resume_text(resume_path)
    
    print(f"\n📝 Resume extraction results:")
    print(f"   Text length: {len(resume_text)} characters")
    print(f"   First 300 chars: {repr(resume_text[:300])}")
    print(f"   Preview: {resume_text[:100]}...")

    print("\n⚙️ Loading jobs...")
    jobs_df = load_jobs(jobs_path)

    print("\n🤖 Ranking jobs...")
    ranked_jobs = rank_jobs_by_similarity(resume_text, jobs_df)

    print("\n🏆 Top 10 ranked jobs:")
    print(ranked_jobs[["title", "company", "semantic_score", "keyword_score", "final_score"]].head(10))

    os.makedirs("output", exist_ok=True)
    ranked_jobs.to_csv(output_path, index=False)

    print(f"\n💾 Saved successfully to {output_path}")

    if not validate_csv(output_path):
        print("⚠️ CSV validation failed. Stopping before notifications.")
        return

    top_jobs = ranked_jobs.head(3)

    print("\n📱 Top 3 WhatsApp messages (PREVIEW):")
    for i, (_, row) in enumerate(top_jobs.iterrows(), 1):
        message = (
            f"Top #{i} Job Match\n"
            f"Role: {row['title']}\n"
            f"Company: {row['company']}\n"
            f"Semantic: {row['semantic_score']:.3f}\n"
            f"Keyword: {row['keyword_score']:.3f}\n"
            f"Final: {row['final_score']:.3f}\n"
            f"Link: {row['link']}"
        )
        print(f"[{i}] {message[:120]}...")
        print("-" * 60)

    print("\n✅ Pipeline complete! CSV validated. Ready for WhatsApp (disabled).")


if __name__ == "__main__":
    main()