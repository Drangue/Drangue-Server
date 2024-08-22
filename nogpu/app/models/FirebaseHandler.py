import pyrebase
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import tempfile


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
        self.auth = self.firebase.auth()
        self.tables = {
            "jobs": "Drangeue_jobs",
            "users": "Drangue_users",  # Adjust the name based on your database structure
            # Add more tables if needed
        }

        # Initialize the jobs table
        # self.jobs_ref = self.db.child("Drangeue_jobs")

    def add_job(self, area, thumbnail, userid, jobid, startTime,  jobTitle, jobDescription, isdone=False,):
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

    def update_job(self, thumbnail, area, basemap, userid, jobid, jobTitle, jobDescription,  startTime=None, endTime=None, isdone=None, features=None, center=(2.903955339201735, 101.68038385653196)):
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
        update_data["center"] = center

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
        except Exception as e:
            print("Registration Failed: " + str(e))
            return False  # Registration failed

    def authenticate_user(self, email, password):
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            return True  # Authentication successful
        except Exception as e:
            print("Login Error: ", e)
            return False  # Authentication failed

    def register_user(self, first_name, last_name, email, password, confirm_password):
        if password != confirm_password:
            return False  # Password confirmation failed
        try:
            user = self.auth.create_user_with_email_and_password(
                email, password)
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

    def get_profile(self, email):
        """
        Retrieves the profile data of a user from the database using their email.

        :param email: The email of the user to retrieve the profile for.
        :return: A dictionary with user profile data if found, else None.
        """
        try:
            # Query the database for the user with the specified email
            users = self.db.child(self.tables["users"]).order_by_child(
                "email").equal_to(email).get()
            print(users.each())
            if users.each():
                # Assuming there's only one user with this email, retrieve the first result
                for user in users.each():
                    user_record = user.val()
                    user_record = {
                        "firstName": user_record.get("first_name", "unknown"),
                        "lastName": user_record.get("last_name", "unknown"),
                        "email": user_record.get("email", "unknown"),
                        "password": "********",
                        "oldPassword": "",
                        "newPassword": "",
                    }
                    return user_record
            else:
                print(f"No profile found for email: {email}")
                return None
        except Exception as e:
            print(f"Error retrieving profile for email {email}: {e}")
            return None
        
        
    def update_profile(self, first_name, last_name, email, old_password, new_password):
        """
        Updates the profile of a user. If a new password is provided, updates the password.

        :param first_name: The new first name of the user.
        :param last_name: The new last name of the user.
        :param email: The email of the user whose profile is being updated.
        :param old_password: The old password of the user (required for password update).
        :param new_password: The new password of the user (if empty, password is not updated).
        :return: True if profile update was successful, False otherwise.
        """
        try:
            # If new_password is provided, update the password
            if new_password:
                # Authenticate the user with the old password
                user = self.auth.sign_in_with_email_and_password(email, old_password)
                id_token = user['idToken']
                self.auth.delete_user_account(id_token)
                # Update the password
                
                self.auth.create_user_with_email_and_password(email, new_password)
                print(f"Password changed successfully for user: {email}")
            
            # Update the user details in the database
            users = self.db.child(self.tables["users"]).order_by_child("email").equal_to(email).get()
            
            if users.each():
                # Assuming there's only one user with this email, update the first result
                for user in users.each():
                    user_key = user.key()  # Get the user's unique key in the database

                    # Update the record with the new information
                    updated_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email
                    }

                    self.db.child(self.tables["users"]).child(user_key).update(updated_data)
                    print(f"Profile updated successfully for user: {email}")
                    return True
            
            else:
                print(f"No profile found for email: {email}")
                return False

        except Exception as e:
            print(f"Error updating profile for {email}: {e}")
            return False
# # from firebase_handler import FirebaseHandler  # Adjust this import based on your file structure

# # Instantiate the FirebaseHandler class
# firebase_handler = FirebaseHandler()

# # Define user details
# first_name = "Mohammed"
# last_name = "Alshami"
# email = "test1@drangue.ai"

# # Register the user with Firebase Authentication
# # registration_success = firebase_handler.register_user(first_name, last_name, email, password, confirm_password)

# # Check if registration was successful
# if 1 ==1:
#     print("User registered successfully.")

#     # Add user details to the Firebase Realtime Database
#     add_user_success = firebase_handler.add_user(f"{first_name} {last_name}", email)

#     # Check if adding user to database was successful
#     if add_user_success:
#         print("User details added to the database successfully.")
#     else:
#         print("Failed to add user details to the database.")
# else:
#     print("Failed to register user.")
