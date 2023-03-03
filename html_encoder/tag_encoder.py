from typing import Dict, List

import numpy as np
import tinycss2

from html_encoder.tag import CssRule, Tag

CHARACTER_DELIMITER = "2"
ATTRIBUTE_DELIMITER = "3"
CHILD_DELIMITER = "4"


class TagEncoder:
    def __init__(self):
        self.tag_type_mappings: Dict[str, int] = dict()
        self.attributes_key_mappings: Dict[str, int] = dict()
        self.css_key_mappings: Dict[str, int] = dict()

    @staticmethod
    def _encode_to_mapping(raw_string: str, mapping: Dict[str, int]):
        encoding = mapping.get(raw_string)
        if not encoding and not mapping:
            mapping[raw_string] = 0
        elif not encoding:
            mapping[raw_string] = max(mapping.values()) + 1
        return mapping, mapping.get(raw_string)

    @staticmethod
    def _to_binary(raw_string: str):
        return CHARACTER_DELIMITER.join(format(x, "b") for x in bytearray(raw_string, "utf-8"))

    def _encode_tag_type(self, tag_type: str):
        self.tag_type_mappings, encoded_tag_type = self._encode_to_mapping(
            tag_type, self.tag_type_mappings
        )
        return self._to_binary(str(encoded_tag_type))

    def _encode_tag_attributes(self, tag_attributes: Dict[str, str]) -> str:
        encoded_tag_attributes = dict()
        for key, value in tag_attributes.items():
            self.attributes_key_mappings, encoded_key = self._encode_to_mapping(
                key, self.attributes_key_mappings
            )
            encoded_tag_attributes[encoded_key] = value
        return self._to_binary(str(encoded_tag_attributes))

    def _encode_css_rules(self, css_rules: List[CssRule]) -> str:
        encoded_css_attributes = dict()
        for rule in css_rules:
            serialized_prelude = tinycss2.serialize(rule.tinycss2_rule_obj.prelude)
            content = tinycss2.serialize(
                [token for token in rule.tinycss2_rule_obj.content if token.type != "whitespace"]
            )
            content = content[:-1] if content.endswith(";") else content
            key_attribute_pairs = content.split(";")
            encoded_css_attributes[serialized_prelude] = dict()
            for pair in key_attribute_pairs:
                pair = pair.split(":")
                if len(pair) != 2:
                    continue
                key, value = pair
                self.css_key_mappings, encoded_key = self._encode_to_mapping(
                    key, self.css_key_mappings
                )
                encoded_css_attributes[serialized_prelude][encoded_key] = value
        return self._to_binary(str(encoded_css_attributes))

    def _encode_tag(self, tag: Tag) -> str:
        encoded_tag_type = self._encode_tag_type(tag.tag_type)
        encoded_tag_attributes = self._encode_tag_attributes(tag.attributes)
        encoded_css_rules = self._encode_css_rules(tag.applicable_css_rules)
        encoded_text_length = self._to_binary(str(len(tag.text))) if tag.text else ""
        encoded_children = CHILD_DELIMITER.join([self._encode_tag(child) for child in tag.children])
        return ATTRIBUTE_DELIMITER.join(
            [
                encoded_tag_type,
                encoded_tag_attributes,
                encoded_css_rules,
                encoded_text_length,
                encoded_children,
            ]
        )

    @staticmethod
    def _to_normalized_floats_array(encoded_tag: str) -> np.ndarray:
        encoded_tag_ints = list(map(int, list(encoded_tag)))  # type: ignore
        max_int = max(encoded_tag_ints)
        max_int = 1 if max_int == 0 else max_int
        return np.array(encoded_tag_ints) / max_int

    def encode_html(self, tag: Tag) -> np.ndarray:
        encoded_tag = self._encode_tag(tag)
        return self._to_normalized_floats_array(encoded_tag)
