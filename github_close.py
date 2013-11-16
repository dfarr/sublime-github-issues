import sublime, sublime_plugin
import urllib2
import json

class GithubCloseIssueCommand(sublime_plugin.WindowCommand):

	collaborators = []
	collaboratorData = None

	issues = []
	issueData = None

	def run(self):

		sublime.message_dialog(sublime.packages_path())

		# just read the list if it already exists
		if len(self.collaborators) > 0:
			self.window.show_quick_panel(self.collaborators, self.select_collaborator)
			return
		
		# first read the settings
		settings = sublime.load_settings('Github Issues.sublime-settings')
		url = settings.get('github_url')
		username = settings.get('github_username')
		repo = settings.get('github_repo')

		# call githhub to get the collaborators
		req = urllib2.Request(url + '/api/v3/repos/' + username + '/' + repo + '/collaborators')
		response = urllib2.urlopen(req)
		self.collaboratorData = json.loads(response.read())

		# now parse the data
		for collaborator in self.collaboratorData:
			item = []
			item.append(collaborator['login'])

			# get the name of the assignee
			req = urllib2.Request(collaborator['url'])
			response = urllib2.urlopen(req)
			name = json.loads(response.read())

			if 'name' in name:
				item.append(name['name'])
			else:
				item.append('no name provided')

			self.collaborators.append(item)

		self.collaborators.append(['unassigned', 'close an issue that is currently unassigned'])

		# and finally display the issues
		self.window.show_quick_panel(self.collaborators, self.select_collaborator)


	def select_collaborator(self, index):

		# clear the current issues
		self.issues[:] = []

		# first read the settings
		settings = sublime.load_settings('Github Issues.sublime-settings')
		url = settings.get('github_url')
		username = settings.get('github_username')
		repo = settings.get('github_repo')

		# get the collaborator
		if index == len(self.collaborators)-1:
			assignee = 'none'
		elif index >= 0:
			assignee = self.collaborators[index][0]

		# now call github to get the open issues
		req = urllib2.Request(url + '/api/v3/repos/' + username + '/' + repo + '/issues?state=open&assignee=' + assignee)
		response = urllib2.urlopen(req)
		self.issueData = json.loads(response.read())

		# now parse the issues
		for item in self.issueData:
			issue = []
			issue.append(item['title'])

			if item['body']:
				issue.append(item['body'])
			else:
				issue.append('no description given')

			if item['assignee']:
				issue.append(item['assignee']['login'])
			else:
				issue.append('unassigned')

			self.issues.append(issue)

		if len(self.issues) == 0:
			sublime.message_dialog("No issues assigned to " + assignee)
			return

		# and finally display the issues
		self.window.show_quick_panel(self.issues, self.close_issue)

	def close_issue(self, index):
		sublime.message_dialog(str(self.issueData[index]['number']))

		# now excute the equivalent of this curl:
		# curl -X PATCH --data '{"title":"get rid of additional tag in tiles", "state":"closed"}' -u i834997:password https://github.wdf.sap.corp/api/v3/repos/i834997/Constellations/issues/21 
