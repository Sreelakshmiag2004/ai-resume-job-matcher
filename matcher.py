from sentence_transformers import SentenceTransformer, util
import pandas as pd

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

DEVOPS_KEYWORDS = {
    "docker", "kubernetes", "jenkins", "terraform", "ansible",
    "aws", "azure", "gcp", "ci/cd", "linux", "monitoring",
    "prometheus", "grafana", "devops", "cloud", "pipeline"
}

FRONTEND_KEYWORDS = {
    "react", "javascript", "typescript", "html", "css",
    "frontend", "redux", "next.js", "ui", "web"
}

BACKEND_KEYWORDS = {
    "node.js", "express", "django", "flask", "spring",
    "backend", "api", "mongodb", "mysql", "postgresql"
}


def get_keyword_overlap(resume_text, job_text, keyword_set):
    resume_words = set(resume_text.lower().split())
    job_words = set(job_text.lower().split())
    return len((resume_words & job_words) & keyword_set) / max(len(keyword_set), 1)


def detect_resume_domain(resume_text):
    text = resume_text.lower()
    devops_score = sum(1 for kw in DEVOPS_KEYWORDS if kw in text)
    frontend_score = sum(1 for kw in FRONTEND_KEYWORDS if kw in text)
    backend_score = sum(1 for kw in BACKEND_KEYWORDS if kw in text)

    scores = {
        "devops": devops_score,
        "frontend": frontend_score,
        "backend": backend_score
    }

    return max(scores, key=scores.get)


def rank_jobs_by_similarity(resume_text, jobs_df):
    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    resume_domain = detect_resume_domain(resume_text)

    final_scores = []

    for _, row in jobs_df.iterrows():
        job_text = f"{row['title']} {row['description']}"
        job_embedding = model.encode(job_text, convert_to_tensor=True)

        semantic_score = util.cos_sim(resume_embedding, job_embedding).item()

        devops_overlap = get_keyword_overlap(resume_text, job_text, DEVOPS_KEYWORDS)
        frontend_overlap = get_keyword_overlap(resume_text, job_text, FRONTEND_KEYWORDS)
        backend_overlap = get_keyword_overlap(resume_text, job_text, BACKEND_KEYWORDS)

        if resume_domain == "devops":
            keyword_score = devops_overlap
        elif resume_domain == "frontend":
            keyword_score = frontend_overlap
        else:
            keyword_score = backend_overlap

        final_score = (0.7 * semantic_score) + (0.3 * keyword_score)

        final_scores.append({
            "title": row["title"],
            "company": row["company"],
            "link": row["link"],
            "semantic_score": semantic_score,
            "keyword_score": keyword_score,
            "final_score": final_score
        })

    ranked_df = pd.DataFrame(final_scores)
    ranked_df = ranked_df.sort_values(by="final_score", ascending=False)
    return ranked_df