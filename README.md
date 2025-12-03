# AstrBot WeChat857 Adapter

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/fluidcat/astrbot_plugin_wechat857_adapter)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

A WeChat857 adapter plugin for AstrBot, enabling WeChat integration with the AstrBot framework.

## Features

- 🤖 WeChat857 protocol support
- 📱 Message handling and processing
- 💬 Support for various message types (text, images, files, etc.)
- 🔔 Event handling and notifications
- 🎯 Custom filtering for WeChat857 platform
- 🚀 Hot-reload support for development

## Requirements

- Python 3.11 or higher
- AstrBot 4.5.1 or higher
- defusedxml >= 0.7.1
- pymediainfo ~= 7.0.1

## Installation

### Prerequisites

1. Ensure you have Python 3.11+ installed
2. Install AstrBot framework
3. Install the required dependencies:

```bash
pip install defusedxml>=0.7.1 pymediainfo~=7.0.1
```

### Plugin Installation

1. Clone this repository:
```bash
git clone https://github.com/fluidcat/astrbot_plugin_wechat857_adapter.git
cd astrbot_plugin_wechat857_adapter
```

2. Install the plugin:
```bash
pip install -e .
```

3. Or install directly from source:
```bash
pip install git+https://github.com/fluidcat/astrbot_plugin_wechat857_adapter.git
```

## Configuration

The plugin will automatically integrate with AstrBot's configuration system. No additional configuration files are required.

## Usage

### Basic Integration

The plugin automatically registers itself with AstrBot's platform system. Once installed, WeChat857 events will be processed by the AstrBot framework.

### Message Handling

The adapter supports various WeChat message types including:
- Text messages
- Image messages
- File messages
- Emoji messages
- Quote messages
- And more...

### Event Processing

Events are processed through the `WeChat857Event` class, which handles:
- Message routing
- Event filtering
- Platform-specific processing

## Development

### Project Structure

```
astrbot_plugin_wechat857_adapter/
├── main.py                 # Main plugin entry point
├── wechat857_adapter.py    # Core adapter implementation
├── wechat857_event.py      # Event handling logic
├── client/                 # WeChat857 client implementation
│   ├── __init__.py
│   ├── base.py
│   ├── chatroom.py
│   ├── client_uri.py
│   ├── errors.py
│   ├── friend.py
│   ├── hongbao.py
│   ├── login.py
│   ├── message.py
│   ├── tool.py
│   └── user.py
├── messsage_decorator.py   # Message decoration utilities
├── metadata.yaml          # Plugin metadata
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies
└── README.md              # This file
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run the plugin with AstrBot
# (Refer to AstrBot documentation for specific test commands)
```

### Hot Reload

The plugin supports hot-reload functionality for development. Changes to the plugin code will be automatically reloaded without restarting the entire AstrBot instance.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: fluidcat
- 🐛 Issues: [GitHub Issues](https://github.com/fluidcat/astrbot_plugin_wechat857_adapter/issues)
- 📖 Documentation: [AstrBot Documentation](https://docs.astrbot.com/)

## Acknowledgments

- [AstrBot Framework](https://github.com/AstrBot/AstrBot) - The underlying framework
- WeChat857 Community - For protocol support and inspiration

---

**Note**: This plugin is not affiliated with or endorsed by Tencent or WeChat. Use at your own risk and in compliance with applicable laws and regulations.