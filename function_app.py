import azure.functions as func
import logging
import requests
from requests.auth import HTTPBasicAuth
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="adoautomate")
def adoautomate(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Ado automation function triggered.')

    try:
        payload = req.get_json()
        result = handle_user_story_creation(payload)

        if "successfully" in result:
            return func.HttpResponse(result)
        else:
            return func.HttpResponse(result, status_code=500)

    except ValueError as e:
        logging.error(f"Invalid JSON payload: {e}")
        return func.HttpResponse("Invalid JSON payload", status_code=400)
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse(f"Error processing request: {str(e)}", status_code=500)
    


def handle_user_story_creation(payload):
    # Handle Azure DevOps User Story creation webhook and create 5 child tasks with idempotency

    try:
    # Extract User Story details from payload

        resource = payload.get('resource', {})
        fields = resource.get('fields', {})
        user_story_id = resource.get('id')
        user_story_title = fields.get('System.Title', 'Unknown User Story')
        area_path = fields.get('System.AreaPath', '')
        iteration_path = fields.get('System.IterationPath', '')

        required_task_titles = [
            "Requirements & Grooming",
            "Design & Approach", 
            "Implementation",
            "Test & Validation",
            "Documentation & Handover"
        ]
        
        # Get missing tasks by comparing existing children with required tasks
        missing_tasks, existing_tasks = get_missing_tasks(user_story_id, required_task_titles)
        
        created_tasks = []
        
        # Only create tasks that are missing
        for task_title in missing_tasks:
            logging.info(f"Creating missing task '{task_title}' for User Story {user_story_id}")
            task_result = create_child_task(user_story_id, task_title, user_story_title, area_path, iteration_path)
            if "successfully" in task_result:
                created_tasks.append(task_title)
                logging.info(f"Successfully created task '{task_title}' for User Story {user_story_id}")
            else:
                logging.error(f"Failed to create task '{task_title}': {task_result}")
        
        # Prepare result message based on what happened
        total_tasks = len(required_task_titles)
        created_count = len(created_tasks)
        existing_count = len(existing_tasks)
        
        if existing_count == total_tasks:
            return f"All {total_tasks} child tasks already exist for User Story '{user_story_title}' (ID: {user_story_id}). No new tasks created."
        elif created_count == total_tasks:
            return f"All {total_tasks} child tasks created successfully for User Story '{user_story_title}' (ID: {user_story_id})"
        else:
            return f"User Story '{user_story_title}' (ID: {user_story_id}): Created {created_count} new tasks, {existing_count} tasks already existed."
            
    except Exception as e:
        logging.error(f"Error handling User Story creation: {e}")
        return f"Error handling User Story creation: {str(e)}"

def get_missing_tasks(parent_id, required_task_titles):
    # Get ALL child tasks in one API call
    org = "KRISHNANANDYADAV-ORG2024"
    proj = "Ado_Automation"
    pat = "xxyyzz"
    
    # Get work item details including relations
    url = f"https://dev.azure.com/{org}/{proj}/_apis/wit/workitems/{parent_id}?$expand=relations&api-version=7.0"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, auth=HTTPBasicAuth('', pat))
        
        if response.status_code == 200:
            work_item = response.json()
            relations = work_item.get('relations', [])
            
            # Get all child task IDs
            child_task_ids = []
            for relation in relations:
                if relation.get('rel') == 'System.LinkTypes.Hierarchy-Forward':
                    # Extract work item ID from URL
                    url_parts = relation['url'].split('/')
                    child_id = url_parts[-1]
                    child_task_ids.append(child_id)
            
            existing_task_titles = []
            
            if child_task_ids:
                # Get details of all child tasks to check titles
                child_ids_str = ','.join(child_task_ids)
                child_url = f"https://dev.azure.com/{org}/{proj}/_apis/wit/workitems?ids={child_ids_str}&fields=System.Title&api-version=7.0"
                
                child_response = requests.get(child_url, headers=headers, auth=HTTPBasicAuth('', pat))
                
                if child_response.status_code == 200:
                    child_items = child_response.json().get('value', [])
                    
                    # Get all existing task titles that match our required tasks
                    for child_item in child_items:
                        child_title = child_item.get('fields', {}).get('System.Title', '')
                        if child_title in required_task_titles:
                            existing_task_titles.append(child_title)
                else:
                    logging.warning(f"Failed to get child task details: {child_response.status_code}")
            
            # Calculate missing tasks
            missing_tasks = [task for task in required_task_titles if task not in existing_task_titles]

            return missing_tasks, existing_task_titles
                
        else:
            logging.warning(f"Failed to get work item details: {response.status_code}, {response.text}")
            return required_task_titles, []  # Assume all tasks are missing if we can't check
            
    except Exception as e:
        logging.error(f"Error checking task existence: {str(e)}")
        return required_task_titles, []  # Assume all tasks are missing if error occurs

def create_child_task(parent_id, task_title, parent_title, area_path, iteration_path):

    org = "KRISHNANANDYADAV-ORG2024"
    proj = "Ado_Automation"
    pat = "xxyyzz"
    

    url = f"https://dev.azure.com/{org}/{proj}/_apis/wit/workitems/$Task?api-version=7.0"
    
    headers = {'Content-Type': 'application/json-patch+json'}

    data = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": task_title
        },
        {
            "op": "add", 
            "path": "/fields/System.Description",
            "value": f"Task for User Story: {parent_title}"
        },
        {
            "op": "add", 
            "path": "/fields/System.AreaPath",
            "value": area_path
        },
        {
            "op": "add", 
            "path": "/fields/System.IterationPath",
            "value": iteration_path
        },
        {
            "op": "add",
            "path": "/fields/System.AssignedTo",
            "value": "krishnanand.yadav@outlook.com"
        },
        {
            "op": "add",
            "path": "/fields/System.State", 
            "value": "New"
        },
        {
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.Priority",
            "value": 2
        },
        {
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/{org}/{proj}/_apis/wit/workitems/{parent_id}"
            }
        }
    ]


    try:
        response = requests.post(url, headers=headers, auth=HTTPBasicAuth('', pat), data=json.dumps(data))
        
        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get('id')
            logging.info(f"Task '{task_title}' created successfully with ID: {task_id}")
            return f"Task '{task_title}' created successfully"
        else:
            error_msg = f"Failed to create task '{task_title}': {response.status_code}, {response.text}"
            logging.error(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Error creating task '{task_title}': {str(e)}"
        logging.error(error_msg)
        return error_msg



