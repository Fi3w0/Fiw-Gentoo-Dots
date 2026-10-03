# Optional Spotify customization

Spotify is installed stock. Selecting this optional setup does not patch it
automatically. The retained scripts are `optional/spotify/spotify-patch` and
`optional/spotify/spicetify-snapshotfix`.

**Unofficial Spotify modifications are optional and used at your own risk.
This project does not endorse bypassing paid features.**

The script supports the Gentoo client at `/opt/spotify/spotify-client`. It
downloads and runs SpotX-Bash and calls an existing Spicetify installation at
`~/.spicetify/spicetify`. Review the downloaded script before executing it.
Spicetify and Marketplace setup, and write permissions on the Spotify client,
must be configured explicitly for the target user. The default installer
does not grant these permissions or install a Portage ACL hook.

If you choose to use it, install the snapshot helper into `~/.local/bin` and
run the patch script as your regular user. The snapshot fix is specific to
the captured Spotify/Spicetify versions and should be reviewed against future
versions rather than assumed to work unchanged.
