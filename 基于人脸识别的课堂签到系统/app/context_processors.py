
import os
def global_defaults(request):
    project_name = os.path.split(os.getcwd())[1]
    return {'project_name': project_name}