import streamlit as st
import pandas as pd
from resume_parser import extract_resume_text
from jobs_loader import load_jobs
from matcher import rank_jobs_by_similarity
import io

st.title("🚀 AI Resume Job Matcher")
st.markdown("Upload resume → Get ranked job matches instantly!")

# File uploaders
resume_file = st.file_uploader("📄 Upload Resume (PDF)", type="pdf")
jobs_file = st.file_uploader("📊 Upload Jobs CSV", type="csv")

if resume_file and jobs_file:
    # Process files
    with st.spinner("Analyzing your resume..."):
        resume_text = extract_resume_text(resume_file)
        jobs_df = pd.read_csv(jobs_file)
        ranked_jobs = rank_jobs_by_similarity(resume_text, jobs_df)
    
    # Display results
    st.success("✅ Job matching complete!")
    st.dataframe(ranked_jobs.head(10), use_container_width=True)
    
    # Download button
    csv = ranked_jobs.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download Ranked Jobs", csv, "ranked_jobs.csv", "text/csv")
    
    # Top 3 highlight
    st.subheader("🏆 Top 3 Matches")
    for i, (_, row) in enumerate(ranked_jobs.head(3).iterrows(), 1):
        st.markdown(f"**#{i}** {row['title']} @ {row['company']} (**{row['final_score']:.3f}**)")

if __name__ == "__main__":
    pass  # Streamlit handles execution