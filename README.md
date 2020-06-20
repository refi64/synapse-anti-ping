# synapse-anti-ping

An antispam module for Synapse with some nice anti-spam functionality, designed for use with
Mjolnir.

## Background

antiping has some distinct features to complement Mjolnir:

- More flexible spam text detection, featuring multiple "weighted" levels
  - In particular, it can handle image and ping spam in a more strict fashion
- Warns the user before a ban to avoid nasty accidents

Please read this guide thoroughly before attempting to try antiping!

**NOTE:** I am not terribly familiar with Synapse's internals, and I am not responsible for any
insanity this module may cause.

### Weights

The idea behind antiping's moderation actions is *weights*. Every message a user sends to a room
is assigned both a weight, representing the potential that the message is spam, and a duration
after which the weight expires. At each message, the sum of all non-expired weights is compared to
a customizable *spam limit*, and if it's above the limit, antiping will tell Mjolnir to treat the
message as spam, as well as notify the user.

In addition, there is a *ban limit* defined. If the sum of all active weights is above the ban
limit, antiping will send a message to Mjolnir to ban the user and redact their messages.

## Setup

### Initial setup

You need the following requirements:

- Mjolnir must be available
- A new user (admin / moderator privileges are not needed) with access to the Mjolnir moderation
  room and the optional log room if available (see below)
- (Recommended) A room for antiping to log spam notifications and bans to. You can, however, just
  set this to be the same room as your Mjolnir private moderation room.

### Installing the antispam module

The easiest way to get started is to use the premade Docker image
`gcr.io/refi64/synapse-with-antispam`, which is rebuilt nightly with the latest Synapse release,
plus the latest Mjolnir and antiping code. Of course, you still have to write the configuration
(see below for details).

If you want to install it by hand, just
`pip install git+https://github.com/refi64/synapse-anti-ping` to grab it straight from Git.
Note that this *must* be installed to the same environment as Mjolnir and Synapse itself, e.g.
installing to a venv won't work.

## Configuration

### Basics

This assumes Mjolnir has already been set up.

Add antiping to the spam_checker list in Synapse's homeserver.yaml:

```yaml
spam_checker:
  - module: mjolnir.AntiSpam
    config:
      # ...
  - module: synapse_anti_ping.AntiSpam
    config:
      # antiping configuration goes here
```

In addition, you will see several references to an *internal room ID*. This is **not** the
standard Matrix `#room:server` syntax. Rather, you can find this ID from Riot by right clicking
on a room -> Settings -> Advanced -> copy the "Internal room ID" value.

antiping *must* be invited to any rooms is expected to be a part of, whether that be via spam
tracking or the log / moderator rooms.

Here is an outline of the configuration file (all sections / values not labeled "optional" are
**mandatory**):

```yaml
log:
  # The *internal room ID* where antiping will send log messages to.
  # antiping's spam prevention will be disabled for this room.
  room: '!fzudtIVZXwoDAWfWYm:my-server'
mjolnir:
  # The Mjolnir ban list where users banned by antiping will be placed.
  banlist: bans
  # The *internal room ID* of Mjolnir's moderation room, i.e. the room where commands
  # may be sent for Mjolnir to execute.
  room: '!vthAvRCfHpuOlyZYiP:my-server'
user:
  # The username of antiping's user
  user: antiping
  # The password for antiping's user
  password: antiping-password
  # OPTIONAL: The homeserver to connect to. This is particularly useful if one or both of the
  # log/moderation room have e2e enabled, as then you will have to use pantalaimon (see below
  # for more details).
  homeserver: http://my-homeserver.chat/
# OPTIONAL: Room inclusion and exclusion lists. Note that all of these use Python 3's glob syntax
# for matching internal room IDs / usernames: https://docs.python.org/3/library/fnmatch.html
rooms:
  # All *internal room IDs* in the "include" list will be moderated by antiping. The default is
  # ['*']; in other words, *all* rooms are expected to be moderated.
  include:
    - ...
  # Any *internal room IDs* in the "exclude" list will *not* be moderated by antiping. This
  # overrides the include list above; i.e., a room is only moderated if it *is* in the include
  # list and *is not* in the exclude list. The default is [] (empty).
  exclude:
    - ...
# OPTIONAL: Member exclusion lists.
members:
  # Any full user names (i.e. `@user:server` syntax) here will not have their activities
  # monitored. It's recommended to put moderators in this list and *required* to put Mjolnir.
  exclude:
    - ...
# OPTIONAL: Configuration for moderation policies.
offences:
  # Customizes the different weights for different user actions. See below for more details.
  text_spam: ...
  media_spam: ...
  mentions: ...
  mass_mentions: ...
  # Defines the message to send to a user when their activity is considered "spam". Defaults to
  # "Stop spamming."
  spam_alert: Cool it!
  # Defines the spam and ban limit, as mentioned in the initial sections (the values listed below
  # are the defaults).
  limits:
    spam: 20
    ban: 30
  # See the offence configuration section below for information on this.
  history_size: 20
  # Sets how often expired offences are removed from the offence lists.
  gc_interval_minutes: 5
```

