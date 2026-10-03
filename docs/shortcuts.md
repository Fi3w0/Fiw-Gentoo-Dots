# KDE shortcuts

Generated from the repo’s captured `kglobalshortcutsrc`. This describes
Fiw’s bindings as configured; applying them is a separate installer action.
It covers KDE global shortcuts, not every shortcut inside individual applications.

**67 assigned actions · 193 unassigned actions · 260 total**

`Meta` is the Super/Windows key. In the full tables, multiple keys for
one action are alternatives. Grouped summary keys match the named actions
in order. “Unassigned” means explicitly disabled in this capture;
a key in the KDE default column is not an active binding. The default
column is copied from KDE’s stored values, not inferred from a release.

## Everyday bindings

| Keys | Action |
|---|---|
| <code>Meta</code> | Open application launcher |
| <code>Meta+Space</code> | Open KRunner |
| <code>Meta+Q</code> | Open Kitty |
| <code>Alt+S</code><br><code>Meta+Shift+S</code> | Select a screenshot region |
| <code>Print</code><br><code>Alt+D</code> | Screenshot monitor under pointer |
| <code>Meta+V</code> | Show clipboard history at pointer |
| <code>Meta+1</code><br><code>Meta+2</code><br><code>Meta+3</code> | Switch to desktop 1 / 2 / 3 |
| <code>Meta+!</code><br><code>Meta+@</code><br><code>Meta+#</code> | Move window to desktop 1 / 2 / 3 |
| <code>Meta+Ctrl+Left</code><br><code>Meta+Ctrl+Right</code><br><code>Meta+Ctrl+Up</code><br><code>Meta+Ctrl+Down</code> | Switch desktop left / right / up / down |
| <code>Meta+Left</code><br><code>Meta+Right</code><br><code>Meta+Up</code><br><code>Meta+Down</code> | Tile window left / right / up / down |
| <code>Meta+Shift+Left</code><br><code>Meta+Shift+Right</code> | Move window to previous / next screen |
| <code>Meta+F</code> | Maximize window |
| <code>Meta+W</code> | Toggle Overview |
| <code>Meta+G</code> | Toggle desktop grid |
| <code>Meta+A</code><br><code>Meta+Shift+A</code> | Next / previous activity |
| <code>Screensaver</code><br><code>Meta+L</code> | Lock session |
| <code>Ctrl+Alt+Del</code> | Show logout screen |

Screenshot bindings use `fiw-shot`: copy to clipboard, then offer Save
or Edit in the notification. They need Spectacle, `wl-copy` and
`notify-send`; Kitty and KRunner bindings need their respective apps.
The native Spectacle bindings are unassigned to avoid competing actions.

The desktop-move bindings are stored as literal symbols (`!`, `@`, `#`).
On a US layout these usually mean Shift+1/2/3; other layouts can differ.
The keyboard-layout preset contains US English, Russian and Spanish;
`Meta+Alt+Space` cycles through them. Shortcut restoration does not
create three virtual desktops or activities on a new installation.

## Captured choices

Forward window switching is currently unassigned; reverse switching
uses `Alt+Shift+Tab` and `Meta+Shift+Tab`.

Other currently unassigned shortcuts include Peek at Desktop (`Meta+D`
in the default column), Minimize (`Meta+PgDown`), Restore
(`Meta+Backspace`) and the window menu (`Alt+F3`). FiwNode’s four
recorded global actions are unassigned. `Meta+1/2/3` are used for
desktops, with the corresponding task-manager shortcuts disabled.

## All assigned actions

### Keyboard Layout Switcher

| Action | Current keys | Stored KDE default |
|---|---|---|
| Switch to Next Keyboard Layout | <code>Meta+Alt+Space</code> | <code>Meta+Alt+K</code> |

### Accessibility

| Action | Current keys | Stored KDE default |
|---|---|---|
| Toggle Screen Reader On and Off | <code>Meta+Alt+S</code> | <code>Meta+Alt+S</code> |

### Audio Volume

