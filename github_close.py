import sublime, sublime_plugin
import urllib2
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "requests"))
import requests


class Repo():
	def __init__(self):
		self.url = None
		self.repo = None
		self.user = None
		self.collaborators = []
		self.issues = {}

	def getRepoInfoFromSettings(self, settingsName='Github Issues.sublime-settings'):
		settings = sublime.load_settings(settingsName)
		self.url = settings.get('github_url')
		self.user = settings.get('github_username')
		self.repo = settings.get('github_repo')

	def getCollaborators(self):

		if self.url and self.user and self.repo:
			r = requests.get(self.url + '/repos/' + self.user + '/' + self.repo + '/collaborators')

			if r.status_code == requests.codes.ok:
				data = r.json()

				for item in data:
					collaborator = {}
					collaborator['id'] = item['id']
					collaborator['login'] = item['login']
					collaborator['url'] = item['url']

					r2 = requests.get(collaborator['url'])
					
					if r2.status_code == requests.codes.ok:
						nameData = r2.json()
						if 'name' in nameData:
							collaborator['name'] = nameData['name']
						else:
							collaborator['name'] = 'no name provided'

					self.collaborators.append(collaborator)

			else:
				print 'could not get collaborators'

	def getIssues(self):
		
		if self.url and self.user and self.repo:
			r = requests.get(self.url + '/repos/' + self.user + '/' + self.repo + '/issues?state=open')

			if r.status_code == requests.codes.ok:
				data = r.json()

				for issue in data:
					if issue['assignee']:
						id = issue['assignee']['id']
						if id not in self.issues:
							self.issues[id] = []
						self.issues[id].append(issue)
					else:
						id = 'none'
						if id not in self.issues:
							self.issues[id] = []
						self.issues[id].append(issue)

			else:
				print 'could not get issues'

	def closeIssue(self, issue, password):

		# close the issue
		r = requests.patch(self.url + '/repos/' + self.user + '/' + self.repo + '/issues/' + str(issue.number), auth=(self.user, password), data='{"state":"closed"}')
		if r.status_code == requests.codes.ok:
			print "ok, closed the issue"
		else:
			print "failed to close the issue"

		# add the comment
		if issue.comment:
			r = requests.post(self.url + '/repos/' + self.user + '/' + self.repo + '/issues/' + str(issue.number) + '/comments', auth=(self.user, password), data='{"body":"' + issue.comment + '"}')
			if r.status_code == requests.codes.ok or r.status_code == 201:
				print "ok, added the comment"
			else:
				print "failed to add the comment"

class Issue():
	def __init__(self):
		self.collaborator = None
		self.number = None
		self.title = None
		self.body = None
		self.assignee = None
		self.comment = None

	def clear(self):
		self.collaborator = None
		self.number = None
		self.title = None
		self.body = None
		self.assignee = None
		self.comment = None

class GithubCloseIssueCommand(sublime_plugin.WindowCommand):

	def __init__(self, window):
		self.window = window

		# the repo stuff
		self.repo = Repo()
		self.repo.getRepoInfoFromSettings()
		self.repo.getCollaborators()
		self.repo.getIssues()

		# the issue stuff
		self.issue = Issue()

	def run(self):

		collaboratorList = []

		for collaborator in self.repo.collaborators:
			collaboratorList.append([collaborator['login'], collaborator['name']])

		collaboratorList.append(['unassigned', 'close an issue that is currently unassigned'])

		# and finally display the issues
		self.window.show_quick_panel(collaboratorList, self.select_collaborator)

	def select_collaborator(self, index):

		issueList = []
		
		if index == len(self.repo.collaborators):
			self.issue.collaborator = self.repo.collaborators['none']
			collaborator = 'none'
		else:
			self.issue.collaborator = self.repo.collaborators[index]
			collaborator = self.repo.collaborators[index]['id']

		for item in self.repo.issues[collaborator]:
			issue = []
			issue.append(item['title'])

			if item['body']:
				issue.append(item['body'])
			else:
				issue.append('no description given')

			if item['assignee']:
				name = self.repo.collaborators[index]['name']
				issue.append(item['assignee']['login'] + ' - ' + name)
			else:
				issue.append('unassigned')

			issueList.append(issue)

		# and finally display the issues
		self.window.show_quick_panel(issueList, self.get_comment)

	def get_comment(self, index):
		self.issue.number = self.repo.issues[self.issue.collaborator['id']][index]['number']
		self.window.show_input_panel('comment', '', self.get_password, None, None)

	def get_password(self, comment):
		if self.issue.comment != "":
			self.issue.comment = comment
		self.window.show_input_panel('password', '', self.close_issue, None, None)

	def close_issue(self, password):
		self.repo.closeIssue(self.issue, password)
		self.issue.clear()
