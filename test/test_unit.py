"""Test pdf-blockifier via unit tests."""
from test import TEST_DATA
from test.utils import load_config, verify_response

import pytest as pytest
from steamship import Steamship
from steamship.base import TaskState
from steamship.plugin.inputs.raw_data_plugin_input import RawDataPluginInput
from steamship.plugin.request import PluginRequest

from src.api import PdfBlockifier

ENVIRONMENT = "prod"

def _read_test_pdf_file(filename: str) -> str:
    with (TEST_DATA / filename).open("rb") as f:
        return f.read()


def test_blockifier():
    """Test AssemblyAI (S2T) Blockifier without edge cases."""
    config = load_config()
    client = Steamship(profile=ENVIRONMENT)
    blockifier = PdfBlockifier(client=client, config=config)
    request = PluginRequest(
        data=RawDataPluginInput(
            data=_read_test_pdf_file("test.pdf"), default_mime_type="application/pdf"
        )
    )
    response = blockifier.run(request)

    blocks = response.data.file.blocks
    assert blocks
    assert len(blocks) == 2
    assert blocks[0].text == "This is the ﬁrst page\n"
    assert blocks[1].text == "This is the second page"


