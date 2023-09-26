"""PDF blockifier."""
import logging
from typing import Any, Dict, Optional, Type, Union
from uuid import uuid4
import pypdf
import re
import io
from pydantic import Field

from steamship import Block, File, SteamshipError, Tag
from steamship.data.tags.tag_constants import TagKind, TagValueKey, DocTag
from steamship.invocable import Config, InvocableResponse
from steamship.plugin.blockifier import Blockifier
from steamship.plugin.inputs.raw_data_plugin_input import RawDataPluginInput
from steamship.plugin.outputs.block_and_tag_plugin_output import BlockAndTagPluginOutput
from steamship.plugin.request import PluginRequest


class PdfBlockifier(Blockifier):
    """Blockifier that turns a text PDF into blocks (one page per block).

    Attributes
    ----------
    config : PdfBlockifierConfig
        The required configuration used to instantiate a pdf-blockifier
    """

    class PdfBlockifierConfig(Config):
        """Config object containing required configuration parameters to initialize a PdfBlockifier."""
        loader: str = Field(
            "pypdf",
            description="The data loader to use (default: pypdf).",
        )

    config: PdfBlockifierConfig

    @classmethod
    def config_cls(cls) -> Type[Config]:
        """Return the configuration object for the Blockifier Plugin."""
        return cls.PdfBlockifierConfig

    def run(
        self, request: PluginRequest[RawDataPluginInput]
    ) -> Union[InvocableResponse, InvocableResponse[BlockAndTagPluginOutput]]:
        """Converts the PDF into one block per page."""
        logging.info("PDF BLockifier received run request.")
        if request.is_status_check:
            logging.info("Status check.")
            raise SteamshipError(message="PDF Blockifier does not yet support async blockification.")
        else:
            return self._run(request.data.data)

    def _run(self, _bytes: bytes) -> InvocableResponse[BlockAndTagPluginOutput]:
        stream = io.BytesIO(_bytes)
        pdf_reader = pypdf.PdfReader(stream)
        blocks = []

        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()

            # Blank pages cause empty blocks, which cause problems for embedders.
            if text == "": 
                continue
                
            # Fix an encoding bug that sometimes arises.
            text = re.sub("\u0000", "", text)
                   
            block = Block(
                text=text,
                tags=[
                    Tag(kind=TagKind.DOCUMENT, name=DocTag.PAGE, value={
                        TagValueKey.NUMBER_VALUE: i
                    })
                ]
            )
            blocks.append(block)
        
        return InvocableResponse(
            data=BlockAndTagPluginOutput(
                file=File(blocks=blocks)
            )
        )
