import requests
import pandas as pd
import time

# Replace 'XxXxX' with your actual client ID and client secret
# To get access to a free Client_ID visit the following:
# https://lightcast.io/products/data/API-form
CLIENT_ID = 're6n7eioh3vryqnu'
CLIENT_SECRET = 'B2vbOOwN'
SCOPE = 'emsi_open'

# For more information on the skills database please visit the following API page:
# https://docs.lightcast.dev/apis/skills#meta

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
        return response.json()
    else:
        raise Exception(f"Failed to obtain OAuth token: {response.text}")

def get_latest_skill_version(token):
    url = "https://emsiservices.com/skills/versions/latest"
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
       return response.json().get('access_token')
    else:
        raise Exception(f"Failed to get latest skill version: {response.text}")

def get_all_skills(token, version="latest", fields=None, page_size=100, max_pages=None):
    url = f"https://emsiservices.com/skills/versions/{version}/skills"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'fields': fields, 'limit': page_size}
    
    all_skills = []
    page = 0
    request_count = 0

    while True:
        page += 1
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception("Failed to get skills: " + response.text)

        skills_batch = response.json().get("data", [])
        if not skills_batch:
            break

        all_skills.extend(skills_batch)

        request_count += 1
        if request_count % 5 == 0:
            time.sleep(60)  # made this a minute

        # Optional: break after a certain number of pages for testing
        if max_pages and page >= max_pages:
            break

    return {'data': all_skills}

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
print("Skills Data:", skills_data)

# Convert skills data to DataFrame
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

# Extract and flatten 'tags'
if 'tags' in skills_df.columns and isinstance(skills_df['tags'].iloc[0], list):
    tags_df = skills_df['tags'].apply(pd.Series)
    tags_df.columns = [f'tag_{i}' for i in range(len(tags_df.columns))]
    skills_df = pd.concat([skills_df, tags_df], axis=1).drop(columns=['tags'])

# Flatten nested dictionaries in tags columns
for col in skills_df.filter(like='tag_').columns:
    if isinstance(skills_df[col].dropna().iloc[0], dict):
        skills_df[f'{col}_key'] = skills_df[col].apply(lambda x: x['key'] if isinstance(x, dict) else None)
        skills_df[f'{col}_value'] = skills_df[col].apply(lambda x: x['value'] if isinstance(x, dict) else None)
        skills_df = skills_df.drop(columns=[col])

# Flatten 'type' field into 'type_id' and 'type_name'
if 'type' in skills_df.columns and isinstance(skills_df['type'].iloc[0], dict):
    skills_df['type_id'] = skills_df['type'].apply(lambda x: x['id'] if isinstance(x, dict) else None)
    skills_df['type_name'] = skills_df['type'].apply(lambda x: x['name'] if isinstance(x, dict) else None)
    skills_df = skills_df.drop(columns=['type'])

# Reorder columns
skills_df = skills_df[[
    'id', 'name', 'description', 'descriptionSource', 'infoUrl',
    'category_id', 'category_name', 'subcategory_id', 'subcategory_name',
    'isLanguage', 'isSoftware', 'tag_0_key', 'tag_0_value', 'tag_1_key', 'tag_1_value',
    'type_id', 'type_name'
]]

# Display the DataFrame
print(skills_df)

# Basic EDA
print("\nDataFrame Info:")
print(skills_df.info())

# Uncomment Below to 
# print("\nTop 5 Rows of the DataFrame:")
# print(skills_df.head())

# Uncomment Below to Display all rows of the DataFrame
# print("\nFull DataFrame:")
# pd.set_option('display.max_rows', 5)
# print(skills_df)

# Save to CSV if needed
skills_df.to_csv('all_skills_latest.csv', index=False)