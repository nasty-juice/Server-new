import os
import uuid

def secure_upload_to(instance, filename):
    # Generate a unique filename using UUID
    unique_filename = f"{uuid.uuid4().hex}{os.path.splitext(filename)[1]}"
    print(unique_filename)
    return os.path.join('secure', unique_filename)