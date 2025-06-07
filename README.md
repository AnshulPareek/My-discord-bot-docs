# Discord Leveling & Moderation Bot

A feature-rich Discord bot built with `discord.py` supporting:

- Role assignment/removal by role ID
- User leveling system with XP and rank leaderboard
- Role rewards based on user level
- Announcements with embedded messages
- Wikipedia search command
- Moderation commands: ban, tempban, kick, mute, unmute, nick, clear
- Captcha verification (if included)
- User and server info commands
- Custom help command
- Audit logging
- Graceful bot shutdown command
- Error handling with user-friendly messages

---

## Features

### Role Management
- Assign or remove roles by ID with permission checks
- Prevents assigning roles higher than bot or command user
- Commands: `!role <user> <role_id>`, `!removerole <user> <role_id>`

### Leveling System
- XP gained by user messages with cooldown (3 seconds)
- Level calculated using `level = int((xp // 50) ** 0.5)`
- Level-up notifications with embedded messages and anime GIFs
- Leaderboard of top users with levels and XP
- Commands: `!level [user]`, `!leaderboard` (aliases: `!rank`, `!lb`)
- Admin commands: `!resetlevel <user>`, `!setlevel <user> <level>`
- Role assignment based on level thresholds

### Moderation Commands
- Ban, tempban, kick, mute, unmute, nickname change, clear messages
- Captcha verification on join (if implemented)
- Command permission checks via `@is_authorized` decorator

### Utility Commands
- Wikipedia search: `!search <query>` (restricted channel)
- User info: `!userinfo [user]`
- Server info: `!serverinfo`
- Announcements: `!announce <message>` (restricted channel)
- Shutdown bot: `!offline`

### Error Handling
- Handles permission errors, missing arguments, bad input gracefully
- Informative messages sent on errors

---

## Setup Instructions

1. **Clone the repository:**
   ````
   git clone [https://github.com/AnshulPareek/My-discord-bot-docs]

2. **Install dependencies:**
   ```
    pip install -r requirements.txt

3. **Configure environment variables:**
Create a .env file or set environment variables with your Discord bot token:
  ```
  DB_HOST=your_database_host
  DB_NAME=your_database_name
  DB_USER=your_database_usee
  DB_PASSWORD=your_database_password
  TOKEN=your_discord_bot_token_here
```
4. **Configure constants in your bot code:**
Update channel IDs and role IDs such as:
```
  ANNOUNCE_CHANNEL_ID = your_announce_channel_id  
  AUDIT_LOG_CHANNEL_ID = your_audit_log_channel_id
  LEVEL_CHANNEL_ID = your_level_channel_id
  SEARCH_CHANNEL_ID = your_search_channel_id
```
5. **Database setup:**
Ensure you have a PostgreSQL database setup and the necessary tables created for levels and XP tracking. Update database connection details in your code.

6. **Run the bot:**
python bot.py

## COMMANDS 

| Command                        | Description                                                 | Permission      |
| ------------------------------ | ----------------------------------------------------------- | --------------- |
| `!role <user> <role_id>`       | Assign role by ID to a user                                 | Moderator/Admin |
| `!removerole <user> <role_id>` | Remove role by ID from a user                               | Moderator/Admin |
| `!offline`                     | Shutdown the bot gracefully                                 | Moderator/Admin |
| `!announce <message>`          | Send an announcement embed                                  | Moderator/Admin |
| `!level [user]`                | Show level and XP of user                                   | Everyone        |
| `!leaderboard`, `!rank`, `!lb` | Show top users leaderboard                                  | Everyone        |
| `!resetlevel <user>`           | Reset level and XP of user                                  | Moderator/Admin |
| `!setlevel <user> <level>`     | Set level and XP of user                                    | Moderator/Admin |
| `!search <query>`              | Search Wikipedia (in search channel only)                   | Everyone        |
| `!userinfo [user]`             | Show user info                                              | Everyone        |
| `!serverinfo`                  | Show server info                                            | Everyone        |
| **Moderation commands:**       | `ban`, `tempban`, `kick`, `mute`, `unmute`, `nick`, `clear` | Moderator/Admin |

## Notes
The bot requires appropriate permissions in your server (Manage Roles, Manage Messages, Embed Links, etc.)
Make sure the bot’s highest role is above any roles it should manage.
The leveling role rewards feature can be customized by editing the level_roles dictionary in the code.
The bot uses an XP cooldown to prevent spam leveling.

## Contributing
Feel free to open issues or submit pull requests with improvements or bug fixes.

## License
This project is licensed under the MIT License - see the **https://opensource.org/license/MIT** file for details.

Made with ❤️ by Anshul Pareek