| Action | Current keys | Stored KDE default |
|---|---|---|
| Decrease Microphone Volume | <code>Microphone Volume Down</code> | <code>Microphone Volume Down</code> |
| Decrease Volume | <code>Volume Down</code> | <code>Volume Down</code> |
| Decrease Volume by 1% | <code>Shift+Volume Down</code> | <code>Shift+Volume Down</code> |
| Increase Microphone Volume | <code>Microphone Volume Up</code> | <code>Microphone Volume Up</code> |
| Increase Volume | <code>Volume Up</code> | <code>Volume Up</code> |
| Increase Volume by 1% | <code>Shift+Volume Up</code> | <code>Shift+Volume Up</code> |
| Mute Microphone | <code>Microphone Mute</code><br><code>Meta+Volume Mute</code> | <code>Microphone Mute</code><br><code>Meta+Volume Mute</code> |
| Mute | <code>Volume Mute</code> | <code>Volume Mute</code> |

### Session Management

| Action | Current keys | Stored KDE default |
|---|---|---|
| Lock Session | <code>Screensaver</code><br><code>Meta+L</code> | <code>Screensaver</code><br><code>Meta+L</code> |
| Show Logout Screen | <code>Ctrl+Alt+Del</code> | <code>Ctrl+Alt+Del</code> |

### KWin

| Action | Current keys | Stored KDE default |
|---|---|---|
| Activate Window Demanding Attention | <code>Meta+Ctrl+A</code> | <code>Meta+Ctrl+A</code> |
| Toggle Present Windows (Current desktop) | <code>Ctrl+F9</code><br><code>Meta+F9</code> | <code>Ctrl+F9</code><br><code>Meta+F9</code> |
| Toggle Present Windows (All desktops) | <code>Launch (C)</code><br><code>Ctrl+F10</code><br><code>Meta+F10</code> | <code>Launch (C)</code><br><code>Ctrl+F10</code><br><code>Meta+F10</code> |
| Toggle Present Windows (Window class) | <code>Ctrl+F7</code><br><code>Meta+F7</code> | <code>Ctrl+F7</code><br><code>Meta+F7</code> |
| Toggle Grid View | <code>Meta+G</code> | <code>Meta+G</code> |
| Kill Window | <code>Meta+Ctrl+Esc</code> | <code>Meta+Ctrl+Esc</code> |
| Toggle Overview | <code>Meta+W</code> | <code>Meta+W</code> |
| Switch One Desktop Down | <code>Meta+Ctrl+Down</code> | <code>Meta+Ctrl+Down</code> |
| Switch One Desktop Up | <code>Meta+Ctrl+Up</code> | <code>Meta+Ctrl+Up</code> |
| Switch One Desktop to the Left | <code>Meta+Ctrl+Left</code> | <code>Meta+Ctrl+Left</code> |
| Switch One Desktop to the Right | <code>Meta+Ctrl+Right</code> | <code>Meta+Ctrl+Right</code> |
| Switch to Desktop 1 | <code>Meta+1</code> | <code>Ctrl+F1</code><br><code>Meta+F1</code> |
| Switch to Desktop 2 | <code>Meta+2</code> | <code>Ctrl+F2</code><br><code>Meta+F2</code> |
| Switch to Desktop 3 | <code>Meta+3</code> | <code>Ctrl+F3</code><br><code>Meta+F3</code> |
| Walk Through Windows (Reverse) | <code>Alt+Shift+Tab</code><br><code>Meta+Shift+Tab</code> | <code>Alt+Shift+Tab</code><br><code>Meta+Shift+Tab</code> |
| Close Window | <code>Alt+F4</code> | <code>Alt+F4</code> |
| Maximize Window | <code>Meta+F</code> | <code>Meta+PgUp</code> |
| Quick Tile Window to the Bottom | <code>Meta+Down</code> | <code>Meta+Down</code> |
| Quick Tile Window to the Left | <code>Meta+Left</code> | <code>Meta+Left</code> |
| Quick Tile Window to the Right | <code>Meta+Right</code> | <code>Meta+Right</code> |
| Quick Tile Window to the Top | <code>Meta+Up</code> | <code>Meta+Up</code> |
| Window to Desktop 1 | <code>Meta+!</code> | Unassigned |
| Window to Desktop 2 | <code>Meta+@</code> | Unassigned |
| Window to Desktop 3 | <code>Meta+#</code> | Unassigned |
| Move Window to Next Screen | <code>Meta+Shift+Right</code> | <code>Meta+Shift+Right</code> |
| Move Window to Previous Screen | <code>Meta+Shift+Left</code> | <code>Meta+Shift+Left</code> |
| Zoom to Actual Size | <code>Meta+0</code> | <code>Meta+0</code> |
| Zoom In | <code>Meta++</code><br><code>Meta+=</code> | <code>Meta++</code><br><code>Meta+=</code> |
| Zoom Out | <code>Meta+-</code> | <code>Meta+-</code> |

