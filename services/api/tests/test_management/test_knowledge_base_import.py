from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class TestKnowledgeBaseImportCommand(TestCase):
    """Test the import_knowledge_base management command."""

    def setUp(self):
        """Set up test fixtures."""
        self.collection_name = "Test Knowledge Base"

    def test_import_knowledge_base_missing_datasets_library(self):
        """Test error when datasets library is missing."""
        with patch("importlib.util.find_spec", return_value=None):
            with pytest.raises(CommandError) as exc_info:
                call_command(
                    "import_knowledge_base_projection",
                    "--collection",
                    self.collection_name,
                    "--lang",
                    "eng",  # Use valid language choice
                )

            assert "datasets" in str(exc_info.value)
            assert "required" in str(exc_info.value)

    def test_command_help_text(self):
        """Test that the command has proper help text."""
        from api.management.commands.import_knowledge_base_projection import Command

        command = Command()
        assert "Knowledge Base Projection" in command.help
        assert "Hugging Face" in command.help

    def test_command_arguments(self):
        """Test that the command has the expected arguments."""
        from api.management.commands.import_knowledge_base_projection import Command

        command = Command()
        parser = command.create_parser("test", "import_knowledge_base_projection")

        # Check that key arguments exist
        help_text = parser.format_help()
        assert "--collection" in help_text
        assert "--split" in help_text
        assert "--streaming" in help_text
        assert "--limit" in help_text
        assert "--async" in help_text
        assert "--hf-token" in help_text
