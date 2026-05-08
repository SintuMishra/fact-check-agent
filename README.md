# Fact-Check Agent

A Streamlit web app that extracts factual claims from uploaded PDFs and verifies them against live web sources.

- Live App: https://fact-check-agent-ai.streamlit.app/
- GitHub Repository: https://github.com/SintuMishra/fact-check-agent

## Overview

This project was built as part of a company assessment focused on automated PDF fact-checking.

The problem is straightforward: marketing decks, research summaries, and internal reports often contain claims that sound credible but may be outdated, overstated, or simply wrong. That is especially common with statistics, company milestones, financial figures, product claims, and time-sensitive facts.

This app acts as a first-pass truth layer. It extracts measurable factual claims from an uploaded PDF, looks for live supporting or contradictory evidence on the web, and returns a structured fact-checking report that a reviewer can inspect quickly.

## What the App Does

- Upload a PDF
- Extract claims involving dates, statistics, percentages, financial values, and technical facts
- Search live web sources
- Classify each claim as `Verified`, `Inaccurate`, or `False`
- Show a confidence score, corrected fact, explanation, and sources
- Export a CSV report

## Live Demo

Live App: https://fact-check-agent-ai.streamlit.app/

The deployed app depends on OpenAI and Serper API availability. A demo video is included in the final submission in case API credits, temporary errors, or rate limits affect the live app during review.

## How It Works

1. PDF text extraction  
   The app reads the uploaded PDF and extracts the document text for processing.

2. Claim extraction  
   It identifies factual statements that are concrete enough to verify, especially claims with numbers, dates, percentages, product details, or company facts.

3. Live web verification  
   Each claim is searched against current web results, and the evidence is analyzed to determine whether the claim still holds up.

4. Report generation  
   The app returns a structured output with status, confidence, explanation, corrected fact where relevant, and source links, then allows the results to be exported as CSV.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Streamlit |
| Language | Python |
| PDF Parsing | PyMuPDF, pdfplumber |
| Claim Extraction | OpenAI API |
| Live Search | Serper API |
| Data Export | pandas CSV |

Additional libraries used in the project include `requests` and `python-dotenv`.

## Project Structure

```text
app.py
utils/pdf_extractor.py
utils/claim_extractor.py
utils/verifier.py
utils/report_generator.py
utils/helpers.py
requirements.txt
packages.txt
.env.example
README.md
```

## Screenshots

Screenshots can be added here for the final assessment submission if needed:

- Home screen / upload view
- Claim verification results view
- CSV export example

## Local Setup

```bash
git clone https://github.com/SintuMishra/fact-check-agent.git
cd fact-check-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

After copying `.env.example`, add your own API keys to `.env`.

## Environment Variables

The app expects the following values:

```bash
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key
```

Notes:

- `OPENAI_API_KEY` is used for claim extraction and verification analysis
- `SERPER_API_KEY` is used for live web search results
- Do not commit `.env` to GitHub

For local development, the app reads from `.env`. For Streamlit Cloud deployment, the same values should be added in the app's Secrets settings.

## Streamlit Cloud Deployment

1. Push the repository to GitHub
2. Create a new app on Streamlit Cloud
3. Select repo: `SintuMishra/fact-check-agent`
4. Branch: `main`
5. Main file: `app.py`
6. Add secrets:

```toml
OPENAI_API_KEY="..."
SERPER_API_KEY="..."
```

7. Deploy

## Example Test Claims

These example claims are useful for checking a mix of `Verified`, `Inaccurate`, and `False` outcomes:

- OpenAI was founded in 2001.
- Google was founded in 1998.
- India GDP grew by 25% in 2025.
- ChatGPT has 10 billion weekly users.
- Microsoft acquired LinkedIn in 2016.

They are helpful because some should verify cleanly, while others should trigger corrections or contradictions from current sources.

## Limitations

- Web search results can vary over time, so outputs may change as source rankings and published evidence change.
- Some claims still need manual review when evidence is weak, conflicting, or too context-dependent.
- The system is a fact-checking assistant, not a final legal, compliance, or editorial authority.
- API rate limits or credit limits may affect long documents or repeated testing sessions.

## Future Improvements

- More source credibility scoring
- Better support for scanned PDFs and OCR
- PDF report export
- Batch document processing
- Domain-specific verification modes

## Assessment Deliverables

- Deployed App: https://fact-check-agent-ai.streamlit.app/
- GitHub Repository: https://github.com/SintuMishra/fact-check-agent

## Final Note

This project is designed to speed up first-pass review, not replace human judgment. Its value is in surfacing checkable claims quickly, attaching live evidence, and making document review more systematic during assessment or internal validation workflows.
