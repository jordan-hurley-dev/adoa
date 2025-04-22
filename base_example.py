import adoa
import sec
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

connection = Connection(base_url="https://dev.azure.com/example-organization", creds=BasicAuthentication(sec.username, sec.password))

for repository_name in ["repo-name1", "repo-name2"]:
    rc  = adoa.RepoClient("example-project", connection, repository_name, "base-branch", "working-branch", "change title")
    
    # Make changes
    content = rc.get_content("./example1.txt").replace("example1", "example2")
    rc.edit("./example1.txt", content)
    rc.create("/example2.txt", "example content")
    rc.delete("example3.txt")

    # Push changes and create merges
    rc.push_to_working()
    # rc.pull_into("test")
    # rc.pull_into("preprod")
    # rc.pull_into("prod")