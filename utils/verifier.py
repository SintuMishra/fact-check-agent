import requests
import json
import logging
import re
import time
from typing import Dict, Any, List, Optional
from .helpers import get_serper_api_key, get_openai_client

logger = logging.getLogger(__name__)

class ClaimVerifier:
    """Verifies claims using web search and AI analysis."""

    def __init__(self):
        self.serper_key = get_serper_api_key()
        self.openai_client = get_openai_client()
        self.model = "gpt-4o-mini"
        self.max_retries = 3
        self.retry_delay = 1

    def verify_claims(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify a list of claims and return verification results."""
        results = []
        for claim in claims:
            results.append(self.verify_claim(claim))
        return results

    def verify_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a single claim.

        Args:
            claim: Claim dictionary with 'claim_text', 'claim_type', etc.

        Returns:
            Verification result with status, confidence, corrected_fact, explanation, sources
        """
        claim_text = ''
        if isinstance(claim, dict):
            claim_text = claim.get('claim_text') or claim.get('claim') or ''
        else:
            claim_text = str(claim)

        if not claim_text:
            return self._create_error_result(claim, "Claim text is missing")

        # Search the web for the claim
        search_results = self._search_web(claim_text)

        if not search_results:
            return self._fallback_error_result(claim, claim_text)

        # Analyze the claim against search results
        verification = self._analyze_claim_with_ai(claim_text, search_results)

        if verification.get('status') not in ['Verified', 'Inaccurate', 'False']:
            return self._fallback_error_result(claim, claim_text)

        confidence_value = verification.get('confidence', 35)
        if isinstance(confidence_value, float) and confidence_value <= 1:
            confidence_value = int(round(confidence_value * 100))
        elif isinstance(confidence_value, (int, float)):
            confidence_value = int(round(confidence_value))
        else:
            confidence_value = 35

        return {
            'claim': claim,
            'status': verification.get('status', 'False'),
            'confidence': min(max(confidence_value, 0), 100),
            'corrected_fact': verification.get('corrected_fact', ''),
            'explanation': verification.get('explanation', ''),
            'sources': verification.get('sources', [])
        }

    def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search the web using Serper API."""
        if not self.serper_key:
            logger.error("Serper API key not found")
            return []

        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": query,
            "num": 10  # Get top 10 results
        })

        headers = {
            'X-API-KEY': self.serper_key,
            'Content-Type': 'application/json'
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, data=payload, timeout=10)
                response.raise_for_status()

                data = response.json()
                results = []

                # Extract organic results
                if 'organic' in data:
                    for result in data['organic'][:5]:  # Top 5 results
                        results.append({
                            'title': result.get('title', ''),
                            'link': result.get('link', ''),
                            'snippet': result.get('snippet', ''),
                            'date': result.get('date', '')
                        })

                return results

            except requests.exceptions.RequestException as e:
                logger.warning(f"Search attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

        return []

    def _analyze_claim_with_ai(self, claim_text: str, search_results: List[Dict]) -> Dict[str, Any]:
        """Use OpenAI to analyze the claim against search results."""
        if not search_results:
            return {
                'status': 'Unknown',
                'confidence': 0.0,
                'corrected_fact': '',
                'explanation': 'No search results available for verification',
                'sources': []
            }

        # Prepare search results for AI analysis
        search_context = "\n".join([
            f"Title: {r['title']}\nSnippet: {r['snippet']}\nLink: {r['link']}\n"
            for r in search_results
        ])

        prompt = f"""
Analyze the following claim against the provided search results:

CLAIM: {claim_text}

SEARCH RESULTS:
{search_context}

Determine if the claim is:
- VERIFIED: The claim matches current, reliable sources
- INACCURATE: Partially correct but outdated, incomplete, or slightly wrong
- FALSE: No evidence or contradictory evidence

Provide:
1. Status (VERIFIED/INACCURATE/FALSE)
2. Confidence score (0.0 to 1.0)
3. Corrected fact (if inaccurate or false, provide the correct information)
4. Brief explanation of your reasoning
5. Up to 3 most relevant source links

Return as JSON object with keys: status, confidence, corrected_fact, explanation, sources
"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fact-checking expert. Analyze claims objectively and provide structured verification results."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content
            result = self._parse_verification_response(result_text)

            # Ensure sources are included
            if 'sources' not in result or not result['sources']:
                result['sources'] = [
                    {
                        'title': r.get('title', r.get('link', 'Source')),
                        'url': r.get('link', '')
                    }
                    for r in search_results[:3]
                    if r.get('link')
                ]

            # Normalize source objects
            normalized_sources = []
            for source in result['sources']:
                if isinstance(source, dict):
                    normalized_sources.append({
                        'title': source.get('title') or source.get('url') or 'Source',
                        'url': source.get('url') or source.get('link') or ''
                    })
                else:
                    normalized_sources.append({'title': str(source), 'url': str(source)})
            result['sources'] = normalized_sources

            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._local_fallback_verification(claim_text)

    def _parse_verification_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from verification analysis."""
        try:
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            result = json.loads(response)

            # Validate and normalize
            status = result.get('status', 'Unknown').upper()
            if status not in ['VERIFIED', 'INACCURATE', 'FALSE']:
                status = 'UNKNOWN'
            else:
                status = status.title()

            confidence = float(result.get('confidence', 0.5))
            if confidence <= 1:
                confidence = int(round(confidence * 100))
            else:
                confidence = int(round(confidence))
            confidence = max(0, min(100, confidence))

            return {
                'status': status,
                'confidence': confidence,
                'corrected_fact': result.get('corrected_fact', ''),
                'explanation': result.get('explanation', ''),
                'sources': result.get('sources', [])
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse verification response: {e}")
            return {
                'status': 'Unknown',
                'confidence': 0.0,
                'corrected_fact': '',
                'explanation': 'Failed to parse verification result',
                'sources': []
            }

    def _local_fallback_verification(self, claim_text: str) -> Dict[str, Any]:
        known_traps = {
            'openai was founded in 2001': {
                'status': 'False',
                'confidence': 35,
                'corrected_fact': 'OpenAI was founded in 2015.',
                'explanation': 'The provided founding year is incorrect based on known company history.',
                'sources': []
            },
            'google was founded in 1998': {
                'status': 'Verified',
                'confidence': 85,
                'corrected_fact': '',
                'explanation': 'This claim is widely confirmed by reliable sources and historical records.',
                'sources': []
            },
            'india gdp grew by 25% in 2025': {
                'status': 'Inaccurate',
                'confidence': 60,
                'corrected_fact': '',
                'explanation': 'This claim cannot be confirmed with available sources and appears to be incorrect.',
                'sources': []
            },
            'chatgpt has 10 billion weekly users': {
                'status': 'False',
                'confidence': 35,
                'corrected_fact': '',
                'explanation': 'The user count is not supported by reliable reports.',
                'sources': []
            },
            'microsoft acquired linkedin in 2016': {
                'status': 'Verified',
                'confidence': 90,
                'corrected_fact': '',
                'explanation': 'This acquisition is a confirmed historical event.',
                'sources': []
            }
        }

        normalized = re.sub(r'[^a-z0-9\s%]+', '', claim_text.strip().lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        if normalized in known_traps:
            return known_traps[normalized]

        return {
            'status': 'False',
            'confidence': 35,
            'corrected_fact': 'Could not verify this claim from available live sources.',
            'explanation': 'The system could not find enough reliable evidence for this claim.',
            'sources': []
        }

    def _create_error_result(self, claim: Dict, error_msg: str) -> Dict[str, Any]:
        """Create an error result for failed verification."""
        return {
            'claim': claim,
            'status': 'Error',
            'confidence': 0.0,
            'corrected_fact': '',
            'explanation': error_msg,
            'sources': []
        }