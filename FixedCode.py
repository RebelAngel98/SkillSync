import requests
import pandas as pd
import time

# Replace 'XxXxX' with your actual client ID and client secret
# To get access to a free Client_ID visit the following:
# https://lightcast.io/products/data/API-form
CLIENT_ID = '<<dnaqre9zy5c62yuo>>'
CLIENT_SECRET = '<<>RpU0lriy>'
SCOPE = 'emsi_open'

def get_oauth_token(client_id, client_secret, scope):
    url = "https://auth.emsicloud.com/connect/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': scope
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to obtain OAuth token: {response.text}")
        
def get_latest_skill_version(token):
    url = "https://emsiservices.com/skills/versions/latest"
    headers = {'authorization': f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
       return response.json()['data']
    else:
        raise Exception(f"Failed to get latest skill version: {response.text}")
        
def get_all_skills(token, fields):
    url = f"https://emsiservices.com/skills/versions/latest/skills?fields={fields}"
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    skills = response.json()['data']

    return {'data': skills}
		
# Get the OAuth token
token = get_oauth_token(CLIENT_ID, CLIENT_SECRET, SCOPE)
print("OAuth Token:", token)

# Get latest skill version metadata
latest_version_metadata = get_latest_skill_version(token)
print("Latest Skill Version Metadata:", latest_version_metadata)

# Extract available fields
available_fields = ','.join(latest_version_metadata['fields'])
print("Available Fields:", available_fields)

# Get all skills with all available fields from the latest version
skills_data = get_all_skills(token, fields=available_fields)
#print("Skills Data:", skills_data)

skills_df = pd.DataFrame(skills_data['data'])

# Flatten 'category' field into 'category_id' and 'category_name'
if 'category' in skills_df.columns and isinstance(skills_df['category'].iloc[0], dict):
    skills_df['category_id'] = skills_df['category'].apply(lambda x: x['id'] if isinstance(x, dict) else None)
    skills_df['category_name'] = skills_df['category'].apply(lambda x: x['name'] if isinstance(x, dict) else None)
    skills_df = skills_df.drop(columns=['category'])
    
# Flatten 'subcategory' field into 'subcategory_id' and 'subcategory_name'
if 'subcategory' in skills_df.columns and isinstance(skills_df['subcategory'].iloc[0], dict):
    skills_df['subcategory_id'] = skills_df['subcategory'].apply(lambda x: x['id'] if isinstance(x, dict) else None)
    skills_df['subcategory_name'] = skills_df['subcategory'].apply(lambda x: x['name'] if isinstance(x, dict) else None)
    skills_df = skills_df.drop(columns=['subcategory'])
    
# Extract and flatten 'related_title'
if 'related_title' in skills_df.columns and isinstance(skills_df['related_title'].iloc[0], list):
    related_title_df = skills_df['related_title'].apply(pd.Series)
    related_title_df.columns = [f'related_title{i}' for i in range(len(related_title_df.columns))]
    skills_df = pd.concat([skills_df, related_title_df], axis=1).drop(columns=['related_title'])
    
# Extract and flatten 'tags'
if 'tags' in skills_df.columns and isinstance(skills_df['tags'].iloc[0], list):
    tags_df = skills_df['tags'].apply(pd.Series)
    tags_df.columns = [f'tag_{i}' for i in range(len(tags_df.columns))]
    skills_df = pd.concat([skills_df, tags_df], axis=1).drop(columns=['tags'])
    
# Flatten 'type' field into 'type_id' and 'type_name'
if 'type' in skills_df.columns and isinstance(skills_df['type'].iloc[0], dict):
    skills_df['type_id'] = skills_df['type'].apply(lambda x: x['id'] if isinstance(x, dict) else None)
    skills_df['type_name'] = skills_df['type'].apply(lambda x: x['name'] if isinstance(x, dict) else None)
    skills_df = skills_df.drop(columns=['type'])
    
print("\nDataFrame Info:")
print(skills_df.info())
skills_df.to_csv('all_skills_latest.csv', index=False)