### Media Controller

| Action | Current keys | Stored KDE default |
|---|---|---|
| Media playback next | <code>Media Next</code> | <code>Media Next</code> |
| Pause media playback | <code>Media Pause</code> | <code>Media Pause</code> |
| Play/Pause media playback | <code>Media Play</code> | <code>Media Play</code> |
| Media playback previous | <code>Media Previous</code> | <code>Media Previous</code> |
| Media playback seek backward 5s | <code>Media Rewind</code> | <code>Media Rewind</code> |
| Media playback seek forward 5s | <code>Media Fast Forward</code> | <code>Media Fast Forward</code> |
| Stop media playback | <code>Media Stop</code> | <code>Media Stop</code> |

### Power Management

| Action | Current keys | Stored KDE default |
|---|---|---|
| Decrease Keyboard Brightness | <code>Keyboard Brightness Down</code> | <code>Keyboard Brightness Down</code> |
| Decrease Screen Brightness | <code>Monitor Brightness Down</code> | <code>Monitor Brightness Down</code> |
| Decrease Screen Brightness by 1% | <code>Shift+Monitor Brightness Down</code> | <code>Shift+Monitor Brightness Down</code> |
| Hibernate | <code>Hibernate</code> | <code>Hibernate</code> |
| Increase Keyboard Brightness | <code>Keyboard Brightness Up</code> | <code>Keyboard Brightness Up</code> |
| Increase Screen Brightness | <code>Monitor Brightness Up</code> | <code>Monitor Brightness Up</code> |
| Increase Screen Brightness by 1% | <code>Shift+Monitor Brightness Up</code> | <code>Shift+Monitor Brightness Up</code> |
| Power Down | <code>Power Down</code> | <code>Power Down</code> |
| Power Off | <code>Power Off</code> | <code>Power Off</code> |
| Suspend | <code>Sleep</code> | <code>Sleep</code> |
| Toggle Keyboard Backlight | <code>Keyboard Light On/Off</code> | <code>Keyboard Light On/Off</code> |

### plasmashell

| Action | Current keys | Stored KDE default |
|---|---|---|
| Activate Application Launcher | <code>Meta</code> | <code>Meta</code><br><code>Alt+F1</code> |
| Walk through activities | <code>Meta+A</code> | Unassigned |
| Walk through activities (Reverse) | <code>Meta+Shift+A</code> | Unassigned |
| Show Clipboard Items at Mouse Position | <code>Meta+V</code> | <code>Meta+V</code> |

### Screenshot region helper

| Action | Current keys | Stored KDE default |
|---|---|---|
| Screenshot region helper | <code>Alt+S</code><br><code>Meta+Shift+S</code> | — |

### Screenshot monitor helper

| Action | Current keys | Stored KDE default |
|---|---|---|
| Screenshot monitor helper | <code>Print</code><br><code>Alt+D</code> | — |

### Kitty launcher

| Action | Current keys | Stored KDE default |
|---|---|---|
| Kitty launcher | <code>Meta+Q</code> | — |

### KRunner launcher

