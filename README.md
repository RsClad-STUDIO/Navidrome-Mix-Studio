# Navidrome Mix Studio

> Create intelligent Spotify/Plexamp-style playlists for your Navidrome music library.

Navidrome Mix Studio is a desktop companion application for Navidrome that generates intelligent playlists from your personal music library.

Instead of relying on simple shuffle playback, the application analyzes your listening history, favorites, and library metadata to create playlists that feel balanced, natural, and personalized.

Designed for self-hosted music enthusiasts, Navidrome Mix Studio brings a modern music discovery experience to your own collection while keeping your library completely under your control.

---


## Highlights

- Intelligent playlist generation based on listening history
- Four recommendation-focused mix types
- Built-in Playlist Manager
- Library statistics and analysis
- English and Japanese language support
- Native Qt desktop interface with Light and Dark Mode support

---

## Screenshots

> **Application screenshots will be added here before the first public release.**


| Main Window    | Statistics     |
| -------------- | -------------- |
| *(Screenshot)* | *(Screenshot)* |


| Playlist Manager | Settings       |
| ---------------- | -------------- |
| *(Screenshot)*   | *(Screenshot)* |


| Blocklist      | About          |
| -------------- | -------------- |
| *(Screenshot)* | *(Screenshot)* |

---

# Overview

Navidrome Mix Studio is designed to help you rediscover and organize your music library.

By connecting directly to a Navidrome server through the Subsonic API, the application analyzes your listening habits and generates playlists tailored to your preferences.

Unlike traditional shuffle playback, every playlist is created using multiple recommendation strategies that improve variety while keeping recommendations relevant.

The application currently provides four mix types:


| Mix                     | Description                                                |
| ----------------------- | ---------------------------------------------------------- |
| **Daily Mix**           | Balanced playlists for everyday listening.                 |
| **Favorites Mix**       | Focuses on your favorite tracks while maintaining variety. |
| **Discovery Mix**       | Recommends overlooked songs from your library.             |
| **Forgotten Favorites** | Brings long-unplayed favorite tracks back into rotation.   |

Beyond playlist generation, the application also provides:

- Playlist management
- Library statistics
- Blocklist management
- Multi-language support
- Native desktop experience

Together, these features make Navidrome Mix Studio a complete companion application for Navidrome users.

---

# Features

## Intelligent Mix Generation

Generate playlists that match different listening styles instead of relying on random playback.


| Mix Type                | Purpose                                            |
| ----------------------- | -------------------------------------------------- |
| **Daily Mix**           | Everyday listening based on your listening habits. |
| **Favorites Mix**       | Enjoy your favorite songs with improved variety.   |
| **Discovery Mix**       | Rediscover songs you rarely play.                  |
| **Forgotten Favorites** | Bring older favorites back into your rotation.     |

---

## Playlist Management

Manage generated playlists without leaving the application.

Features include:

- Browse playlists
- View playlist contents
- Search playlists
- Delete playlists
- Cleanup outdated generated playlists

---

## Library Analysis

Understand your music collection through built-in statistics.

Available information includes:

- Library overview
- Artist and album distribution
- Favorite statistics
- Metadata analysis
- Recommendation confidence

---

## Blocklist

Exclude unwanted songs from future playlist generation.

The blocklist is shared across all recommendation types, allowing playlists to better reflect your personal preferences.

---

## Multi-language Support

The user interface currently supports:

- English
- Japanese

Language changes are applied immediately without restarting the application.

---

## Native Desktop Interface

Built with Qt (PySide6), the application provides a responsive desktop experience using native Qt widgets.

Key characteristics include:

- Light and Dark Mode support
- Responsive layouts
- Native desktop interface
- Consistent visual design

# Requirements

Navidrome Mix Studio is designed to run on modern Windows environments and requires access to a Navidrome server.


| Component        | Requirement                        |
| ---------------- | ---------------------------------- |
| Operating System | Windows 10 / Windows 11 (64-bit)   |
| Python           | 3.11 or later*(source build only)* |
| Framework        | PySide6                            |
| Music Server     | Navidrome                          |
| API              | Subsonic API                       |
| Network          | Access to the Navidrome server     |

### Before You Begin

Prepare the following information before connecting:

- Navidrome Server URL
- Username
- Password

---

# Installation

Navidrome Mix Studio can be used either as a pre-built Windows application or by running the source code.

## Option 1 — Download a Release (Recommended)

1. Download the latest release from the GitHub **Releases** page.
2. Extract the downloaded archive.
3. Launch the executable.

No Python installation is required when using the packaged release.

---

## Option 2 — Build from Source

Clone the repository.

```bash
git clone https://github.com/<username>/navidrome-mix-studio.git
cd navidrome-mix-studio
```

Install the required packages.

```bash
pip install -r requirements.txt
```

Run the application.

```bash
python main.py
```

---

## Verify the Installation

If the application starts successfully, the main window will appear.

You are now ready to connect to your Navidrome server.

---

# Getting Started

Follow these steps to generate your first playlist.

## 1. Configure the Connection

Open **Settings** and enter your:

- Server URL
- Username
- Password

Save the configuration.

---

## 2. Connect to Navidrome

Select **Connect**.

Once the connection succeeds, your music library becomes available to the application.

---

## 3. Analyze Your Library

Navidrome Mix Studio loads information including:

- Artists
- Albums
- Songs
- Favorites
- Listening history

This information is used to build personalized recommendations.

---

## 4. Generate a Mix

Return to the main window and select one of the available mix types.

- Daily Mix
- Favorites Mix
- Discovery Mix
- Forgotten Favorites

Click **Generate** to create a playlist.

---

## 5. Save the Playlist

When you are satisfied with the generated playlist, save it directly to your Navidrome server.

