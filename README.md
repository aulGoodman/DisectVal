# DisectVal - Valorant Gameplay Analysis AI

<p align="center">
  <strong>Analyze • Learn • Improve</strong>
</p>

DisectVal is an AI-powered gameplay analysis tool for Valorant. It analyzes your gameplay footage to provide insights, track your performance, and help you improve your skills.

## Features

### 🔐 Secure Authentication
- Encrypted credential storage with PBKDF2 key derivation
- Role-based access control (User, Admin, Developer)
- Machine-specific encryption keys

### 🎮 Gameplay Analysis
- **Video Analysis**: Process gameplay footage to detect kills, deaths, and game events
- **Sensitivity Tracking**: Analyze aim patterns and suggest sensitivity adjustments
- **Settings Suggestions**: Recommend Raw Accel or Intercept Mouse for aim improvement
- **Position Data**: Track player positioning and suggest better plays

### 🖥️ Modern GUI
- Dark theme with transparent colors and shadows
- Bold text with subtle shadow effects
- Responsive sidebar navigation
- Animated UI elements

### 📊 Dashboard Tabs
- **Home**: Top clips from recent games
- **Career**: Match history and performance tracking
- **Ranked**: In-depth analytics and improvement areas
- **AI Summary**: Timeline of events with AI-generated insights
- **PC Check**: Windows settings optimization checklist
- **Admin**: Developer tools and AI training (dev access only)

### ⚙️ PC Optimization
- Power plan settings check
- Mouse acceleration detection (Enhance pointer precision)
- Windows Game Mode verification
- Graphics settings recommendations
- Network optimization tips

### 🛡️ Valorant Detection
- Detects when Valorant is running
- Can block input during gameplay (configurable)
- Developer override for SGM user

## Installation

### Requirements
- Python 3.10 or higher
- Windows 10/11 (for full functionality)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Saulgoodmantm/DisectVal.git
cd DisectVal

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m disectval.main
```

### For Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/
```

## Default Accounts

The application comes with two pre-configured accounts:

| Username | Password | Role |
|----------|----------|------|
| SGM | *(encrypted)* | Developer |
| RIOT | *(encrypted)* | Admin |

> ⚠️ Credentials are encrypted and stored securely. The passwords are not stored in plain text.

## Architecture

```
src/disectval/
├── auth/              # Authentication & authorization
│   ├── credentials.py # Encrypted credential management
│   └── roles.py       # Role-based permissions
├── gui/               # User interface
│   ├── theme.py       # UI theme and styling
│   ├── login_page.py  # Login screen
│   └── dashboard.py   # Main application dashboard
├── analysis/          # Gameplay analysis
│   └── video_analyzer.py # Video processing and event detection
├── utils/             # Utilities
│   ├── valorant_detector.py # Valorant process detection
│   └── windows_checker.py   # Windows settings optimization
├── config/            # Configuration
│   └── settings.py    # App settings management
└── main.py           # Application entry point
```

## Security Features

- **Encrypted Credentials**: User credentials are encrypted using Fernet symmetric encryption
- **PBKDF2 Key Derivation**: 480,000 iterations for key derivation
- **Machine-Specific Keys**: Encryption keys are derived from machine-specific identifiers
- **Password Hashing**: Passwords are salted and hashed with SHA-256
- **Secure Comparisons**: Constant-time comparison for password verification

## Riot API Compliance

This application is designed to comply with [Riot Games Developer API Policy](https://developer.riotgames.com/docs/valorant#developer-api-policy):

- ✅ No scouting (seeing opponent stats before match)
- ✅ No real-time performance-altering overlays
- ✅ Post-game analysis and coaching focus
- ✅ Learning and reflection based improvement

## Roadmap

- [ ] Riot API integration for match history
- [ ] YouTube video training support
- [ ] Cloud sync for training data
- [ ] Installer/Setup wizard
- [ ] Browser-based login integration
- [ ] Replay analysis support

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

<p align="center">
  <em>Built for the Valorant community</em>
</p>
