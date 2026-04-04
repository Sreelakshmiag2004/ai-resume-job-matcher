from sentence_transformers import SentenceTransformer, util
import pandas as pd
import re

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

DEVOPS_KEYWORDS = {
    "docker", "kubernetes", "k8s", "jenkins", "terraform", "ansible", 
    "aws", "azure", "gcp", "cicd", "linux", "ubuntu", "cloud", "devops", 
    "sre", "pipeline", "github", "gitlab", "monitoring"
}

FRONTEND_KEYWORDS = {
    "react", "javascript", "typescript", "html", "css", "frontend", 
    "redux", "nextjs", "angular", "vue", "tailwind"
}

BACKEND_KEYWORDS = {
    "nodejs", "express", "django", "flask", "backend", "api", 
    "mongodb", "mysql", "postgresql", "sql"
}

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'node\.js|nodejs?', 'nodejs', text)
    text = re.sub(r'next\.js|nextjs?', 'nextjs', text)
    text = re.sub(r'ci[-_/]cd|cicd?', 'cicd', text)
    words = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text)
    return set(words)

def detect_domain(resume_text):
    resume_words = normalize_text(resume_text)
    
    devops_score = len(resume_words & DEVOPS_KEYWORDS)
    frontend_score = len(resume_words & FRONTEND_KEYWORDS)
    backend_score = len(resume_words & BACKEND_KEYWORDS)
    
    scores = {"devops": devops_score, "frontend": frontend_score, "backend": backend_score}
    domain = max(scores, key=scores.get)
    
    print(f"🔍 Resume domain: {domain} (D:{devops_score}, F:{frontend_score}, B:{backend_score})")
    return domain

def fuzzy_keyword_match(resume_text, job_text, keywords):
    """Fuzzy matching - checks if ANY keyword exists in EITHER text"""
    resume_lower = resume_text.lower()
    job_lower = job_text.lower()
    
    matches = 0
    for kw in keywords:
        if kw in resume_lower or kw in job_lower:
            matches += 1
    
    score = matches / max(len(keywords), 1)
    return min(score * 1.5, 1.0)  # Boost keywords

def get_keyword_score(resume_text, job_text, resume_domain):
    if resume_domain == "devops":
        keywords = DEVOPS_KEYWORDS
    elif resume_domain == "frontend":
        keywords = FRONTEND_KEYWORDS
    else:
        keywords = BACKEND_KEYWORDS
    
    score = fuzzy_keyword_match(resume_text, job_text, keywords)
    return score

def title_boost(title, resume_domain):
    title_lower = title.lower()
    boosts = {
        "devops": ["devops", "sre", "cloud", "infrastructure"],
        "frontend": ["frontend", "ui", "react", "front-end"],
        "backend": ["backend", "api"]
    }
    
    boost_kws = boosts.get(resume_domain, [])
    matches = sum(1 for kw in boost_kws if kw in title_lower)
    return min(matches * 0.2, 0.4)

def rank_jobs_by_similarity(resume_text, jobs_df):
    print("🤖 Computing embeddings...")
    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    resume_domain = detect_domain(resume_text)
    
    results = []
    for _, row in jobs_df.iterrows():
        job_text = f"{row['title']} {row['description']}"
        job_embedding = model.encode(job_text, convert_to_tensor=True)
        
        semantic_score = util.cos_sim(resume_embedding, job_embedding).item()
        keyword_score = get_keyword_score(resume_text, job_text, resume_domain)
        title_boost_score = title_boost(row['title'], resume_domain)
        
        final_score = 0.6 * semantic_score + 0.3 * keyword_score + 0.1 * title_boost_score
        
        results.append({
            'title': row['title'],
            'company': row['company'],
            'link': row['link'],
            'semantic_score': round(semantic_score, 3),
            'keyword_score': round(keyword_score, 3),
            'title_boost': round(title_boost_score, 3),
            'final_score': round(final_score, 3)
        })
    
    df = pd.DataFrame(results).sort_values('final_score', ascending=False)
    print(f"\n🏆 Top 5 (domain: {resume_domain}):")
    print(df[['title', 'final_score', 'keyword_score', 'title_boost']].head())
    return df