| Action | Current keys | Stored KDE default |
|---|---|---|
| KRunner launcher | <code>Meta+Space</code> | — |

## All unassigned actions

These entries are restored as unassigned, including actions with a
stored KDE default. Expand each section to review the full capture.

<details>
<summary>Keyboard Layout Switcher (4)</summary>

| Action | Stored KDE default |
|---|---|
| Switch keyboard layout to English (US) | Unassigned |
| Switch keyboard layout to Russian | Unassigned |
| Switch keyboard layout to Spanish | Unassigned |
| Switch to Last-Used Keyboard Layout | <code>Meta+Alt+L</code> |

</details>

<details>
<summary>FiwNode (4)</summary>

| Action | Stored KDE default |
|---|---|
| FiwNode: next | <code>Meta+Alt+N</code> |
| FiwNode: show and search | <code>Meta+Alt+F</code> |
| FiwNode: stop | <code>Meta+Alt+S</code> |
| FiwNode: play / pause | <code>Meta+Alt+P</code> |

</details>

<details>
<summary>Audio Volume (1)</summary>

| Action | Stored KDE default |
|---|---|
| Push to talk | Unassigned |

</details>

<details>
<summary>Session Management (6)</summary>

| Action | Stored KDE default |
|---|---|
| Shut Down Without Confirmation | Unassigned |
| Log Out Without Confirmation | Unassigned |
| Log Out | Unassigned |
| Reboot | Unassigned |
| Reboot Without Confirmation | Unassigned |
| Shut Down | Unassigned |

</details>

<details>
<summary>KWin (138)</summary>

