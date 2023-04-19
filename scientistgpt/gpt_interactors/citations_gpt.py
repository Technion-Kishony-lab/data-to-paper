import requests


def get_citations(text):
    url = f"https://api.citeas.org/product/{text}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(data)  # Add this line to print the response JSON
        # Remove the following line for now
        # products = data["data"]

        # bibtex_citations = [create_bibtex(product) for product in products]
        # return bibtex_citations
    else:
        return "Error retrieving citations."


def create_bibtex(product):
    citation_template = (
        "@{type}{{{id},\n"
        "  title={{{title}}},\n"
        "  author={{{author}}},\n"
        "  year={{{year}}},\n"
        "  url={{{url}}}\n"
        "}}"
    )

    bibtex_citation = citation_template.format(
        type=product["type"],
        id=product["id"],
        title=product["title"],
        author=" and ".join([author["given"] + " " + author["family"] for author in product["author"]]),
        year=product["issued"]["date-parts"][0][0],
        url=product["URL"]
    )
    return bibtex_citation


text_to_cite = "Vaccination is widely recognized as one of the most effective tools to control the spread of the virus and to reduce mortality."
citations = get_citations(text_to_cite)

for index, citation in enumerate(citations, start=1):
    print(f"Citation {index}:\n{citation}\n")