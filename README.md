# Fact-Check Agent

Upload a PDF to check factual claims against current web sources.

## What I built

This project is a Streamlit app that:

- accepts a PDF upload
- extracts factual claims from the document
- checks those claims against live web search results
- classifies each claim as `Verified`, `Inaccurate`, or `False`
- shows a confidence score, corrected fact, explanation, and source links
- exports the results as a CSV report

## Why I built it

The assessment asks for a practical way to review factual statements in uploaded documents. PDFs often contain dates, percentages, financial numbers, and product claims that need quick checking. The goal here was to build a tool that helps reviewers move faster while still keeping the output understandable and easy to inspect.

## How it works

1. Upload a PDF in the Streamlit interface.
2. The app extracts text from the file page by page.
3. The claim extraction step identifies measurable factual statements.
4. Each claim is searched against current web sources using Serper.
5. OpenAI analyzes the claim and search evidence together.
6. The app returns a status, confidence score, corrected fact, explanation, and source links.
7. The final report can be downloaded as CSV.

## Assessment alignment

This app covers the requested workflow:

- PDF upload
- factual claim extraction
- live web verification
- status classification: `Verified`, `Inaccurate`, `False`
- corrected fact or fallback message
- explanation for each result
- source links when available
- downloadable report

## Tech stack

- Python
- Streamlit
- OpenAI API
- Serper API
- PyMuPDF
- pdfplumber
- pandas

## Project structure

```text
fact-check-agent/
├── app.py
├── README.md
├── requirements.txt
├── packages.txt
├── .env.example
├── deploy.sh
├── utils/
│   ├── claim_extractor.py
│   ├── helpers.py
│   ├── pdf_extractor.py
│   ├── report_generator.py
│   └── verifier.py
└── sample_outputs/
```

## Local setup

### Prerequisites

- Python 3.10+ recommended
- OpenAI API key
- Serper API key

### Install and run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Then add your own values to `.env`:

```bash
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

The app also supports Streamlit Cloud secrets through `st.secrets`.

## Environment variables

The app expects:

- `OPENAI_API_KEY`
- `SERPER_API_KEY`

These can be provided through either:

- a local `.env` file for development
- Streamlit Cloud secrets for deployment

## Deployment steps

### Streamlit Cloud

1. Push the repository to GitHub.
2. Create a new app in Streamlit Cloud.
3. Set the main file path to `app.py`.
4. Add `OPENAI_API_KEY` and `SERPER_API_KEY` in the app secrets settings.
5. Deploy.

### Notes

- `app.py` is the main entry point.
- No local-only absolute paths are required.
- The app reads secrets from `st.secrets` before falling back to environment variables.

## Security notes

- `.env` is ignored by `.gitignore`.
- `.env.example` contains placeholders only.
- No API keys are hardcoded in the app.
- This README uses placeholder environment values only.

## Limitations

- Results depend on the quality and availability of live web evidence.
- Some claims may need manual review if sources are sparse or conflicting.
- Scanned PDFs without selectable text may be harder to process reliably.
- Very domain-specific claims may need stronger source coverage than a general web search can provide.

## Future improvements

- stronger handling for scanned PDFs and OCR workflows
- better source quality ranking
- richer report formats such as PDF or JSON
- support for batch document processing
- clearer handling of time-sensitive claims

## Submission deliverables

This repository includes:

- the working Streamlit app
- the source code for extraction, verification, and reporting
- deployment files for Streamlit Cloud
- environment variable template
- CSV export support

For the final submission, the expected deliverables are:

- GitHub repository link
- deployed app link
- short demo video

## Final notes

This tool is meant to assist with document review, not replace judgment. It is best used as a first-pass fact-checking workflow that surfaces claims, likely issues, and relevant source links quickly.
