import sublime, sublime_plugin
import os, sys, shutil, re, hashlib, math
import locale, time, datetime

class Snapshots(sublime_plugin.EventListener):

	"""Does an automatic backup of every file you save, if it's been modified only.
	currently the script does not support keeping file system resource fork data about the script being backed up"""

	# class properties
	exclude = False
	modified = False

	def on_modified(self, view):

		"""This runs when the file has been modified"""

		self.modified = True

	def on_pre_save(self, view):

		"""When a file is saved, and there is no backup of it yet, create a
		backup of the original file before saving the new, modified version."""

		buffer_file_name = view.file_name()
		file_name = os.path.basename(buffer_file_name)

		# stop processing if we cannot backup the file
		if self.can_backup(view) == False:
			return

		# check to see if we have the backup directory '2011-07-23'
		buffer_file_name = view.file_name()
		backup_dir = self.get_backup_dir()

		# create the backup file name
		file_name = os.path.basename(buffer_file_name)
		backup_name = os.path.join(backup_dir, file_name)

		# check to see if the file should be excluded form the backup
		if self.is_excluded( buffer_file_name ):
			self.exclude = True
			return
		else:
			self.exclude = False

		# backup of original file already exists
		if os.path.isfile(backup_name):
			return

		# backup the file
		try:
			shutil.copy(buffer_file_name, backup_name)
		except IOError as err:
			self.log("I/O error({0}): {1}".format(err.errno, err.strerror))
		except:
			self.log("Unexpected error:", sys.exc_info()[0])
		finally:
			# set as not modified since the last save
			self.modified = False

	def on_post_save(self, view):

		"""When a file is saved, put a copy of the file into the
		backup directory"""

		# stop processing if we cannot backup the file
		if self.can_backup(view) == False:
			return

		# we need to check to see how many weeks backup files they want to keep
		self.prune_backups();

		# check to see if we have the backup directory '2011-07-23'
		buffer_file_name = view.file_name()
		backup_dir = self.get_backup_dir()

		# create the backup filename
		file_name = self.timestamp_file( os.path.basename(buffer_file_name) )
		backup_name = os.path.join(backup_dir, file_name)
		if backup_name != None:
			try:
				shutil.copy(buffer_file_name, backup_name)
			except IOError as err:
				self.log("I/O error({0}): {1}".format(err.errno, err.strerror))
			except:
				self.log("Unexpected error:" + sys.exc_info()[0])
			finally:
				# mark it as not modified since the last save
				self.modified = False

	def can_backup(self, view):

		"""Check to see if we can backup the file."""

		# we need to check to see how many weeks backup files they want to keep
		settings = sublime.load_settings('Snapshots.sublime-settings')
		max_backup_file_size_bytes = int(settings.get("max_backup_file_size_bytes"))

		# this list is getting to long, you get the idea :)
		if self.is_enabled() == False or self.modified == False or self.exclude == True or view.size() == 0 or (max_backup_file_size_bytes != 0 and view.size() > max_backup_file_size_bytes):
			return False
		else:
			return True

	def prune_backups(self):

		"""Prune any old backups, if pruning days are set greater than 0"""

		# we need to check to see how many weeks backup files they want to keep
		settings = sublime.load_settings('Snapshots.sublime-settings')
		prune_backups_after_days = int(settings.get("prune_backups_after_days"))

		# stop processing if we are disabled, not modified, 0 in size or in the settings exclusions
		if self.is_enabled() == False or prune_backups_after_days == 0:
			return

		# prune any folders greater than x amount of days (using the directory as the date check)
		pruned_dirs = 0
		now = int(datetime.datetime.today().strftime('%Y%m%d'))
		for dirname, dirnames, filenames in os.walk(self.get_backup_dir_root()):
			for directory in dirnames:
				path = str(os.path.join(dirname, directory))
				if os.path.isdir( path ) and  directory != 'Snapshots':
					dir_date = int(directory.replace('-', ''));
					if ((now - dir_date) >= prune_backups_after_days):
						try:
							shutil.rmtree(path)
							pruned_dirs = pruned_dirs + 1
						except OSError as e:
							self.log(e)

		return str(pruned_dirs) + " snapshot directories pruned."

	def display_limit(self):

		"""Gets the number of copies to file per backup or each file"""

		settings = sublime.load_settings('Snapshots.sublime-settings')
		limit = settings.get("display_limit")

		if (limit is None):
			return 0 # unlimited backups of a single file
		else:
			return limit

	def is_excluded(self, file_name):

		"""This checks to see if the file is in any of the exclude lists"""

		exclude = False

		# get the exclude setting values
		settings = sublime.load_settings('Snapshots.sublime-settings')
		exclude_dir = settings.get("exclude_dir")
		exclude_files = settings.get("exclude_files")
		exclude_extensions = settings.get("exclude_extensions")

		# get the file extension and parent path
		parent_dir, extension = os.path.splitext(file_name)

		# see if the files should be excluded
		if extension in exclude_extensions or parent_dir in exclude_dir or file_name in exclude_files:
			exclude = True

		return exclude

	def is_enabled(self):

		"""Check to see if the plugin is enabled to do backups"""

		settings = sublime.load_settings('Snapshots.sublime-settings')
		option = settings.get("enabled")

		if (option is None):
			return False
		else:
			return option

	def get_backup_dir_root(self):

		"""This gets the main root backup directory"""

		settings = sublime.load_settings('Snapshots.sublime-settings')
		backup_dir = settings.get("backup_dir")

		if (backup_dir is None):
			self.log("No backup dir specified")
		else:

			# check to see if the path starts with a ~ and use os.path.expanduser if so then we need to do something different for windows
			if backup_dir.startswith('~'):
				backup_dir = os.path.expanduser( backup_dir )

			# make sure that we have a directory to write into
			if not os.path.exists(backup_dir):
				try:
					os.makedirs(backup_dir)
				except IOError as e:
					if e.errno == errno.EACCES:
						sublime.error_message('Unable to create root backup folder' + backup_dir)
		return backup_dir

	def get_backup_dir(self):

		"""This gets the backup directory for the current day, i.e. 2012-01-02"""

		settings = sublime.load_settings('Snapshots.sublime-settings')
		backup_dir = settings.get("backup_dir")

		if (backup_dir is None):
			sublime.error_message('No backup dir specified in the settings')
		else:

			# check to see if the path starts with a ~ and use os.path.expanduser if so then we need to do something different for windows
			if backup_dir.startswith('~'):
				backup_dir = os.path.expanduser( backup_dir )

			now = datetime.datetime.today()
			backup_dir = "%s%s%04d-%02d-%02d" % ( backup_dir, os.sep, now.year, now.month, now.day)

			# make sure that we have a directory to write into
			if not os.path.exists(backup_dir):
				try:
					os.makedirs(backup_dir)
				except IOError as e:
					if e.errno == errno.EACCES:
						sublime.error_message('Unable to create backup folder' + backup_dir)

		return backup_dir

	def get_snapshot_backup_dir(self):

		"""This returns the snapshot directory"""

		settings = sublime.load_settings('Snapshots.sublime-settings')
		backup_dir = settings.get("backup_dir")

		if (backup_dir is None):
			sublime.error_message('No backup dir specified in the settings')
		else:
			# check to see if the path starts with a ~ and use os.path.expanduser if so then we need to do something different for windows
			if backup_dir.startswith('~'):
				backup_dir = os.path.expanduser( backup_dir )

			# os.sep = / and os.pathsep = : (work out which of they are using, then determine the path they are using)
			backup_dir = backup_dir + os.sep + 'Snapshots'

			# make sure that we have a directory to write into
			if not os.path.exists(backup_dir):
				try:
					os.makedirs(backup_dir)
				except IOError as e:
					if e.errno == errno.EACCES:
						sublime.error_message('Unable to create snapshot backup folder' + backup_dir)

		return backup_dir

	def log(self, message):

		"""Prints out a message to the Sublime console"""

		settings = sublime.load_settings('Snapshots.sublime-settings')
		display_errors = settings.get("display_errors")

		if display_errors == True:
			sublime.error_message('Unable to create backup folder' + backup_dir)
		else:
			print("Log : %s", str(message))

	def md5Checksum(self, filePath):

		"""Gets the md5 checksum of the passed file"""
		digest = None

		try:
			fh = open(filePath, 'rb')
			m = hashlib.md5()
			while True:
				data = fh.read(8192)
				if not data:
					break
				m.update(data)
			digest =  m.hexdigest()
		except IOError as err:
			self.log("I/O error({0}): {1}".format(err.errno, err.strerror))
		except:
			self.log("Unexpected error:" + sys.exc_info()[0])
		finally:
			fh.close()
		return digest

	def timestamp_snapshot(self, file_name):

		"""Puts a datestamp in file_name, just before the extension."""

		now = datetime.datetime.today()
		filepart, extensionpart = os.path.splitext(file_name)
		return "%s (%04d-%02d-%02d-%02d-%02d-%02d)%s" % ( filepart, now.year, now.month, now.day, now.hour, now.minute, now.second, extensionpart )

	def snapshot_dir(self, file_name):

		"""This creates a directory timestamp."""

		now = datetime.datetime.today()
		filepart, extensionpart = os.path.splitext(file_name)
		return "%s-%04d-%02d-%02d-%02d-%02d-%02d%s" % ( filepart, now.year, now.month, now.day, now.hour, now.minute, now.second, extensionpart )

	def timestamp_file(self, file_name):

		"""Puts a datestamp in file_name, just before the extension."""

		now = datetime.datetime.today()
		filepart, extensionpart = os.path.splitext(file_name)
		return "%s (%04d-%02d-%02d-%02d-%02d-%02d)%s" % ( filepart, now.year, now.month, now.day, now.hour, now.minute, now.second, extensionpart )

	def timestamp_dir(self, file_name):

		"""This creates a directory timestamp."""

		now = datetime.datetime.today()
		filepart, extensionpart = os.path.splitext(file_name)
		return "%s-%04d-%02d-%02d-%02d-%02d-%02d%s" % ( filepart, now.year, now.month, now.day, now.hour, now.minute, now.second, extensionpart )