The playlist immediately becomes available to any Subsonic-compatible client connected to the same server.

---

## 6. Continue Exploring

Additional features include:

- Playlist Management
- Library Statistics
- Blocklist Management
- Language Switching
- Application Settings

These tools help you organize your library and improve future recommendations.



## Important Notes

> [!IMPORTANT]
> **Use Your Regular Navidrome Account**
>
> For the best recommendation results, sign in using the same Navidrome account that you normally use for listening to music.
>
> Playlist recommendations are generated from your personal listening history, favorite tracks, and playlists.
>
> If you use an administrator account or another user's account instead of your regular account, the generated mixes may not accurately reflect your own listening preferences.
>
> If you normally listen to music using an administrator account (for example, on a single-user server), using that account is perfectly acceptable.

> [!IMPORTANT]
> **Testing Status**
>
> Navidrome Mix Studio has been thoroughly tested with its core functionality, including:
>
> * Navidrome connection
> * Playlist generation
> * Playlist management
> * Library statistics
> * Blocklist management
> * Language switching
> * Settings
> * About dialog
>
> The following features have not yet been fully verified across different environments:
>
> * Automatic Generation
> * Default Mix Settings
>
> These features are included in the application, but additional compatibility testing is still in progress.
>
> If you encounter any unexpected behavior, please open an Issue on GitHub. Your feedback helps improve future releases.
>

# Usage

Navidrome Mix Studio is designed to fit naturally into your everyday music listening workflow.

A typical workflow is shown below.

## 1. Connect to Your Library

Launch the application and connect to your Navidrome server.

Once connected, the application retrieves the information required for playlist generation.

---

## 2. Select a Mix Type

Choose the mix that best matches your current listening preference.


| Mix Type                | Best For                         |
| ----------------------- | -------------------------------- |
| **Daily Mix**           | Everyday listening               |
| **Favorites Mix**       | Listening to your favorite songs |
| **Discovery Mix**       | Exploring overlooked tracks      |
| **Forgotten Favorites** | Rediscovering older favorites    |

---

## 3. Generate a Playlist

Click **Generate** to create a new playlist.

The recommendation engine analyzes your listening history and library metadata to produce balanced and personalized recommendations.

---

## 4. Review the Results

Preview the generated playlist.

If desired, generate another playlist to explore different recommendations before saving.

---

## 5. Save to Navidrome

Save the playlist directly to your Navidrome server.

The playlist immediately becomes available from any Subsonic-compatible client connected to the same server.

---

## 6. Manage Your Playlists

The built-in Playlist Manager allows you to organize playlists without leaving the application.

Available operations include:

- Browse playlists
- View playlist contents
- Search playlists
- Delete playlists
- Cleanup generated playlists

Regular maintenance helps keep your playlist collection organized over time.

---

# Architecture & Design

Navidrome Mix Studio is built around a modular architecture that emphasizes maintainability, scalability, and long-term development.

The application separates recommendation logic, user interface, services, and localization into independent components, making the codebase easier to understand and maintain.

---

## Recommendation Engine

The recommendation engine follows a modular design based on independent processing stages.

Core technologies include:

- Strategy Pattern
- Recommendation Pipeline
- Candidate Filtering
- Scoring System
- Statistics Collection
- Confidence Evaluation
- Dataclass-based models

This design allows each recommendation stage to evolve independently while preserving the overall architecture.

---

## User Interface

The graphical interface is implemented with Qt (PySide6).

Design goals include:

- Native desktop experience
- Responsive layouts
- Light and Dark Mode support
- Clear separation between UI and application logic
- Consistent user experience across the application

---

## Internationalization

The application includes a fully integrated localization system.

Key features include:

- JSON-based translation files
- Runtime language switching
- Centralized translation management
- Easy addition of new languages

Keeping all user-facing text outside the source code simplifies maintenance and future localization.

---

## Code Quality

The project follows a consistent set of development principles.

- Modular architecture
- Separation of responsibilities
- Readable and maintainable code
- Consistent coding style
- Type hints throughout the project
- Comprehensive documentation
- GitHub release quality

These principles help ensure that the project remains easy to maintain and extend over time.

# Project Status

Navidrome Mix Studio has reached its first stable public release.

The recommendation engine, user interface, playlist management, and internationalization systems are considered feature complete. Future development will focus on improving quality and maintaining long-term stability.

---

## Current Status


| Component             | Status     |
| --------------------- | ---------- |
| Version               | **v1.0.0** |
| Release               | Stable     |
| Recommendation Engine | Complete   |
| User Interface        | Complete   |
| Playlist Manager      | Complete   |
| Internationalization  | Complete   |
| Documentation         | Complete   |

---

## Development Policy

The recommendation engine has entered **Feature Freeze**.

Future releases will primarily focus on:

- Bug fixes
- Performance improvements
- User experience refinements
- Documentation
- Long-term maintenance

Major changes to the recommendation algorithm are intentionally avoided to preserve stable and predictable playlist generation.

---

## Future Development

Planned improvements may include:

- Additional language support
- User interface refinements
- Performance optimization
- General quality-of-life improvements

Future features will continue to follow the existing architecture without compromising stability or maintainability.

---

# License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this software in accordance with the terms of the license.

See the **LICENSE** file for the complete license text.

---

# Acknowledgements

Navidrome Mix Studio is built upon several outstanding open-source projects.

Special thanks to:

- **Navidrome** — Self-hosted music server with a Subsonic-compatible API.
- **Qt / PySide6** — Cross-platform desktop application framework.
- **Python** — Programming language and ecosystem.

This project would not have been possible without the excellent work of the open-source community.

Thank you to everyone who contributes through software, documentation, testing, and shared knowledge.
