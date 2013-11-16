import sublime, sublime_plugin
from github import *

class GithubNewIssueCommand(sublime_plugin.WindowCommand):
	def run(self, edit):
		self.view.insert(edit, 0, "Hello, World!")
