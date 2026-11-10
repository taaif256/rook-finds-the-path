"""The shared error envelope and the flattening of DRF's nested errors."""

import unittest

from rest_framework.exceptions import ErrorDetail

from config.exceptions import flatten_errors

from .helpers import ApiTestCase


def detail(*messages):
    return [ErrorDetail(message) for message in messages]


class FlattenErrorsTests(unittest.TestCase):
    def test_flat_fields(self):
        self.assertEqual(
            flatten_errors({"algorithm": detail("Bad."), "end": detail("One.", "Two.")}),
            {"algorithm": ["Bad."], "end": ["One.", "Two."]},
        )

    def test_nested_serializers_use_dotted_paths(self):
        self.assertEqual(flatten_errors({"grid": {"rows": detail("Bad.")}}), {"grid.rows": ["Bad."]})

    def test_list_errors_use_the_item_index_and_skip_valid_items(self):
        errors = {"barriers": [{}, {"row": detail("Bad.")}, {}, {"col": detail("Missing.")}]}
        self.assertEqual(flatten_errors(errors), {"barriers.1.row": ["Bad."], "barriers.3.col": ["Missing."]})

    def test_a_nested_non_field_error_belongs_to_the_parent_field(self):
        self.assertEqual(
            flatten_errors({"grid": {"non_field_errors": detail("Expected a dictionary.")}}),
            {"grid": ["Expected a dictionary."]},
        )
        self.assertEqual(
            flatten_errors({"barriers": [{"non_field_errors": detail("Expected a dictionary.")}]}),
            {"barriers.0": ["Expected a dictionary."]},
        )

    def test_top_level_non_field_errors_keep_their_name(self):
        self.assertEqual(flatten_errors({"non_field_errors": detail("Nope.")}), {"non_field_errors": ["Nope."]})

    def test_bare_lists_and_strings(self):
        self.assertEqual(flatten_errors(detail("Nope.")), {"non_field_errors": ["Nope."]})
        self.assertEqual(flatten_errors(ErrorDetail("Nope.")), {"non_field_errors": ["Nope."]})

    def test_integer_keys_and_empty_input(self):
        self.assertEqual(flatten_errors({"barriers": {0: detail("Bad.")}}), {"barriers.0": ["Bad."]})
        self.assertEqual(flatten_errors({}), {})
        self.assertEqual(flatten_errors({"barriers": []}), {})

    def test_messages_are_plain_strings(self):
        message = flatten_errors({"a": detail("x")})["a"][0]
        self.assertIs(type(message), str)


class EnvelopeAppliesToEveryEndpointTests(ApiTestCase):
    def test_health_endpoint_errors_use_the_same_envelope(self):
        response = self.client.post("/api/v1/health/")
        body = self.assertRejected(response, status=405, message=None)
        self.assertEqual(body["errors"], {})
        self.assertIn("GET", response.headers["Allow"])


if __name__ == "__main__":
    unittest.main()
