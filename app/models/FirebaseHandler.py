import pyrebase
import os
from dotenv import load_dotenv
from datetime import datetime
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
        self.jobs_ref = self.db.child("jobs")

    def add_job(self, userid, jobid, startTime, isdone=False):
        job_data = {
            "userid": userid,
            "jobid": jobid,
            "startTime": startTime,
            "isdone": isdone
        }
        self.jobs_ref.child(jobid).set(job_data)

    def update_job(self, jobid, startTime=None, endTime=None, isdone=None, features=None):
        update_data = {}
        folder_name = f"job_{jobid}"

        update_data["startTime"] = startTime
        update_data["endTime"] = endTime
        update_data["isdone"] = isdone
        
        
        startTime = datetime.fromisoformat(startTime)
        endTime = datetime.fromisoformat(endTime)
        update_data["processing_time"] = (endTime - startTime).total_seconds()

        if features:
            for key, value in features.items():
                print(f"Processing feature: {key}")
                geojsonpath = value.get("geojson")
                shapefiles = value.get("shapefile")
                polygons = value.get("polygons")

                update_data[key] = {}
                if geojsonpath is not None:
                    file_urls = self.upload_files(folder_name, [geojsonpath])
                    update_data[key]["geojsonpath"] = file_urls[0]
                if shapefiles is not None:
                    file_urls = self.upload_files(folder_name, [shapefiles])
                    update_data[key]["shapefiles"] = file_urls[0]
                if polygons is not None:
                    update_data[key]["polygons"] = polygons

        # print("Update data:", update_data)
        self.jobs_ref.child("jobs").child(jobid).set(update_data)
        # self.jobs_ref.child(jobid).update(update_data)

    def get_job(self, jobid):
        job = self.jobs_ref.child(jobid).get()
        if job.val():
            return job.val()
        else:
            return None

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
