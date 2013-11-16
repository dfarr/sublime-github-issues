import sublime, sublime_plugin

class GithubConnectCommand(sublime_plugin.WindowCommand):

	def run(self):
		self.window.open_file(sublime.packages_path() + '/Github Issues/Github Issues.sublime-settings')
		pass