| Action | Stored KDE default |
|---|---|
| Cycle through Overview and Grid View | Unassigned |
| Cycle through Grid View and Overview | Unassigned |
| Decrease Opacity of Active Window by 5% | Unassigned |
| Toggle Tiles Editor | <code>Meta+T</code> |
| Toggle Present Windows (Window class on current desktop) | Unassigned |
| Increase Opacity of Active Window by 5% | Unassigned |
| Move the tablet to the next output | Unassigned |
| Move Mouse to Center | <code>Meta+F6</code> |
| Move Mouse to Focus | <code>Meta+F5</code> |
| Move Zoomed Area Downwards | Unassigned |
| Move Zoomed Area to Left | Unassigned |
| Move Zoomed Area to Right | Unassigned |
| Move Zoomed Area Upwards | Unassigned |
| Setup Window Shortcut | Unassigned |
| Peek at Desktop | <code>Meta+D</code> |
| Switch to Window Below | <code>Meta+Alt+Down</code> |
| Switch to Window to the Left | <code>Meta+Alt+Left</code> |
| Switch to Window to the Right | <code>Meta+Alt+Right</code> |
| Switch to Window Above | <code>Meta+Alt+Up</code> |
| Switch to Desktop 10 | Unassigned |
| Switch to Desktop 11 | Unassigned |
| Switch to Desktop 12 | Unassigned |
| Switch to Desktop 13 | Unassigned |
| Switch to Desktop 14 | Unassigned |
| Switch to Desktop 15 | Unassigned |
| Switch to Desktop 16 | Unassigned |
| Switch to Desktop 17 | Unassigned |
| Switch to Desktop 18 | Unassigned |
| Switch to Desktop 19 | Unassigned |
| Switch to Desktop 20 | Unassigned |
| Switch to Desktop 21 | Unassigned |
| Switch to Desktop 22 | Unassigned |
| Switch to Desktop 23 | Unassigned |
| Switch to Desktop 24 | Unassigned |
| Switch to Desktop 25 | Unassigned |
| Switch to Desktop 4 | <code>Ctrl+F4</code><br><code>Meta+F4</code> |
| Switch to Desktop 5 | Unassigned |
| Switch to Desktop 6 | Unassigned |
| Switch to Desktop 7 | Unassigned |
| Switch to Desktop 8 | Unassigned |
| Switch to Desktop 9 | Unassigned |
| Switch to Next Desktop | Unassigned |
| Switch to Next Screen | Unassigned |
| Switch to Previous Desktop | Unassigned |
| Switch to Previous Screen | Unassigned |
| Switch to Screen 0 | Unassigned |
| Switch to Screen 1 | Unassigned |
| Switch to Screen 2 | Unassigned |
| Switch to Screen 3 | Unassigned |
| Switch to Screen 4 | Unassigned |
| Switch to Screen 5 | Unassigned |
| Switch to Screen 6 | Unassigned |
| Switch to Screen 7 | Unassigned |
| Switch to Screen Above | Unassigned |
| Switch to Screen Below | Unassigned |
| Switch to Screen to the Left | Unassigned |
| Switch to Screen to the Right | Unassigned |
| Suspend/Resume Night Light | Unassigned |
| Toggle Window Raise/Lower | Unassigned |
| Walk Through Windows | <code>Alt+Tab</code><br><code>Meta+Tab</code> |
| Walk Through Windows Alternative | Unassigned |
| Walk Through Windows Alternative (Reverse) | Unassigned |
| Walk Through Windows of Current Application | <code>Alt+&#96;</code><br><code>Meta+&#96;</code> |
| Walk Through Windows of Current Application (Reverse) | <code>Alt+~</code><br><code>Meta+~</code> |
| Walk Through Windows of Current Application Alternative | Unassigned |
| Walk Through Windows of Current Application Alternative (Reverse) | Unassigned |
| Keep Window Above Others | Unassigned |
| Keep Window Below Others | Unassigned |
| Custom Quick Tile Window to the Bottom | Unassigned |
| Custom Quick Tile Window to the Left | Unassigned |
| Custom Quick Tile Window to the Right | Unassigned |
| Custom Quick Tile Window to the Top | Unassigned |
| Make Window Fullscreen | Unassigned |
| Expand Window Horizontally | Unassigned |
| Expand Window Vertically | Unassigned |
| Lower Window | Unassigned |
| Maximize Window Horizontally | Unassigned |
| Maximize Window Vertically | Unassigned |
| Minimize Window | <code>Meta+PgDown</code> |
| Move Window | Unassigned |
| Move Window to the Center | Unassigned |
| Toggle Window Titlebar and Frame | Unassigned |
| Keep Window on All Desktops | Unassigned |
| Window One Desktop Down | <code>Meta+Ctrl+Shift+Down</code> |
| Window One Desktop Up | <code>Meta+Ctrl+Shift+Up</code> |
| Window One Desktop to the Left | <code>Meta+Ctrl+Shift+Left</code> |
| Window One Desktop to the Right | <code>Meta+Ctrl+Shift+Right</code> |
| Move Window One Screen Down | Unassigned |
| Move Window One Screen Up | Unassigned |
| Move Window One Screen to the Left | Unassigned |
| Move Window One Screen to the Right | Unassigned |
| Window Menu | <code>Alt+F3</code> |
| Move Window Down | Unassigned |
| Move Window Left | Unassigned |
| Move Window Right | Unassigned |
| Move Window Up | Unassigned |
| Quick Tile Window to the Bottom Left | Unassigned |
| Quick Tile Window to the Bottom Right | Unassigned |
| Quick Tile Window to the Top Left | Unassigned |
| Quick Tile Window to the Top Right | Unassigned |
| Raise Window | Unassigned |
| Resize Window | Unassigned |
| Restore Window | <code>Meta+Backspace</code> |
| Shrink Window Horizontally | Unassigned |
| Shrink Window Vertically | Unassigned |
| Window to Desktop 10 | Unassigned |
| Window to Desktop 11 | Unassigned |
| Window to Desktop 12 | Unassigned |
| Window to Desktop 13 | Unassigned |
| Window to Desktop 14 | Unassigned |
| Window to Desktop 15 | Unassigned |
| Window to Desktop 16 | Unassigned |
| Window to Desktop 17 | Unassigned |
| Window to Desktop 18 | Unassigned |
| Window to Desktop 19 | Unassigned |
| Window to Desktop 20 | Unassigned |
| Window to Desktop 21 | Unassigned |
| Window to Desktop 22 | Unassigned |
| Window to Desktop 23 | Unassigned |
| Window to Desktop 24 | Unassigned |
| Window to Desktop 25 | Unassigned |
| Window to Desktop 4 | Unassigned |
| Window to Desktop 5 | Unassigned |
| Window to Desktop 6 | Unassigned |
| Window to Desktop 7 | Unassigned |
| Window to Desktop 8 | Unassigned |
| Window to Desktop 9 | Unassigned |
| Window to Next Desktop | Unassigned |
| Window to Previous Desktop | Unassigned |
| Move Window to Screen 0 | Unassigned |
| Move Window to Screen 1 | Unassigned |
| Move Window to Screen 2 | Unassigned |
| Move Window to Screen 3 | Unassigned |
| Move Window to Screen 4 | Unassigned |
| Move Window to Screen 5 | Unassigned |
| Move Window to Screen 6 | Unassigned |
| Move Window to Screen 7 | Unassigned |
| Disable Active Input Capture | <code>Meta+Shift+Esc</code> |

