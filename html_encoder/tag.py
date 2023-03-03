from typing import Dict, List, NamedTuple, Optional

import tinycss2
from lxml.html import HtmlElement
from tinycss2.ast import QualifiedRule


class CssRule(NamedTuple):
    tinycss2_rule_obj: QualifiedRule
    selected_elements: List[HtmlElement]


class Tag(NamedTuple):
    tag_type: str
    attributes: Dict[str, str]
    text: str
    all_css_rules: List[CssRule]
    applicable_css_rules: List[CssRule]
    children: List["Tag"]

    def __eq__(self, __o: "Tag") -> bool:
        # equality intentionally excludes children attribute for wrangling
        return (
            __o.tag_type == self.tag_type and __o.attributes == self.text and __o.text == self.text
        )

    def __repr__(self) -> str:
        text = self.text[:10]
        text = text if text == self.text else text + "..."
        id_ = [v for k, v in self.attributes.items() if k == "id"]
        id_ = f' id="{id_[0]}"' if id_ else ""
        children = "".join([child.__repr__() for child in self.children])
        return f"<{self.tag_type}{id_} css_rules={len(self.applicable_css_rules)}>{text}{children}</{self.tag_type}>"

    @classmethod
    def from_element(
        cls,
        tag: HtmlElement,
        style_sheet_content: Optional[List[bytes]] = None,
        all_css_rules: Optional[List[CssRule]] = None,
    ) -> "Tag":

        if all_css_rules is None and style_sheet_content is None:
            raise ValueError(
                "Tag must be constructed with either "
                "stylesheet content (empty list is valid) or css_rules."
            )
        elif all_css_rules is None:
            all_css_rules = cls._get_css_rules(tag, style_sheet_content)  # type: ignore

        applicable_css_rules = [rule for rule in all_css_rules if tag in rule.selected_elements]

        tag_obj = Tag(
            tag_type=tag.tag if isinstance(tag.tag, str) else tag.tag.__name__,
            attributes={k: v for k, v in tag.items()},
            text=tag.text if tag.text else "",
            children=[Tag.from_element(child, None, all_css_rules) for child in tag],  # type: ignore
            all_css_rules=all_css_rules,
            applicable_css_rules=applicable_css_rules,
        )
        return tag_obj

    @classmethod
    def _get_css_rules(cls, tag: HtmlElement, style_sheet_content: List[bytes]) -> List[CssRule]:
        css_rules: List[CssRule] = list()
        for content in style_sheet_content:
            for qualified_rule in cls._parse_css(content):
                prelude_string = tinycss2.serialize(qualified_rule.prelude)
                if ":" in prelude_string:  # skip pseudo classes and ids
                    continue
                try:
                    tags = tag.cssselect(prelude_string)
                except Exception as e:
                    print(e)
                    continue
                css_rules.append(CssRule(qualified_rule, tags))
        return css_rules

    @staticmethod
    def _parse_css(css_content: bytes) -> List[QualifiedRule]:
        rules, _ = tinycss2.parse_stylesheet_bytes(
            css_content, skip_whitespace=True, skip_comments=True
        )
        return [rule for rule in rules if rule.type == "qualified-rule"]

    def flatten(self) -> List["Tag"]:
        children = [child.flatten() for child in self.children]
        children = [c for child in children for c in child]
        return [self, *children]
