# Citation Verification Summary

Every bibliographic entry was checked against the Crossref REST API (title + first author query; best match scored by title similarity, author match, journal container and year). Raw responses and the script are in `crossref_raw/`.

- Entries in bibliography: **200**
- Entries with a DOI: **160**
- DOIs matched or confirmed via Crossref: **157**

| DOI status | Entries |
|---|---|
| Crossref match (title, author, year, journal) | 113 |
| DOI from publisher page/search; Crossref-confirmed | 41 |
| Working paper (journal DOI not available/verified) | 21 |
| Conference/ML venue (not in Crossref or not matched) | 11 |
| Book (no DOI recorded) | 4 |
| Crossref match (online/issue year differs) | 3 |
| No DOI verified | 3 |
| DOI from publisher page/search | 2 |
| Industry white paper (no DOI) | 1 |
| Publisher record (manual) | 1 |

**Caveats.** Conference papers (NeurIPS/ICML), books, some surveys and working papers have no Crossref DOI. Working-paper publication status can change; re-check before submission. Items flagged `[verify]` in the documents are details not confirmed from accessible full text.
