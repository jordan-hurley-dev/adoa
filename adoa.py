from types import SimpleNamespace
import base64
import urllib.parse

class RepoClient:
    project: str
    git_client: object
    repository: object
    base_branch: str
    working_branch: str
    change_title: str
    is_first_push: bool
    pending_changes = []

    def __init__(self, project: str, connection: object, repository_name: object, base_branch: str, working_branch: str, change_title: str):
        self.project        = project
        self.git_client     = connection.clients.get_git_client()
        self.repository     = self.git_client.get_repository(repository_name, self.project)
        self.base_branch    = base_branch
        self.working_branch = working_branch
        self.change_title   = change_title
        if self.base_branch != self.working_branch:
            self.is_first_push = True
        else:
            self.is_first_push = False

    # Get content of an item as string. 
    # Note: content will keep its newline format, for CRLF the string will end lines with "/r/n"
    def get_content(self, item_path: str):
        if self.is_first_push:
            source_branch = urllib.parse.quote_plus(self.base_branch)
        else:
            source_branch = urllib.parse.quote_plus(self.working_branch)

        version_descriptor = SimpleNamespace(version=source_branch, version_options=None, version_type=None)
        get_item_response = self.git_client.get_item_text(self.repository.id, path=item_path, project=self.project, version_descriptor=version_descriptor)
        file_content = ""
        for part in get_item_response:
            file_content += part.decode("utf-8")
        return file_content

    # Add an add file change to the pending changes
    def add(self, new_file_path: str, new_file_content: str):
        self.pending_changes.append(SimpleNamespace(type="add", path=new_file_path, content=new_file_content))

    # Add an edit file change to the pending changes
    def edit(self, file_path: str, changed_content: str):
        self.pending_changes.append(SimpleNamespace(type="edit", path=file_path, content=changed_content))

    # Add an delete file change to the pending changes
    def delete(self, file_path:str):
        self.pending_changes.append(SimpleNamespace(type="delete", path=file_path))

     # Clear pending changes
    def clear(self):
        self.pending_changes.clear()
    
    # Push changes to the working branch
    def build_push(self):
        if self.is_first_push:
            source_branch = self.base_branch
        else:
            source_branch = self.working_branch
        
        old_branch_id = self.git_client.get_refs(self.repository.id, project=self.project, filter=f"heads/{source_branch}")[0].object_id
        formatted_changes = []
        for change in self.pending_changes:
            if change.type == "delete":
                formatted_changes.append(
                    {
                        "changeType": "delete",
                        "item": {
                            "path": change.path
                        }
                    }
                )
            else:
                formatted_changes.append(
                    {
                        "changeType": change.type,
                        "item": {
                            "path": change.path
                        },
                        "newContent": {
                            "content": base64.b64encode(change.content.encode("ascii")).decode("ascii"),
                            "contentType": "base64Encoded"
                        }
                    }
                )

        return {
            "refUpdates": [
                {
                    "name": "refs/heads/" + self.working_branch,
                    "oldObjectId": old_branch_id
                }
            ],
            "commits": [
                {
                    "comment": self.change_title,
                    "changes": formatted_changes
                }
            ]
        }

    # Push changes to working branch
    def push_to_working(self):
        self.git_client.create_push(self.build_push(), self.repository.id, self.project)
        self.is_first_push = False
        self.clear()

    # Pull into given branch
    def pull_into(self, branch_name: str):
        if self.pending_changes != []:
            print("\nERROR: all pending changes must be pushed to the working branch before merging into another branch\n")
            exit()

        pull_request = {
            "title": self.change_title, 
            "sourceRefName": "refs/heads/" + self.working_branch, 
            "targetRefName": "refs/heads/" + branch_name
        }
        self.git_client.create_pull_request(pull_request, repository_id=self.repository.id)