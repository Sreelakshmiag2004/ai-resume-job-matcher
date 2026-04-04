import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


class JobTracker:
    def __init__(self):
        self.db_path = Path("output/applications.csv")
        self.columns = [
            "job_title",
            "company",
            "link",
            "applied_date",
            "status",
            "last_contact",
            "next_action",
            "priority",
        ]
        self.load_db()

    def load_db(self):
        try:
            if self.db_path.exists():
                self.df = pd.read_csv(self.db_path)
            else:
                self.df = pd.DataFrame(columns=self.columns)
        except Exception:
            self.df = pd.DataFrame(columns=self.columns)

    def add_application(self, job_title, company, link, priority="medium"):
        self.load_db()

        new_app = {
            "job_title": job_title,
            "company": company,
            "link": link,
            "applied_date": datetime.now().isoformat(),
            "status": "Applied",
            "last_contact": "",
            "next_action": "Follow up in 7 days",
            "priority": priority,
        }

        self.df = pd.concat([self.df, pd.DataFrame([new_app])], ignore_index=True)
        self.save()
        print(f"✅ Tracked: {job_title} @ {company}")

    def update_status(self, company, status, notes=""):
        self.load_db()

        mask = self.df["company"].astype(str).str.contains(company, case=False, na=False)

        if mask.any():
            self.df.loc[mask, "status"] = status
            self.df.loc[mask, "last_contact"] = datetime.now().isoformat()
            self.df.loc[mask, "next_action"] = notes
            self.save()
            print(f"✅ Updated status for {company} -> {status}")
        else:
            print(f"⚠️ No matching company found for: {company}")

    def get_due_followups(self):
        self.load_db()

        if self.df.empty:
            return self.df

        self.df["applied_date"] = pd.to_datetime(self.df["applied_date"], errors="coerce")

        due = self.df[
            (self.df["status"] == "Applied")
            & (self.df["applied_date"] < datetime.now() - timedelta(days=7))
        ]

        return due

    def save(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(self.db_path, index=False)