class ListSnapshotsCommand(sublime_plugin.TextCommand):

	"""This handles showing the backups"""

	# class properties
	diff = False
	backups = []

	def run(self, edit):

		"""This is run when the command is issued"""

		# store the list of backup files found
		self.show_backups()

	def show_backups(self):

		"""This uses the show_quick_panel to show a list of backups that match the current file name"""

		# make sure we have a file in the buffer
		if self.view.file_name() == None:
			return

		# init code
		date_file_list = []
		self.backups = []
		backup = Snapshots()

		# get the current file in the buffer
		current_file = os.path.basename( self.view.file_name() )
		backup_root = backup.get_backup_dir_root()
		snapshot_root = backup.get_snapshot_backup_dir()

		# loop through each file in the backup directory
		for dirname, dirnames, filenames in os.walk(backup_root):
			for filename in filenames:
				path = str(os.path.join(dirname, filename))
				if os.path.isfile( path ): # avoid any symlinks and directories
					date_file_tuple = int(os.path.getmtime( path )), path, 'backup'
					date_file_list.append(date_file_tuple)

		# loop through each file in the snapshot directory
		for dirname, dirnames, filenames in os.walk(snapshot_root):
			for filename in filenames:
				path = str(os.path.join(dirname, filename))
				if os.path.isfile( path ): # avoid any symlinks and directories
					date_file_tuple = int(os.path.getmtime( path )), path, 'snapshot'
					date_file_list.append(date_file_tuple)

		# sort the modified / created date
		date_file_list.sort()
		date_file_list.reverse()  # newest mod date now first

		# loop through each tuple's as they are now in order with the newest first and filter out the files we do not need
		for f in date_file_list:

			# if we have reached the number of backup files to display then stop processing
			if len(self.backups) >= backup.display_limit():
				break

			ctime = f[0]; file_path = f[1]; backup_type = f[2]; filename = os.path.basename(file_path)

			# try to match on a non versioned file (i.e. the very first save)
			match = re.search(r'\((\d{4}-\d{1,2}-\d{1,2})-\d{1,2}-\d{1,2}-\d{1,2}\)', filename)
			if match == None and filename == current_file:
				self.backups.append( self.get_formatted_backup_data(file_path, ctime, backup_type))

			# try to match on a versioned file
			match2 = re.search(r'(.+)(\s\((\d{4}-\d{1,2}-\d{1,2})-\d{1,2}-\d{1,2}-\d{1,2}\))', filename)
			if match2:
				name, extension = os.path.splitext(filename)
				if current_file == match2.group(1) + extension:
					self.backups.append( self.get_formatted_backup_data(file_path, ctime, backup_type) )

		# no backups found
		if len(self.backups) == 0:
			sublime.error_message('Sorry, no backups found for this file.')
			return

		# add the data to display in the quick_panel
		filenames = []
		for item in self.backups:
			if item != None:
				filenames.append(
					[
						item['created'],
						'Size: ' + str(item['size']),
						'Filename: ' + item['filename'],
						'Type: ' + item['type']
					]
				)

		# show in the command window
		self.view.window().show_quick_panel(filenames, self.on_click)

	def on_click(self, picked):

		"""Runs when we click a row in the quick panel"""

		# nothing was clicked or the panel was closed by clicking elsewhere or pressing escape
		if picked >= 0 and self.backups[picked]:

			path = self.backups[picked]['path']
			if os.path.isfile(path):

				# see if they want to open the backup file as a preview only: it won't have a tab assigned it (can be closed via the usual close method)
				settings = sublime.load_settings('Snapshots.sublime-settings')
				quick_view = settings.get("quick_view")

				# open the file and make it read_only
				window = sublime.active_window()
				if window:
					if quick_view == None or quick_view == False:
						new_buffer = window.open_file(path)
					else:
						new_buffer = window.open_file(path, sublime.TRANSIENT)

					# make it read_only so they cannot modify it
					new_buffer.set_read_only(True)

			else:
				sublime.error_message('Unable to find backup file')

	def prettySize(self, size):

		"""Returns a nicely formatted filesize from bytes to a more human readable size"""

		# originally created by jakob on http://snippets.dzone.com/posts/show/5434
		suffixes = [("b",2**10), ("k",2**20), ("m",2**30)]
		for suf, lim in suffixes:
			if size > lim:
				continue
			else:
				return round(size/float(lim/2**10),2).__str__()+suf

	def get_pretty_time_format(self, seconds):

		"""Returns a formatted time display from seconds"""

		days = seconds / 86400
		seconds -= 86400*days
		hours = seconds / 3600
		seconds -= 3600*hours
		minutes = seconds / 60
		seconds -= 60*minutes

		if minutes == 0 and hours == 0 and days == 0 and seconds == 3:
			return "%1d sec" % (seconds)
		elif minutes == 0 and hours == 0 and days == 0:
			return "%1d secs" % (seconds)
		elif days == 0 and hours == 0 and minutes == 1 and seconds == 0:
			return "%01d min" % (minutes)
		elif days == 0 and hours == 0:
			return "%01d mins, %01d secs" % (minutes, seconds)
		elif days == 0 and hours == 1:
			return "%01d hr" % (hours)
		elif days == 0 and hours > 1:
			return "%01d hrs" % (hours)
		elif days == 1:
			return "%01d day" % (days)
		else:
			return "%01d days" % (days)

	def get_formatted_backup_data(self, file_path, ctimestamp, backup_type):

		"""Returns a dictionary with the data to show in the quick panel in the display formats"""

		# if the file is invalid then simply return
		if os.path.isfile(file_path) == False:
			return None

		# set the locale here
		locale.setlocale(locale.LC_ALL, '')

		# set the display date format (readable, normal)
		settings = sublime.load_settings('Snapshots.sublime-settings')
		date_format = settings.get("date_format")

		# set the default fallback time display
		display_month = datetime.datetime.fromtimestamp( ctimestamp ).strftime('%d %B')
		display_time = datetime.datetime.fromtimestamp( ctimestamp ).strftime(', %I:%M%p').lower()

		# get the difference between now and when the file was saved
		diff = (int(time.time()) - ctimestamp)
		display_date = display_month +  display_time + ' (' + self.get_pretty_time_format(diff) + ' ago)'

		# populate the current file dictionary
		return {
			'size' : self.prettySize( os.path.getsize( file_path ) ),
			'created' : display_date,
			'filename' : os.path.basename(file_path),
			'path' : file_path,
			'type' : backup_type.capitalize()
		}

