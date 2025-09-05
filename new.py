import requests 
def case_text_search_citations_list(query: str): 
    # set API URL
    url = "https://api.a2aj.ca/search"

    # get parameters
    query = query    # required, supports advanced syntax
    search_type = "full_text"     # "full_text" or "name" (default "full_text")
    doc_type = "cases"            # "cases" or "laws" (default "cases")
    size = 5                    # optional, max 50
    search_language = "en"        # "en" or "fr" (default "en")
    sort_results = "default"      # "default", "newest_first", "oldest_first"
    dataset = "CHRT,SCC,ONCA"     # optional, comma-separated dataset codes
    start_date = "2020-01-01"     # optional YYYY-MM-DD
    end_date = "2025-06-01"       # optional YYYY-MM-DD

    params = {
        "query": query,
        "search_type": search_type,
        "doc_type": doc_type,
        "size": size,
        "search_language": search_language,
        "sort_results": sort_results,
        "dataset": dataset,
        "start_date": start_date,
        "end_date": end_date,
    }

    # get data
    resp = requests.get(url, params=params, timeout=30)
    data = resp.json()
    results = data.get("results", [])
    return [result['citation_en'] for result in results]

def retrieve_citation_text(citations: list[str]):

    url = "https://api.a2aj.ca/fetch"

    # get parameters
    doc_type = "cases"                # "cases" | "laws"  (default is "cases")
    output_language = "en"            # "en" | "fr" | "both" (default "en")
    start_char = 0                    # optional, chunk start
    end_char = -1                     # optional, -1 → end
    # section is ONLY for laws; omit it for cases
    # section = None
    citation_results = []
    for citation in citations: 
        params = {
            "citation": citation,
            "doc_type": doc_type,
            "output_language": output_language,
            "start_char": start_char,
            "end_char": end_char,
            # "section": section,  # include ONLY when doc_type == "laws" and you want a specific section
        }

        # get data
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        results = data.get("results", [])[0].get("unofficial_text_en") # how many texts per 1 citation
        citation_results.append(results) 
    return citation_results

if __name__ == "__main__":
    # 10 citations -> 10 unstructured texts
    citations = case_text_search_citations_list('("employment discrimination" OR "workplace discrimination" OR "discrimination in employment" OR "employment equity" OR "human rights" OR "wrongful dismissal" OR "workplace harassment") AND (Canada OR "Canadian" OR "Ontario" OR "British Columbia" OR "Alberta" OR "federal") AND (employee OR worker OR "plaintiff" OR "claimant" OR "complainant" OR "applicant") AND ("ruled for" OR "favored" OR "decision in favor of" OR "successful" OR "awarded" OR "damages" OR "remedy" OR "reinstatement" OR "compensation")')
    print(citations)
    print(len(retrieve_citation_text(citations)))
    # how many unstructured texts per citation -> 
# conversational query -> rewrite -> retrieve citations (10 - by rank) -> simultaneous AI calls 