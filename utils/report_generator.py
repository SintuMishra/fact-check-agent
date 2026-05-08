import pandas as pd
import csv
import io
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates downloadable reports from verification results."""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_csv_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a CSV report from verification results.

        Args:
            results: List of verification result dictionaries

        Returns:
            CSV content as string
        """
        if not results:
            return self._generate_empty_report()

        # Prepare data for CSV
        csv_data = []
        for result in results:
            claim = result.get('claim', {})
            if isinstance(claim, dict):
                claim_text = claim.get('claim_text') or claim.get('claim') or ''
                claim_type = claim.get('claim_type', '')
                page_number = claim.get('page_number', '')
            else:
                claim_text = str(claim)
                claim_type = ''
                page_number = ''

            sources = result.get('sources', [])
            if isinstance(sources, list):
                source_texts = [s.get('url') if isinstance(s, dict) else str(s) for s in sources]
            else:
                source_texts = [str(sources)]

            row = {
                'Claim Text': claim_text,
                'Claim Type': claim_type,
                'Page Number': page_number,
                'Status': result.get('status', ''),
                'Confidence': result.get('confidence', 0.0),
                'Corrected Fact': result.get('corrected_fact', ''),
                'Explanation': result.get('explanation', ''),
                'Sources': '; '.join(source_texts)
            }
            csv_data.append(row)

        # Create DataFrame and CSV
        df = pd.DataFrame(csv_data)

        # Use StringIO for in-memory CSV
        output = io.StringIO()
        df.to_csv(output, index=False, quoting=csv.QUOTE_ALL)
        csv_content = output.getvalue()
        output.close()

        return csv_content

    def generate_summary_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from results.

        Args:
            results: List of verification result dictionaries

        Returns:
            Summary dictionary
        """
        if not results:
            return {
                'total_claims': 0,
                'verified': 0,
                'inaccurate': 0,
                'false': 0,
                'error': 0,
                'accuracy_percentage': 0.0,
                'average_confidence': 0.0
            }

        total_claims = len(results)
        status_counts = {
            'VERIFIED': 0,
            'INACCURATE': 0,
            'FALSE': 0,
            'ERROR': 0,
            'UNKNOWN': 0
        }

        total_confidence = 0.0
        valid_confidence_count = 0

        for result in results:
            status = result.get('status', 'UNKNOWN').upper()
            status_counts[status] = status_counts.get(status, 0) + 1

            confidence = result.get('confidence', 0.0)
            if isinstance(confidence, (int, float)):
                total_confidence += confidence
                valid_confidence_count += 1

        verified_count = status_counts['VERIFIED']
        accuracy_percentage = (verified_count / total_claims) * 100 if total_claims > 0 else 0.0
        average_confidence = total_confidence / valid_confidence_count if valid_confidence_count > 0 else 0.0

        return {
            'total_claims': total_claims,
            'verified': verified_count,
            'inaccurate': status_counts['INACCURATE'],
            'false': status_counts['FALSE'],
            'error': status_counts['ERROR'] + status_counts['UNKNOWN'],
            'accuracy_percentage': round(accuracy_percentage, 2),
            'average_confidence': round(average_confidence, 2)
        }

    def _generate_empty_report(self) -> str:
        """Generate an empty CSV report."""
        df = pd.DataFrame(columns=[
            'Claim Text', 'Claim Type', 'Page Number', 'Status',
            'Confidence', 'Corrected Fact', 'Explanation', 'Sources'
        ])
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_content = output.getvalue()
        output.close()
        return csv_content

    def get_report_filename(self) -> str:
        """Generate a timestamped filename for the report."""
        return f"fact_check_report_{self.timestamp}.csv"