class PruneSnapshotsCommand(sublime_plugin.TextCommand):

	"""This creates a snapshot of the current file with a special .snapshot extension"""

	def run(self, edit):

		"""This is run when the command is issued"""
		backup = Snapshots()
		message = backup.prune_backups()
		sublime.status_message(message)


class CreateSnapshotCommand(sublime_plugin.TextCommand):

	"""This creates a snapshot of the current file with a special .snapshot extension"""

	def run(self, edit):

		"""This is run when the command is issued"""

		# make sure we have a file in the buffer
		self.create_snapshot()

	def create_snapshot(self):

		"""This uses the show_quick_panel to show a list of backups that match the current file name"""

		if self.view.file_name() == None:
			return

		"""When a file is saved, and there is no backup of it yet, create a
		backup of the original file before saving the new, modified version."""

		backup = Snapshots()

		# stop processing if we are disabled, not modified, 0 in size or in the settings exclusions
		if backup.is_enabled() == False or self.view.size() == 0:
			return

		# check to see if we have the backup directory '2011-07-23'
		buffer_file_name = self.view.file_name()
		backup_dir = backup.get_snapshot_backup_dir()

		# check to see if the file should be excluded form the backup
		if backup.is_excluded( buffer_file_name ):
			backup.exclude = True
			return
		else:
			backup.exclude = False

		# create the backup filename
		file_name = backup.timestamp_snapshot( os.path.basename(buffer_file_name) )
		backup_name = os.path.join(backup_dir, file_name)

		if backup_name != None:
			try:
				shutil.copy(buffer_file_name, backup_name)

			except IOError as err:
				backup.log("I/O error({0}): {1}".format(err.errno, err.strerror))
			except:
				backup.log("Unexpected error:" + sys.exc_info()[0])
