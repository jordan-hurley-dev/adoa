import adoa
import sec
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

connection = Connection(base_url="ado url", creds=BasicAuthentication(sec.username, sec.password))

for repository_name in ["repo name", "repo name"]:
    rc  = adoa.RepoClient("ado project name", connection, repository_name, "base branch", "working branch", "change title")
    
    # Make changes
    content = rc.get_content("./file.example").replace("example1", "example2")
    rc.edit("./file.example", content)
    rc.add("/example.txt", "example content")

    # Push changes and create merges
    rc.push_to_working()
    # rc.pull_into("test")
    # rc.pull_into("preprod")
    # rc.pull_into("prod")