</details>

<details>
<summary>Media Controller (5)</summary>

| Action | Stored KDE default |
|---|---|
| Media volume down | Unassigned |
| Media volume up | Unassigned |
| Play media playback | Unassigned |
| Media playback seek backward 30s | Unassigned |
| Media playback seek forward 30s | Unassigned |

</details>

<details>
<summary>Power Management (2)</summary>

| Action | Stored KDE default |
|---|---|
| Turn Off Screen | Unassigned |
| Switch Power Profile | <code>Battery</code><br><code>Meta+B</code> |

</details>

<details>
<summary>plasmashell (25)</summary>

| Action | Stored KDE default |
|---|---|
| Next Wallpaper Image | Unassigned |
| Activate Task Manager Entry 1 | <code>Meta+1</code> |
| Activate Task Manager Entry 10 | Unassigned |
| Activate Task Manager Entry 2 | <code>Meta+2</code> |
| Activate Task Manager Entry 3 | <code>Meta+3</code> |
| Activate Task Manager Entry 4 | <code>Meta+4</code> |
| Activate Task Manager Entry 5 | <code>Meta+5</code> |
| Activate Task Manager Entry 6 | <code>Meta+6</code> |
| Activate Task Manager Entry 7 | <code>Meta+7</code> |
| Activate Task Manager Entry 8 | <code>Meta+8</code> |
| Activate Task Manager Entry 9 | <code>Meta+9</code> |
| Clear Notification History | Unassigned |
| Clear Clipboard History | Unassigned |
| Automatic Action Popup Menu | <code>Meta+Ctrl+X</code> |
| Move keyboard focus between panels | <code>Meta+Alt+P</code> |
| Next History Item | Unassigned |
| Previous History Item | Unassigned |
| Edit Contents… | Unassigned |
| Show Activity Switcher | <code>Meta+Q</code> |
| Manually Invoke Action on Current Clipboard | Unassigned |
| Show Desktop | <code>Ctrl+F12</code> |
| Show Barcode… | Unassigned |
| Switch to Next Activity | Unassigned |
| Switch to Previous Activity | Unassigned |
| Toggle do not disturb | Unassigned |

</details>

<details>
<summary>services][org.kde.kscreen.desktop (1)</summary>

| Action | Stored KDE default |
|---|---|
| ShowOSD | — |

</details>

<details>
<summary>services][org.kde.spectacle.desktop (7)</summary>

| Action | Stored KDE default |
|---|---|
| ActiveWindowScreenShot | — |
| CurrentMonitorScreenShot | — |
| FullScreenScreenShot | — |
| OpenWithoutScreenshot | — |
| RectangularRegionScreenShot | — |
| WindowUnderCursorScreenShot | — |
| _launch | — |

</details>

## Refresh the reference

```sh
python3 tools/shortcuts.py
```

Run this after reviewing a shortcut capture or changing the preset.
The generator reads repo files only and does not change live KDE settings.
