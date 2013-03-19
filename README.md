Snapshot plugin for Sublime Text 2
====

Snapshot is a simple plugin that makes backups (snapshots) of the file you are editing. By default it prunes all old snapshots after two weeks.

You can configure Snapshot to ignore certain file types, extensions and directories when deciding to backup.

Important configuration options:
----

  - `backup_dir`: Your backup directory '~/Documents/Sublime Text 2 Backups'
  - `prune_backups_after_days`: Number of days of snapshots to keep. Each day's snapshots are stored in a separate folder.
  - `enabled`: true | false
  
Hotkeys:
----
  - `cmd+super+b`: view snapshots of the current file.
  - `cmd+shift+c`: force a snapshot creation in the special 'snapshots' folder.

Installation
-----

Just copy or clone it to your Sublime Packages folder.