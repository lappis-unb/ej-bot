# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.3.10] - Jul 8, 2024

### Added

- Adds support to receive webhook events from Serpro WhatsApp API.

## [0.3.9] - Jul 4, 2024

### Added

- Adds PostgresSQL as TrackerStore 

### Changed

- Improves messages formating with bold.

## [0.3.8] - Jul 4, 2024

### Added

- Allows the user to stop voting by sending the "stop" intent during the conversation.

### Changed

- Shows conversation title after starting a new conversation with the /start command.

### Fixed

- Set carry_over_slots_to_new_session to false. This will fix a bug when user takes to long to answer.

### Removed

- Removes unused intents.

## [0.3.7] - Jul 2, 2024

### Changed

- increases session_expiration_time
- logs whatsapp events in custom_channel 

## [0.3.6] - Jul 2, 2024

### Changed

- Use Redis as Lock Store

## [0.3.5] - Jun 26, 2024

### Changed

- Read recipient phone number from WhatsApp Event, insted of WhatsApp Message

## [0.3.4] - Jun 26, 2024

### Changed

- Pass WhatsApp recipient phone number as Rasa sender_id field.


## [0.3.3] - Jun 24, 2024

### Added
- When beginning a new conversation during the voting, the chatbot will request the new conversation to the EJ API.
- When the user sends a text that isn't a valid vote option, the chatbot will return a warning message and will show a new comment to vote on.
- When the user sends a text at the beginning of the research that isn't valid to initiate participation, the chatbot will return a help message.
- When the user starts the research only with the `/start` command (without and ID), the chatbot will return a help message.

### Changed

- By default, the chatbot will not use Rasa cache to train the NLU model.
