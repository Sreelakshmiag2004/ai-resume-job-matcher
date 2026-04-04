import schedule
import time
import pandas as pd
import os
import json
from datetime import datetime
from matcher import rank_jobs_by_similarity
from resume_parser import extract_resume_text
from whatsapp_notifier import send_whatsapp_message
import hashlib

from job_scraper import scrape_linkedin_jobs
from tracker import JobTracker

STATE_FILE = "output/sent_jobs.json"


def load_sent_jobs():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
    except Exception:
        pass
    return set()


def save_sent_jobs(sent_jobs_hash):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(list(sent_jobs_hash), f)


sent_jobs_hash = load_sent_jobs()


def job_id(row):
    return hashlib.md5(
        f"{row['title']}{row['company']}{row['link']}".encode()
    ).hexdigest()


def check_new_jobs():
    global sent_jobs_hash

    print(f"\n⏰ Hourly job check: {datetime.now().strftime('%H:%M:%S')}")

    try:
        resume_path = "data/resume.pdf"
        if not os.path.exists(resume_path):
            print("❌ Missing data/resume.pdf")
            return

        print(f"[DEBUG] Resume parsed from: {resume_path}")
        resume_text = extract_resume_text(resume_path)
        print(f"[DEBUG] Extracted text length: {len(resume_text)}")

        print("🌐 Scraping fresh jobs...")
        fresh_jobs = scrape_linkedin_jobs()

        if fresh_jobs is None or fresh_jobs.empty:
            print("ℹ️ No fresh jobs scraped")
            return

        print("[DEBUG] Scraped columns:", fresh_jobs.columns.tolist())
        print("[DEBUG] Fresh jobs preview:")
        print(fresh_jobs.head())

        fresh_jobs.columns = fresh_jobs.columns.map(lambda x: str(x).strip().lower())

        fresh_jobs = fresh_jobs.rename(columns={
            "job_title": "title",
            "company_name": "company",
            "url": "link",
            "job_link": "link"
        })

        required_cols = ["title", "company", "link"]
        missing_cols = [col for col in required_cols if col not in fresh_jobs.columns]

        if missing_cols:
            print(f"❌ Missing required columns: {missing_cols}")
            print(f"Available columns: {fresh_jobs.columns.tolist()}")
            return

        if "description" not in fresh_jobs.columns:
            fresh_jobs["description"] = (
                fresh_jobs["title"].fillna("").astype(str) + " at " +
                fresh_jobs["company"].fillna("").astype(str)
            )

        os.makedirs("data", exist_ok=True)
        fresh_jobs.to_csv("data/fresh_jobs.csv", index=False)
        print(f"✅ Scraped {len(fresh_jobs)} fresh jobs")

        print("🤖 Computing embeddings...")
        ranked_jobs = rank_jobs_by_similarity(resume_text, fresh_jobs)

        if ranked_jobs is None or ranked_jobs.empty:
            print("ℹ️ No ranked jobs available")
            return

        top_new = ranked_jobs.head(5)

        print("\n🏆 Top 5 fresh jobs:")
        cols_to_show = [col for col in ["title", "company", "final_score"] if col in top_new.columns]
        if cols_to_show:
            print(top_new[cols_to_show].round(3).to_string(index=False))
        else:
            print("ℹ️ No displayable columns found in ranked jobs")

        new_messages_sent = 0
        tracker = JobTracker()

        for _, row in top_new.iterrows():
            job_hash = job_id(row)

            if job_hash not in sent_jobs_hash:
                message = (
                    f"🆕 FRESH Job Match!\n\n"
                    f"📋 {row['title']}\n"
                    f"🏢 {row['company']}\n"
                    f"⭐ Score: {row['final_score']:.3f}\n"
                    f"🔗 {row['link']}"
                )

                print(f"\n📱 Sending: {row['title']}")
                success = send_whatsapp_message(message)

                if success:
                    sent_jobs_hash.add(job_hash)
                    save_sent_jobs(sent_jobs_hash)
                    new_messages_sent += 1

                    tracker.add_application(
                        row["title"],
                        row["company"],
                        row["link"]
                    )
                    print(f"✅ Sent + TRACKED: {row['title']}")
                else:
                    print(f"❌ Failed to send: {row['title']}")
            else:
                print(f"⏭️ Already sent: {row['title']}")

        save_sent_jobs(sent_jobs_hash)
        print(f"✅ Sent {new_messages_sent} alerts | Total tracked: {len(sent_jobs_hash)}")

    except Exception as e:
        print(f"❌ Error: {e}")

def daily_report():
    print(f"\n📊 Daily Report: {datetime.now().strftime('%Y-%m-%d')}")
    tracker = JobTracker()
    due = tracker.get_due_followups()

    if not due.empty:
        message = "📋 Follow-ups due:\n\n" + "\n".join(
            [f"• {row['job_title']} @ {row['company']}" for _, row in due.iterrows()]
        )
        send_whatsapp_message(message)
    else:
        print("ℹ️ No follow-ups due today")

    print("✅ Daily report complete")


def main():
    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    print("🚀 ENHANCED Job Scheduler (Scrape + Track + Alert)")
    print("🌐 Auto-scrapes fresh jobs hourly")
    print("📊 Auto-tracks applications")
    print("📱 WhatsApp alerts + follow-ups")

    check_new_jobs()
    schedule.every(1).minutes.do(check_new_jobs)
    #schedule.every().hour.do(check_new_jobs)
    schedule.every().day.at("09:00").do(daily_report)

    print("\n✅ FULL Step 3 system running!")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()