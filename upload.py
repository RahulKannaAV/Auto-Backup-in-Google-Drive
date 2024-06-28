import google.auth
import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

def read_backup_files_info():
  info_file = open('files_info.json') # JSON file which has details of files that needs to be backed up

  backup_files = json.load(info_file)

  # Create a folder
  return backup_files

def search_file():
  """Search file in drive location

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  creds = auth()
  files_info = read_backup_files_info()
  #print(creds, files_info)
  try:
    # create drive api client
    service = build("drive", "v3", credentials=creds)
    files = []
    page_token = None
    for folder in files_info:
      print(folder)
      folderName = folder["folder_name"]
      print(folderName)
      while True:
      # Checks for that file
        response = (
          service.files()
          .list(
              q=f'mimeType="application/vnd.google-apps.folder" and name="{folderName}"',
              spaces="drive",
              fields="nextPageToken, files(id, name)",
              pageToken=page_token,
          )
          .execute()
      )

        is_there = len(response.get("files")) == 1

        if is_there:
          # Call upload function
          folder_id = response.get("files")[0].get("id")

        else:
        # Call new folder creation function
        # Use that folder id to call upload function
          folder_id = create_folder(folder['folder_name'])

        # Uploading the file in the folder
        for file in folder["file_names"]:
          file_name = file["name"]
          file_mime = file["mime"]
          file_path = file["path"]
          upload_basic(file_name, file_mime, file_path , folder_id)
        break


  except HttpError as error:
    print(f"An error occurred: {error}")
    files = None

  return files

def create_folder(folder_name):
  """Create a folder and prints the folder ID
  Returns : Folder Id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  creds = auth()

  try:
    # create drive api client
    service = build("drive", "v3", credentials=creds)
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }

    # pylint: disable=maybe-no-member
    file = service.files().create(body=file_metadata, fields="id").execute()
    return file.get("id")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None
def auth():
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):  # Get it by following Google Drive API Docs
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  return creds



def upload_basic(file_name, file_mime, file_path, folder_id):
  """Insert new file.
  Returns : Id's of the file uploaded

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  #creds, _ = google.auth.default()
  creds = auth()


  try:
    # create drive api client
    service = build("drive", "v3", credentials=creds)
    page_token = None
    while True:
      # Checks for that file
      response = (
        service.files()
        .list(
          q=f'mimeType="{file_mime}" and name="{file_name}" and parents in "{folder_id}"',
          spaces="drive",
          fields="nextPageToken, files(id, name)",
          pageToken=page_token,
        )
        .execute()
      )
      print(response.get("files"))
      is_there = len(response.get("files")) == 1

      # If the file exists previously
      if is_there:
        file_metadata = {"name": file_name, "parents": [folder_id]}
        media = MediaFileUpload(file_path, mimetype=file_mime)
    # pylint: disable=maybe-no-member
        file = service.files().update(fileId=response.get("files")[0]['id'], media_body=media).execute()
        print(f'Updated File ID: {file.get("id")}')

      # Otherwise, create it
      else:
        file_metadata = {"name": file_name, "parents": [folder_id]}
        media = MediaFileUpload(file_path, mimetype=file_mime)
        # pylint: disable=maybe-no-member
        file = (
          service.files()
          .create(body=file_metadata, media_body=media, fields="id")
          .execute()
        )
        print(f'File ID: {file.get("id")}')
      break

  except HttpError as error:
    print(f"An error occurred: {error}")
    file = None

  return file.get("id")


if __name__ == "__main__":
  search_file()