import pyrebase
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import tempfile
import secrets

class FirebaseHandler:
    def __init__(self):
        load_dotenv()

        # Firebase configuration from environment variables
        firebaseConfig = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "databaseURL": os.environ.get("FIREBASE_DATABASE_URL"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID")
        }
        # Initialize Firebase
        self.firebase = pyrebase.initialize_app(firebaseConfig)
        self.db = self.firebase.database()
        self.storage = self.firebase.storage()

        # Initialize the jobs table
        self.jobs_ref = self.db.child("Drangeue_jobs")

    def add_job(self,area, thumbnail, userid, jobid, startTime,  jobTitle, jobDescription, isdone=False,):
        job_data = {
            "userID": userid,
            "title": jobTitle,
            "description": jobDescription,
            "job_id": jobid,
            "startTime": startTime,
            "isdone": isdone,
            "thumbnail": thumbnail,
            "area": area
        }
        self.jobs_ref.child(jobid).set(job_data)

    def update_job(self, thumbnail, area, basemap, userid, jobid, jobTitle, jobDescription,  startTime=None, endTime=None, isdone=None, features=None):
        update_data = {}
        folder_name = f"job_{jobid}"

        update_data["startTime"] = startTime
        update_data["endTime"] = endTime
        update_data["isdone"] = isdone
        update_data["title"] = jobTitle
        update_data["description"] = jobDescription
        update_data["userID"] = userid
        update_data["job_id"] = jobid
        update_data["area"] = area
        update_data["basemap"] = basemap
        update_data["thumbnail"] = thumbnail

        
        startTime = datetime.fromisoformat(startTime)
        endTime = datetime.fromisoformat(endTime)
        update_data["processing_time"] = (endTime - startTime).total_seconds()

        if features:
            for key, value in features.items():
                print(f"Processing feature: {key}")
                geojsonpath = value.get("geojson")
                shapefiles = value.get("shapefile")
                polygons = value.get("polygons")
                num_instances = value.get("num_instances")

                update_data[key] = {}
                if geojsonpath is not None:
                    file_urls = self.upload_files(folder_name, [geojsonpath])
                    update_data[key]["geojsonpath"] = file_urls[0]
                if shapefiles is not None:
                    file_urls = self.upload_files(folder_name, [shapefiles])
                    update_data[key]["shapefiles"] = file_urls[0]
                if polygons is not None:
                    update_data[key]["polygons"] = polygons
                if num_instances is not None:
                    update_data[key]["num_instances"] = num_instances

        # print("Update data:", update_data)
        self.jobs_ref.child("Drangeue_jobs").child(jobid).set(update_data)
        # self.jobs_ref.child(jobid).update(update_data)

    def get_job(self, jobid):
        job = self.jobs_ref.child(jobid).get()
        if job.val():
            return job.val()
        else:
            return None
    def get_jobs_by_email(self, email):
        jobs = self.jobs_ref.order_by_child("userID").equal_to(email).get()
        if jobs.each():
            return [
                {
                    "job_id": job.val().get("job_id"),
                    "title": job.val().get("title"),
                    "endTime": job.val().get("startTime"),
                    "area": job.val().get("area"),
                    "thumbnail": job.val().get("thumbnail")
                }
                for job in jobs.each()
            ]
        else:
            return []

    def upload_files(self, folder_name, files):
        file_urls = []
        for file in files:
            # Get the filename from the file path
            filename = os.path.basename(file)

            # Path in storage where the file will be uploaded
            storage_path = f"{folder_name}/{filename}"

            # Upload the file
            self.storage.child(storage_path).put(file)

            # Get the URL of the uploaded file
            url = self.storage.child(storage_path).get_url(None)
            file_urls.append(url)
        return file_urls
    def add_user(self, display_name, email):
        display_name = display_name + " "
        display_name = display_name.split()
        first_name = display_name[0]
        last_name = display_name[1]
        try:
            # Add user details to the database, excluding the password
            data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email
            }
            self.db.child(self.tables["users"]).push(data)
            return True  # Registration successful
        except:
            return False  # Registration failed
    def authenticate_user(self, email, password):
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            return True  # Authentication successful
        except:
            return False  # Authentication failed
        
    def register_user(self, first_name, last_name, email, password, confirm_password):
        if password != confirm_password:
            return False  # Password confirmation failed
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            # Add user details to the database, excluding the password
            data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email
            }   
            self.db.child(self.tables["users"]).push(data)
            return True  # Registration successful
        except:
            return False  # Registration failed
    def get_thumbnail(self, coordinates):
        url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/pin-s+9ed4bd({coordinates[0]},{coordinates[1]})/{coordinates[0]},{coordinates[1]},14,0,0/800x600?access_token=pk.eyJ1IjoibXNoYW1pIiwiYSI6ImNsb2ZqMzFkbTBudTMycnFjM3QybW54MnAifQ.8SDg8QedEnsOGHU4AL9L4A"
        
        """
        Downloads an image from a URL, uploads it to Firebase Storage, and returns the URL of the uploaded image.

        :param url: URL of the image to download
        :return: URL of the uploaded image in Firebase Storage
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to download the image from {url}: {e}")
            return None

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name

        # Generate a unique file name using the current timestamp
        filename = f"thumbnail_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        folder_name = "thumbnails"

        try:
            # Upload the file to Firebase Storage
            storage_path = f"{folder_name}/{filename}"
            self.storage.child(storage_path).put(tmp_file_path)

            # Get the URL of the uploaded file
            url = self.storage.child(storage_path).get_url(None)
        finally:
            # Clean up the temporary file
            os.remove(tmp_file_path)

        return url
    def delete_table(self, table_name):
        """
        Deletes a table (node) from the Firebase Realtime Database.

        :param table_name: Name of the table (node) to delete
        """
        try:
            self.db.child(table_name).child(table_name).set(None)
            print(f"Table '{table_name}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting table '{table_name}': {e}")

    # TODO: my assumptions that the user table will have a key called api_key
    def check_user_api_key(self, api_key):
        """
        Checks if the API key provided by the user is valid.

        :param api_key: API key
        :return: True if the API key is valid, False otherwise
        """
        try:
            # Get the user details using the API key
            user = self.db.child(self.tables["users"]).order_by_child("api_key").equal_to(api_key).get()
            if user.each():
                return True
            else:
                return False
        except Exception as e:
            print(f"Error checking API key: {e}")
            return False

    # generate api keys using secrets.token_urlsafe(16)
    def generate_user_api_key(self, email):
        """
        Generates an API key for the user, stores it in the database and returns that api key.

        :param email: Email of the user
        :return: API key generated for the user
        """
        api_key = secrets.token_urlsafe(16)
        try:
            # Update the user details with the generated API key
            self.db.child(self.tables["users"]).child(email).update({"api_key": api_key})
            return api_key
        except Exception as e:
            print(f"Error generating API key: {e}")
            return None
        
    # delete api key of the user that user selected
    def delete_user_api_key(self, email, api_key):
        """
        Deletes the specified API key of the user.

        :param email: Email of the user
        :param api_key: API key to delete
        """
        try:
            # Fetch the current API key for the user
            user_data = self.db.child(self.tables["users"]).child(email).get().val()
            if not user_data or 'api_key' not in user_data:
                print(f"No API key found for user '{email}'.")
                return

            # Check if the specified API key matches the user's API key
            if user_data['api_key'] == api_key:
                # Update the user details to remove the API key
                self.db.child(self.tables["users"]).child(email).update({"api_key": None})
                print(f"API key '{api_key}' deleted successfully.")
            else:
                print(f"API key '{api_key}' does not match the user's current API key.")

        except Exception as e:
            print(f"Error deleting API key '{api_key}': {e}")
