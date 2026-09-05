from __future__ import annotations

import os
from datetime import date

import httpx

from ..models import EvidenceBundle, FilingEvidence, MetricSnapshot, SecFactEvidence, SourceStatus


class SecFilingEvidenceProvider:
    """Official recent SEC filing metadata from data.sec.gov.

    SEC's submissions API does not require an API key, but automated clients are
    expected to send an identifying User-Agent. `SEC_USER_AGENT` can override
    the default application identifier.
    """

    TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
    COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
    FACT_CONCEPTS = (
        ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenue", "USD"),
        ("Revenues", "Revenue", "USD"),
        ("NetIncomeLoss", "Net income", "USD"),
        ("OperatingIncomeLoss", "Operating income", "USD"),
        ("NetCashProvidedByUsedInOperatingActivities", "Operating cash flow", "USD"),
        ("PaymentsToAcquirePropertyPlantAndEquipment", "Capital expenditures", "USD"),
        ("Assets", "Total assets", "USD"),
        ("Liabilities", "Total liabilities", "USD"),
        ("StockholdersEquity", "Stockholders' equity", "USD"),
        ("ShareBasedCompensation", "Stock-based compensation", "USD"),
        ("CommonStockSharesOutstanding", "Common shares outstanding", "shares"),
    )
    FORMS = {
        "10-K",
        "10-K/A",
        "10-Q",
        "10-Q/A",
        "8-K",
        "8-K/A",
        "20-F",
        "40-F",
        "6-K",
    }

    def __init__(self, max_filings: int = 8, user_agent: str | None = None, timeout: float = 20.0):
        self.max_filings = max(0, max_filings)
        self.user_agent = user_agent or os.getenv(
            "SEC_USER_AGENT",
            "AskWarren/0.4 https://github.com/drmaganti/ask-warren",
        )
        self.timeout = timeout
        self._ticker_map: dict[str, tuple[int, str]] | None = None

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
        )

    def _load_ticker_map(self, client: httpx.Client) -> dict[str, tuple[int, str]]:
        if self._ticker_map is not None:
            return self._ticker_map
        response = client.get(self.TICKER_MAP_URL)
        response.raise_for_status()
        payload = response.json()
        mapping: dict[str, tuple[int, str]] = {}
        for record in payload.values():
            ticker = str(record.get("ticker") or "").strip().upper()
            cik = record.get("cik_str")
            if not ticker or cik is None:
                continue
            mapping[ticker] = (int(cik), str(record.get("title") or ticker))
        self._ticker_map = mapping
        return mapping

    @staticmethod
    def _parse_date(raw: str | None) -> date | None:
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None

    @classmethod
    def _extract_company_facts(cls, payload: dict, cik: int) -> list[SecFactEvidence]:
        us_gaap = ((payload.get("facts") or {}).get("us-gaap") or {})
        results: list[SecFactEvidence] = []
        seen_labels: set[str] = set()
        for concept, label, preferred_unit in cls.FACT_CONCEPTS:
            if label in seen_labels:
                continue
            fact = us_gaap.get(concept) or {}
            unit_rows = (fact.get("units") or {}).get(preferred_unit) or []
            eligible = [row for row in unit_rows if row.get("form") in {"10-K", "10-Q"} and row.get("val") is not None]
            if not eligible:
                continue
            row = max(eligible, key=lambda item: (str(item.get("filed") or ""), str(item.get("end") or "")))
            accession = str(row.get("accn") or "")
            accession_path = accession.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_path}/" if accession_path else None
            results.append(SecFactEvidence(
                concept=concept,
                label=label,
                value=float(row["val"]),
                unit=preferred_unit,
                period_end=cls._parse_date(row.get("end")),
                filed_at=cls._parse_date(row.get("filed")),
                fiscal_period=row.get("fp"),
                form=row.get("form"),
                accession_number=accession or None,
                url=url,
            ))
            seen_labels.add(label)
        return results

    def fetch_evidence(self, ticker: str, metrics: MetricSnapshot) -> EvidenceBundle:
        symbol = ticker.strip().upper()
        bundle = EvidenceBundle()

        if symbol.endswith(".TO"):
            bundle.source_status.append(
                SourceStatus(
                    source="SEC EDGAR",
                    status="unavailable",
                    detail="TSX symbol; Warren does not guess a US cross-listing for SEC evidence.",
                )
            )
            return bundle

        with self._client() as client:
            mapping = self._load_ticker_map(client)
            company = mapping.get(symbol)
            if company is None:
                bundle.source_status.append(
                    SourceStatus(
                        source="SEC EDGAR",
                        status="unavailable",
                        detail=f"No exact SEC ticker-to-CIK mapping for {symbol}.",
                    )
                )
                return bundle

            cik, sec_name = company
            response = client.get(self.SUBMISSIONS_URL.format(cik=cik))
            response.raise_for_status()
            payload = response.json()
            try:
                facts_response = client.get(self.COMPANY_FACTS_URL.format(cik=cik))
                facts_response.raise_for_status()
                bundle.sec_facts = self._extract_company_facts(facts_response.json(), cik)
            except (httpx.HTTPError, ValueError, TypeError):
                bundle.sec_facts = []

        recent = (payload.get("filings") or {}).get("recent") or {}
        forms = recent.get("form") or []
        filed = recent.get("filingDate") or []
        accessions = recent.get("accessionNumber") or []
        documents = recent.get("primaryDocument") or []

        total = min(len(forms), len(filed), len(accessions), len(documents))
        for idx in range(total):
            form = str(forms[idx] or "")
            if form not in self.FORMS:
                continue
            accession = str(accessions[idx] or "")
            document = str(documents[idx] or "")
            accession_path = accession.replace("-", "")
            url = None
            if accession_path and document:
                url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_path}/{document}"
            bundle.filings.append(
                FilingEvidence(
                    form=form,
                    filed_at=self._parse_date(str(filed[idx] or "")),
                    accession_number=accession or None,
                    primary_document=document or None,
                    url=url,
                )
            )
            if len(bundle.filings) >= self.max_filings:
                break

        bundle.metadata.update({"sec_cik": cik, "sec_company_name": sec_name})
        bundle.source_status.append(
            SourceStatus(
                source="SEC EDGAR",
                status="ok" if bundle.filings and bundle.sec_facts else "partial",
                detail=f"{len(bundle.filings)} recent material filings and {len(bundle.sec_facts)} latest XBRL facts returned",
            )
        )
        return bundle
