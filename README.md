# Python Chat Application

A real-time terminal-based chat application with support for private messaging, colorized usernames, and an interactive UI. Built with Python's socket programming and threading capabilities.


<p align="center">
  <img src="https://drive.google.com/uc?export=view&id=1vf97o171y5yqfPumLRvqNh4uxROoG4B0" alt="Chat App Screenshot" width="600"/>
</p>


## Features

- 🌐 Real-time group chat
- 📱 Private messaging with `@username` syntax
- 🎨 Colorized usernames for better message distinction
- ⌨️ Interactive terminal UI with hotkeys
- 🕒 Message timestamps
- 👤 Unique username validation
- 🔄 Clean disconnection handling

## Requirements

- Python 3.6+
- Windows OS (for interactive terminal features)
- Required Python packages:
  - keyboard (for hotkey handling)
  - All other dependencies are from Python's standard library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/shahzaibahmad05/python-chat-app.git
cd python-chat-app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python server.py [host] [port]
```
Default: host=127.0.0.1, port=55555

2. Launch the client in a different terminal:
```bash
python client.py
```

3. Chat Interface Controls:
   - Press 'a' to type a new message
   - Press 'ESC' to exit
   - Type '@username message' for private messages
   - Use '/quit' to leave the chat

## Architecture

### Server (`server.py`)
- Multi-threaded TCP server handling multiple concurrent clients
- Thread-safe client management with proper cleanup
- Broadcast and private message routing
- Username uniqueness enforcement
- ANSI color support for usernames

### Client (`client.py`)
- Interactive terminal UI with real-time updates
- Separate thread for receiving messages
- Clean shutdown handling
- Message history display
- Hotkey-based input system

## Network Protocol

- TCP-based communication
- UTF-8 encoded messages
- Newline-delimited messages
- Special command prefixes:
  - '@' for private messages
  - '/quit' for disconnection

## Contributing

Feel free to open issues or submit pull requests with improvements. Some areas for potential enhancement:

- File transfer support
- Message persistence
- Emoji support
- Server commands/moderation
- Chat rooms/channels
- End-to-end encryption

## License

This project is open source and available under the MIT License.