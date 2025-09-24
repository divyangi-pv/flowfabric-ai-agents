"""
Unit tests for utility functions, particularly release notes extraction.
"""
import pytest
from mcp_tools.version_support_assistant import extract_text_from_description


class TestExtractTextFromDescription:
    """Test release notes extraction from various Jira description formats."""
    
    def test_structured_description_with_release_info(self):
        """Test extraction from structured Jira description with release information."""
        description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "This is a test ticket. "},
                        {"type": "text", "text": "Release Information: https://example.com/release-notes"},
                        {"type": "text", "text": " Additional text here."}
                    ]
                }
            ]
        }
        result = extract_text_from_description(description)
        assert result == "https://example.com/release-notes"
    
    def test_structured_description_without_release_info(self):
        """Test extraction from structured description without release information."""
        description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "This is a test ticket without release info."}
                    ]
                }
            ]
        }
        result = extract_text_from_description(description)
        assert result is None
    
    def test_plain_text_description_with_release_info(self):
        """Test extraction from plain text description with release information."""
        description = "This is a plain text description. Release Information: https://example.com/release-notes More text."
        result = extract_text_from_description(description)
        assert result == "https://example.com/release-notes"
    
    def test_plain_text_description_without_release_info(self):
        """Test extraction from plain text description without release information."""
        description = "This is a plain text description without release info."
        result = extract_text_from_description(description)
        assert result is None
    
    def test_none_description(self):
        """Test extraction from None description."""
        result = extract_text_from_description(None)
        assert result is None
    
    def test_empty_string_description(self):
        """Test extraction from empty string description."""
        result = extract_text_from_description("")
        assert result is None
    
    def test_nested_paragraph_structure(self):
        """Test extraction from nested paragraph structure."""
        description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "First paragraph. "}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Release Information: https://nested.example.com/release"}
                    ]
                }
            ]
        }
        result = extract_text_from_description(description)
        assert result == "https://nested.example.com/release"
    
    def test_multiple_urls_after_release_info(self):
        """Test extraction when multiple URLs follow release information marker."""
        description = "Some text. Release Information: https://first.com/release https://second.com/release"
        result = extract_text_from_description(description)
        assert result == "https://first.com/release"
    
    def test_release_info_at_beginning(self):
        """Test extraction when release information is at the beginning."""
        description = "Release Information: https://beginning.com/release Additional text follows."
        result = extract_text_from_description(description)
        assert result == "https://beginning.com/release"
    
    def test_release_info_at_end(self):
        """Test extraction when release information is at the end."""
        description = "Some descriptive text here. Release Information: https://end.com/release"
        result = extract_text_from_description(description)
        assert result == "https://end.com/release"
    
    def test_case_sensitive_release_info(self):
        """Test that release information marker is case sensitive."""
        description = "Some text. release information: https://lowercase.com/release"
        result = extract_text_from_description(description)
        assert result is None
    
    def test_malformed_structured_description(self):
        """Test handling of malformed structured description."""
        description = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph"
                    # Missing content field
                }
            ]
        }
        result = extract_text_from_description(description)
        assert result is None
    
    def test_non_text_content_types(self):
        """Test handling of non-text content types in structured description."""
        description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "hardBreak"},
                        {"type": "text", "text": "Release Information: https://mixed.com/release"}
                    ]
                }
            ]
        }
        result = extract_text_from_description(description)
        assert result == "https://mixed.com/release"
    
    def test_invalid_description_type(self):
        """Test handling of invalid description types."""
        description = 12345  # Invalid type
        result = extract_text_from_description(description)
        assert result is None
    
    def test_empty_content_array(self):
        """Test handling of empty content array in structured description."""
        description = {
            "type": "doc",
            "version": 1,
            "content": []
        }
        result = extract_text_from_description(description)
        assert result is None