### Customizing offence rules

There are four different categories of messages (poorly termed as "offences") that antiping can
track:

- Text: Plain text messages fall here if they don't fall under any of the "ping" categories.
- Media: Messages with video, audio, or images fall here.
- Mentions: Any messages with a small number of pings / mentions fall here.
- Mass mentions: Any messages with a number of pings above a user-customizable limit fall here.

Each of these offences can be individually disabled. Note that, however, if you disable any but
leave the text offence enabled, any messages that would have fallen under the others will still
fall under "text".

These are configured using the following keys:

```yaml
offences:
  # Text category
  text_spam: ...
  # Media category
  media_spam: ...
  # Mentions category
  mentions: ...
  # Mass mentions category
  mass_mentions: ...
```

The individual sections have the following keys available (defaults are listed later on):

```yaml
offences:
  # Just as an example, these keys apply to *any* of the offence sections:
  text_spam:
    # Is this offence enabled? Defaults to 'true'.
    enabled: true
    # What numeric weight is assigned to this offence?
    weight: ...
    # How many minutes until this event expires? Can be a float to represent a fraction of a minute.
    expires_minutes: ...
```

Here are the defaults:

```yaml
offences:
  text_spam:
    enabled: true
    weight: 2
    expires_minutes: 0.5
  media_spam:
    enabled: true
    weight: 4
    expires_minutes: 0.5
  mentions:
    enabled: true
    weight: 5
    expires_minutes: 0.5
  mass_mentions:
    enabled: true
    weight: 10
    expires_minutes: 1
```

In addition, `mass_mentions` has one more option, `upgrade_at`. This is an int that defines how
many pings a message needs to have before it is considered a "mass mention". The default is 5.

There is one more important concept tied to this: history. Offences need to be tracked, thus they
are stored in the *history* (optimized for removing expired offences). The size of this is
critical: if the list is too small, it will be impossible to save enough events to monitor the
offences will smaller weights, such as text spam. The default size is `20`, which is large neough
for some extra wiggle room for experimentation.

## Important notes

**Read this section thoroughly!**

- Just like with Mjolnir, antiping should have rate limiting removed. The only way to do this at
  the moment is to
  [run a direct database insertion](https://github.com/matrix-org/synapse/issues/6286).
- You must add Mjolnir to the member exclusion list, and ideally also add the server-wide
  moderators.
- antiping must be invited into *every* room it is expected to moderate (i.e. anything matched
  by the rooms include list). Otherwise, it will still have an effect at tagging spam and banning
  the user, but will be unable to notify them outside of Matrix's default spam alerts.
- If your moderation room and/or log room use e2e, antiping should have its homeserver set to a
  Pantalaimon instance, again just like Mjolnir.
- It is recommended to disable Mjolnir's built-in anti-flood protection if enabled (see
  `!mjolnir protections`), as antiping has equivalent but more flexible functionality anyway, and
  it would be confusing to the members to have two different sets of anti-spam rules in use.
