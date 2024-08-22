import inspect
import os
from typing import Awaitable, Callable, Text

from actions.logger import custom_logger
from rasa.core.channels.channel import (
    CollectingOutputChannel,
    InputChannel,
    UserMessage,
)
from sanic import Blueprint
from sanic.request import Request
from sanic.response import HTTPResponse

from .whatsapp_api_integration.message import NotSupportedMessage
from .whatsapp_api_integration.wpp_event import WhatsAppEvent


class WhatsApp(InputChannel):
    def name(self) -> Text:
        """Name of your custom channel."""
        return "whatsapp"

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[None]]
    ) -> Blueprint:
        custom_webhook = Blueprint(
            "custom_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        @custom_webhook.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            return HTTPResponse("ok", status=200)

        @custom_webhook.route("/webhook", methods=["GET", "POST"])
        async def receive(request: Request) -> HTTPResponse:
            if request.method == "GET":
                if request.args.get("hub.verify_token") != os.getenv(
                    "WPP_VERIFY_TOKEN", ""
                ):
                    return HTTPResponse("Invalid verify token", status=500)
                return HTTPResponse(request.args.get("hub.challenge"), status=200)

            # extracting whatsapp text message
            whatsapp_event = WhatsAppEvent(request.json)
            whatsapp_message = whatsapp_event.get_event_message()
            custom_logger(f"WHATSAPP_MESSAGE: {whatsapp_message}")

            # Send whatsapp message to Rasa NLU
            if type(whatsapp_message) is NotSupportedMessage:
                return HTTPResponse("ok", status=200)

            custom_logger("WHATSAPP EVENT", request.json)

            # send message to Rasa
            collector = CollectingOutputChannel()
            await on_new_message(
                UserMessage(
                    whatsapp_message.text,
                    collector,
                    whatsapp_event.contact.phone,
                    input_channel=self.name(),
                    metadata={"contact_name": whatsapp_event.contact.name},
                )
            )

            # Retrieve Rasa answers
            bot_answers = collector.messages

            # Convert Rasa answers to WhatsApp API expected format
            parser = whatsapp_event.parser_class(
                bot_answers, whatsapp_event.contact.phone
            )
            wpp_client = whatsapp_event.wpp_client
            wpp_messages = parser.parse_messages()

            # Send Rasa answers to WhatsApp
            for message in wpp_messages:
                response = wpp_client.send_message(message)
                if response.status_code != 200:
                    custom_logger("WHATSAPP EVENT ERROR", response.json())

            return HTTPResponse("ok", status=200)

        return custom_webhook
