# Azure DevOps Automation - User Story Task Creator

##  **Objective**
When a new User Story is created in Azure DevOps, automatically create five Tasks and link them as child work items under that story.

## **Requirements**
Create exactly **5 child Tasks** with the following titles:
1. **Requirements & Grooming**
2. **Design & Approach** 
3. **Implementation**
4. **Test & Validation**
5. **Documentation & Handover**

###  **Key Features**
-  Each Task is properly linked as a **child** of the User Story
-  Tasks inherit relevant metadata such as **Area Path** and **Iteration Path**
-  The process is **idempotent** — no duplicate Tasks if retried or triggered multiple times
-  All corner/edge cases in architecture and coding are handled properly

---

##  **Setup & Configuration**

### 1. **Azure DevOps Service Hook Configuration**

#### Navigate to Project Settings
1. Go to your Azure DevOps project: `KRISHNANANDYADAV-ORG2024/Ado_Automation`
2. Click on **"Project Settings"** (gear icon)
3. Select **"Service hooks"** under "General" section

#### Create New Service Hook
1. Click **"+ Create subscription"**
2. Select **"Web Hooks"** as the service

#### Configure the Trigger
- **Service**: Web Hooks
- **Event**: Work item created
- **Filters**:
  - **Work item type**: User Story
  - **Area path**: (leave blank or specify if needed)
  - **State**: (leave blank to trigger on any state)

#### Configure the Action
- **URL**: `https://adoautomationfuncapp.azurewebsites.net/api/adoautomate?code=xxxxxxxxxxxxxxxxxxxxxx`
- **HTTP headers**: `Content-Type: application/json`
- **Resource details to send**: All
- **Messages to send**: All
- **Detailed messages to send**: All

### 2. **Azure Function Configuration**

Update these variables in `function_app.py`:
```python
org = "KRISHNANANDYADAV-ORG2024"
proj = "Ado_Automation" 
pat = "xxx"  # Update with your PAT
assignee = "krishnanand.yadav@outlook.com"  # Update with your email
```

### 3. **Required Permissions**
Your Personal Access Token (PAT) needs:
-  **Work Items**: Read & Write
-  **Work Items**: Full Access (to create links/relations)

---

##  **How It Works**

### **Function Flow**
```
User Story Created → Service Hook Triggered → Azure Function Receives Webhook
                                                        ↓
                                           Extract User Story Details
                                           (ID, Title, Area Path, Iteration Path)
                                                        ↓
                                        Check Existing Child Tasks (Idempotency)
                                                        ↓
                                    Get Missing Tasks → Create Only Missing Tasks
                                                        ↓
                                           Link Tasks as Children → Return Result
```

### **Idempotency Implementation**
The function implements **smart idempotency**:
1. **Single API Call**: Gets all existing child tasks in one request
2. **Local Comparison**: Compares existing task titles with required tasks
3. **Selective Creation**: Only creates tasks that don't already exist
4. **Performance Optimized**: Minimal API calls for maximum efficiency

### **Task Properties**
Each created task includes:
```json
{
  "System.Title": "[One of 5 predefined titles]",
  "System.Description": "Task for User Story: [Parent Story Title]",
  "System.AreaPath": "[Inherited from User Story]",
  "System.IterationPath": "[Inherited from User Story]", 
  "System.AssignedTo": "krishnanand.yadav@outlook.com",
  "System.State": "New",
  "Microsoft.VSTS.Common.Priority": 2,
  "Relations": "[Child link to parent User Story]"
}
```

---

### **Sample Test Payload**
```json
{
  "resource": {
    "id": 123,
    "fields": {
      "System.Title": "Sample User Story",
      "System.AreaPath": "Ado_Automation\\Development",
      "System.IterationPath": "Ado_Automation\\Sprint 1"
    }
  }
}
```

---

## 🔍 **How Idempotency is Achieved**

### **Problem Solved**
Azure DevOps service hooks might trigger multiple times due to:
- Network retries
- Manual re-triggering
- Service maintenance
- Configuration changes

### **Our Solution**
```python
# 1. Get existing child tasks in one API call
missing_tasks, existing_tasks = get_missing_tasks(user_story_id, required_tasks)

# 2. Only create missing tasks
for task_title in missing_tasks:
    create_child_task(...)

# 3. Smart result messages
if existing_count == total_tasks:
    return "All tasks already exist - no duplicates created"
elif created_count == total_tasks:
    return "All tasks created successfully"  
else:
    return f"Created {created_count} new, {existing_count} already existed"
```

### **Benefits**
 **No Duplicates**: Never creates duplicate tasks  
 **Performance**: Only 1-2 API calls regardless of existing tasks  
 **Reliability**: Handles partial failures gracefully  
 **Transparency**: Clear logging of what happened  

---

##  **Troubleshooting**

### **Common Issues**
1. **Function not triggering**:
   - Check service hook URL and function key
   - Verify service hook is Active in Azure DevOps
   - Check Azure Function logs

2. **Tasks not being created**:
   - Verify PAT permissions (Work Items: Full Access)
   - Check organization and project names in code
   - Ensure PAT is not expired

3. **Duplicate tasks**:
   -  This should not happen with our idempotency implementation
   -  Check logs to see what tasks were found vs created

### **Monitoring & Logs**
Check Azure Function logs for detailed information:




---

## **Project Structure**
```
Ado_automation/
├── function_app.py              # Main Azure Function
├── requirements.txt             # Python dependencies
├── host.json                    # Function host configuration
├── local.settings.json          # Local development settings
└── README.md                    # This documentation
```

---

##  **Success Indicators**
When working correctly, you should see:
-  **User Story created** → 5 child tasks appear automatically
-  **Duplicate webhook** → "All tasks already exist" message
-  **Partial existing tasks** → Only missing tasks are created
-  **Proper hierarchy** → Tasks show as children in Azure DevOps
-  **Inherited properties** → Tasks have same Area Path and Iteration Path as parent

 
