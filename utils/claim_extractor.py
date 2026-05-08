import json
import logging
import re
import tiktoken
from typing import List, Dict, Any
from .helpers import get_openai_client

logger = logging.getLogger(__name__)

class ClaimExtractor:
    """Extracts factual claims from text using OpenAI and regex fallback."""

    def __init__(self):
        self.client = get_openai_client()
        self.model = "gpt-4o-mini"
        self.max_tokens = 4000

    def extract_claims(self, text: str, pages: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        Extract factual claims from text.

        Args:
            text: Full text from PDF
            pages: List of page dictionaries with text

        Returns:
            List of claim dictionaries
        """
        if not text.strip():
            return []

        truncated_text = self._truncate_text(text)
        prompt = self._build_extraction_prompt(truncated_text)

        claims = []
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert fact-checker. Extract every clear factual claim from the text. "
                            "Focus on measurable facts, dates, years, percentages, company events, acquisitions, user counts, revenue, growth, rankings, and other verifiable statements. "
                            "Return only valid JSON."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result = response.choices[0].message.content
            claims = self._parse_claims_response(result)

        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")

        if pages:
            claims = self._add_page_numbers(claims, pages)

        if not claims:
            logger.info("AI extraction returned no claims. Using fallback regex-based extraction.")
            claims = self._fallback_extract_claims(text, pages)

        return claims

    def _truncate_text(self, text: str) -> str:
        encoding = tiktoken.encoding_for_model(self.model)
        tokens = encoding.encode(text)
        if len(tokens) > self.max_tokens:
            return tiktoken.encoding_for_model(self.model).decode(tokens[:self.max_tokens])
        return text

    def _build_extraction_prompt(self, text: str) -> str:
        return f"""
Extract every factual claim from the following text. Include measurable facts that contain:
- years and dates (for example, 1998, 2001, 2025)
- percentages and growth rates (for example, 25%)
- counts and large numbers (for example, 10 billion users)
- company events and acquisitions (for example, founded, acquired)
- revenue, market share, rankings, GDP, user counts, and technical metrics

Do not extract opinions, subjective statements, promotional language, or generic descriptions.

For each claim, return a JSON object with these keys:
- claim: The exact claim text
- claim_type: One of company_event, statistic, growth, financial, demographic, market, date, user_count, or unknown
- page_number: The page number where the claim appears, or null if not available

Return only a JSON array of objects, with no explanatory text.

Text to analyze:
{text}
"""

    def _parse_claims_response(self, response: str) -> List[Dict[str, Any]]:
        cleaned = response.strip()
        if cleaned.startswith('```'):
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        if cleaned.endswith('```'):
            cleaned = re.sub(r'```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        try:
            claims = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse claims JSON: {e}")
            return []

        if isinstance(claims, dict):
            claims = [claims]
        if not isinstance(claims, list):
            logger.error("Failed to parse claims JSON: response is not an array")
            return []

        validated_claims = []
        for raw in claims:
            if not isinstance(raw, dict):
                continue
            claim_text = raw.get('claim') or raw.get('claim_text') or raw.get('text')
            if not claim_text:
                continue
            claim_text = str(claim_text).strip()
            if not claim_text:
                continue

            claim_type = raw.get('claim_type') or raw.get('type') or self._infer_claim_type(claim_text)
            page_number = raw.get('page_number')
            if isinstance(page_number, str) and page_number.isdigit():
                page_number = int(page_number)
            elif not isinstance(page_number, int):
                page_number = None

            validated_claims.append({
                'claim': claim_text,
                'claim_text': claim_text,
                'claim_type': claim_type,
                'page_number': page_number,
                'confidence': raw.get('confidence', 0.5)
            })

        return validated_claims

    def _infer_claim_type(self, text: str) -> str:
        text_lower = text.lower()
        if re.search(r'\b(founded|acquired|launched|merged|opened|created|established)\b', text_lower):
            return 'company_event'
        if re.search(r'\b(revenue|profit|income|earnings|sales|market share|valuation|price)\b', text_lower):
            return 'financial'
        if re.search(r'\b(gdp|growth|increase|decrease|gain|loss)\b', text_lower):
            return 'growth'
        if re.search(r'\b(users|monthly active users|weekly users|audience|subscribers)\b', text_lower):
            return 'user_count'
        if re.search(r'\b(percent|%|percentage|rate)\b', text_lower):
            return 'statistic'
        if re.search(r'\b(population|demographic|people|citizens)\b', text_lower):
            return 'demographic'
        if re.search(r'\b(rank|ranking|market share)\b', text_lower):
            return 'market'
        if re.search(r'\b(19|20)\d{2}\b', text_lower):
            return 'date'
        return 'unknown'

    def _fallback_extract_claims(self, text: str, pages: List[Dict] = None) -> List[Dict[str, Any]]:
        sentences = self._split_into_sentences(text)
        claims = []
        seen = set()

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if self._is_factual_sentence(sentence):
                claim_text = sentence
                if claim_text in seen:
                    continue
                seen.add(claim_text)
                page_number = self._find_page_number(sentence, pages)
                claims.append({
                    'claim': claim_text,
                    'claim_text': claim_text,
                    'claim_type': self._infer_claim_type(claim_text),
                    'page_number': page_number,
                    'confidence': 0.5
                })

        return claims

    def _split_into_sentences(self, text: str) -> List[str]:
        text = re.sub(r'\s+', ' ', text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _is_factual_sentence(self, sentence: str) -> bool:
        has_year = bool(re.search(r'\b(19|20)\d{2}\b', sentence))
        has_percent = bool(re.search(r'\b\d+(?:\.\d+)?%\b', sentence))
        has_number_phrase = bool(re.search(r'\b\d+(?:\.\d+)?\s*(?:billion|million|thousand|trillion|users|people|dollars|USD)\b', sentence, re.I))
        has_keyword = bool(re.search(
            r'\b(founded|acquired|revenue|users|growth|gdp|market share|rank|ranking|launched|merged|estimated|population|sales|profit|income)\b',
            sentence,
            re.I
        ))
        return has_year or has_percent or has_number_phrase or has_keyword

    def _find_page_number(self, claim_text: str, pages: List[Dict] = None):
        if not pages:
            return None
        for page in pages:
            if claim_text in page['text']:
                return page['page_number']
        return None

    def _add_page_numbers(self, claims: List[Dict], pages: List[Dict]) -> List[Dict[str, Any]]:
        if not pages:
            return claims

        for claim in claims:
            if claim.get('page_number') is None:
                claim['page_number'] = self._find_page_number(claim['claim_text'], pages)

        return claims
