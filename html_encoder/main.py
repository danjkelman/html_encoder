from typing import List, Optional

import pandas as pd
from lxml.html import fromstring
from tldextract import tldextract

from html_encoder.tag import Tag
from html_encoder.tag_encoder import TagEncoder
from html_encoder.get_data import get_data

def main():
    # intialize tag encoder
    tag_encoder = TagEncoder()

    # how many standard deviations to filter out long-tail
    # encoding in terms of high character count
    SIGMA = 1
    ARTICLE_DATA_FILEPATH = "./data/articles.xlsx"
    OUTPUT_FILEPATH = "./data/test_results.xlsx"


    def get_title_index(tag: Tag, title: str, title_tag_type: str) -> List[int]:
        """
        get the index of the tag(s) with the title string
        as its text content and is of the type specified (ex. H1)
        """
        title_index = [
            i
            for i, tag in enumerate(tag.flatten())
            if title in tag.text and tag.tag_type == title_tag_type
        ]
        return title_index


    def create_html_tag(link: str) -> Optional[Tag]:
        "creates the parent tag and all child tags from url link"

        response = get_data(link)
        # create lxml html element object
        if not response:
            return

        try:
            html_element = fromstring(response.text)
        except ValueError as e:
            print(link, e)
            return

        # get tld for relative links from tags
        extract = tldextract.extract(link)
        tld = link.split(extract.suffix)[0] + extract.suffix

        # get css stylesheet data
        css_links = html_element.xpath('//link[contains(@href, ".css")]')
        style_sheet_content: List[bytes] = list()
        for css_link in css_links:
            css_link = [v for k, v in css_link.items() if k == "href"][0]
            css_link = tld + css_link if css_link[0] == "/" else css_link
            response = get_data(css_link)
            if response:
                style_sheet_content.append(response.content)

        # create tag object
        tag = Tag.from_element(html_element, style_sheet_content)
        print(f"tag created for {link}")
        return tag


    # read in article data
    df = pd.read_excel(ARTICLE_DATA_FILEPATH)

    # get tags
    df["tag"] = df.apply(lambda x: create_html_tag(x.links), axis=1)

    full_length = len(df)

    # fitler out failed attempts
    df = df[df.tag.apply(lambda x: isinstance(x, Tag))].copy()

    crawling_success = len(df)

    # get title element index value
    df["title_index"] = df.apply(lambda x: get_title_index(x.tag, x.titles, x.title_tag_type), axis=1)

    df = df[df.title_index.astype(bool)].copy()

    found_title = len(df)

    df["tag_encoding"] = df.tag.apply(tag_encoder.encode_html)

    print(
        "\n".join(
            [
                f"{crawling_success}/{full_length} successfully crawled.",
                f"{found_title}/{crawling_success} successfully found title.",
                "Maximum number of tags per link:",
                str(max(df.tag.apply(lambda x: len(x.flatten())))),
                "Maximum number of characters per encoding:",
                str(max(df["tag_encoding"].apply(len))),
            ]
        )
    )

    df["tag_encoding_length"] = df.tag_encoding.apply(len)
    sigma = df.tag_encoding_length.mean() + df.tag_encoding_length.std()
    df = df[df.tag_encoding_length <= sigma * SIGMA].copy()

    df.to_excel(OUTPUT_FILEPATH, index=False)

if __name__ == "__main__":
    main()