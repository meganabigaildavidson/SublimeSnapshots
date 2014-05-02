Snapshot plugin for Sublime Text 2/3
====

Snapshot is a simple plugin that makes backups (snapshots) of the file you are editing. By default it prunes all old snapshots after two weeks.

You can configure Snapshot to ignore certain file types, extensions and directories when deciding to backup.

Important configuration options:
----

  - `backup_dir`: Your backup directory '~/Documents/Sublime Text Backups'
  - `prune_backups_after_days`: Number of days of snapshots to keep. Each day's snapshots are stored in a separate folder.
  - `enabled`: true | false


General configuration options:
----

  - `max_backup_file_size_bytes `: This is in bytes, the default size is 256KB, any file larger than this will not be backed up
  - `display_limit `: The number of files to display in the view snapshots list (lower shows less files but faster).
  - `quick_view `: true | false - If true then the snapshot view will open in the same window as the original file
  - `exclude_dir`: A list of folders to not automatically backup
  - `exclude_files `: A list of filenames to not automatically backup
  - `exclude_extensions `: A list of filetypes to not automatically backup


Hotkeys:
----
  - `cmd+super+b`: view snapshots of the current file.
  - `cmd+shift+c`: force a snapshot creation in the special 'snapshots' folder.


Installation
-----

Just copy or clone it to your Sublime Packages folder.