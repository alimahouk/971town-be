import boto3
from botocore.exceptions import ClientError

from app.config import Configuration


###########
# CLASSES #
###########


class ObjectWrapper:
    """Encapsulates S3 object actions."""

    def __init__(self,
                 s3_object):
        """
        :param s3_object: A Boto3 Object resource. This is a high-level resource in Boto3
                          that wraps object actions in a class-like structure.
        """
        self.object = s3_object
        self.key = self.object.key

    def put(self,
            data,
            metadata: dict = {}):
        """
        Upload data to the object.
        :param data: The data to upload. This can either be bytes or a string. When this
                     argument is a string, it is interpreted as a file name, which is
                     opened in read bytes mode.
        """
        put_data = data

        if isinstance(data, str):
            try:
                put_data = open(data, "rb")
            except IOError:
                print(f"Expected file name or binary data, got '{data}'.")
                raise

        try:
            self.object.put(Body=put_data, Metadata=metadata)
            self.object.wait_until_exists()

            print(f"Put object '{self.object.key}' to bucket '{self.object.bucket_name}'.")
        except ClientError:
            print(f"Couldn't put object '{self.object.key}' to bucket '{self.object.bucket_name}'.")
            raise
        finally:
            if getattr(put_data, "close", None):
                put_data.close()

    def get(self):
        """
        Gets the object.
        :return: The object data in bytes.
        """
        try:
            body = self.object.get()['Body'].read()
            print(f"Got object '{self.object.key}' from bucket '{self.object.bucket_name}'.")
        except ClientError:
            print(f"Couldn't get object '{self.object.key}' from bucket '{self.object.bucket_name}'.")
            raise
        else:
            return body

    def exists(self,
               client) -> bool:
        exists = True

        try:
            client.head_object(Bucket=self.object.bucket_name, Key=self.object.key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # The key does not exist.
                exists = False
            elif e.response["Error"]["Code"] == 403:
                # Unauthorized, including invalid bucket.
                exists = False
            else:
                # Something else has gone wrong.
                raise e

        return exists

    @staticmethod
    def list(bucket,
             prefix: str = None):
        """
        Lists the objects in a bucket, optionally filtered by a prefix.
        :param bucket: The bucket to query. This is a Boto3 Bucket resource.
        :param prefix: When specified, only objects that start with this prefix are listed.
        :return: The list of objects.
        """
        try:
            if not prefix:
                objects = list(bucket.objects.all())
            else:
                objects = list(bucket.objects.filter(Prefix=prefix))
            print(f"Got objects {[o.key for o in objects]} from bucket '{bucket.name}'")
        except ClientError:
            print(f"Couldn't get objects for bucket '{bucket.name}'.")
            raise
        else:
            return objects

    def copy(self,
             dest_object):
        """
        Copies the object to another bucket.
        :param dest_object: The destination object initialized with a bucket and key.
                            This is a Boto3 Object resource.
        """
        try:
            dest_object.copy_from(CopySource={
                "Bucket": self.object.bucket_name,
                "Key": self.object.key
            })
            dest_object.wait_until_exists()
            print(
                f"Copied object from {self.object.bucket_name}:{self.object.key} to {dest_object.bucket_name}:{dest_object.key}.")
        except ClientError:
            print(
                f"Couldn't copy object from {self.object.bucket_name}:{self.object.key} to {dest_object.bucket_name}:{dest_object.key}.")
            raise

    def delete(self):
        """
        Deletes the object.
        """
        try:
            self.object.delete()
            self.object.wait_until_not_exists()
            print(f"Deleted object '{self.object.key}' from bucket '{self.object.bucket_name}'.")
        except ClientError:
            print(f"Couldn't delete object '{self.object.key}' from bucket '{self.object.bucket_name}'.")
            raise

    @staticmethod
    def delete_objects(bucket,
                       object_keys):
        """
        Removes a list of objects from a bucket.
        This operation is done as a batch in a single request.
        :param bucket: The bucket that contains the objects. This is a Boto3 Bucket
                       resource.
        :param object_keys: The list of keys that identify the objects to remove.
        :return: The response that contains data about which objects were deleted
                 and any that could not be deleted.
        """
        try:
            response = bucket.delete_objects(Delete={
                "Objects": [{
                    "Key": key
                } for key in object_keys]
            })

            if "Deleted" in response:
                print(
                    f"Deleted objects '{[del_obj['Key'] for del_obj in response['Deleted']]}' from bucket '{bucket.name}'.")
            if 'Errors' in response:
                print(f"Could not delete objects", [
                      f"{del_obj['Key']}: {del_obj['Code']}" for del_obj in response['Errors']], f" from bucket '{bucket.name}'.")
        except ClientError:
            print("Couldn't delete any objects from bucket %s.", bucket.name)
            raise
        else:
            return response

    @staticmethod
    def empty_bucket(bucket):
        """
        Remove all objects from a bucket.
        :param bucket: The bucket to empty. This is a Boto3 Bucket resource.
        """
        try:
            bucket.objects.delete()
            print(f"Emptied bucket '{bucket.name}'.")
        except ClientError:
            print(f"Couldn't empty bucket '{bucket.name}'.")
            raise

    def put_acl(self,
                email):
        """
        Applies an ACL to the object that grants read access to an AWS user identified
        by email address.
        :param email: The email address of the user to grant access.
        """
        try:
            acl = self.object.Acl()
            # Putting an ACL overwrites the existing ACL, so append new grants
            # if you want to preserve existing grants.
            grants = acl.grants if acl.grants else []
            grants.append({
                "Grantee": {
                    "Type": "AmazonCustomerByEmail",
                    "EmailAddress": email
                },
                "Permission": "READ"
            })
            acl.put(
                AccessControlPolicy={
                    "Grants": grants,
                    "Owner": acl.owner
                }
            )
            print(f"Granted read access to {email}.")
        except ClientError:
            print(f"Couldn't add ACL to object '{self.object.key}'.")
            raise

    def get_acl(self):
        """
        Gets the ACL of the object.
        :return: The ACL of the object.
        """
        try:
            acl = self.object.Acl()
            print(f"Got ACL for object {self.object.key} owned by", acl.owner["DisplayName"])
        except ClientError:
            print(f"Couldn't get ACL for object {self.object.key}.")
            raise
        else:
            return acl


class s3:
    client = boto3.client("s3",
                          aws_access_key_id=Configuration.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=Configuration.AWS_SECRET_ACCESS_KEY,
                          region_name=Configuration.AWS_REGION)
    resource = boto3.resource("s3",
                              aws_access_key_id=Configuration.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=Configuration.AWS_SECRET_ACCESS_KEY,
                              region_name=Configuration.AWS_REGION)

    @staticmethod
    def delete_media(object_key: str) -> None:
        bucket = s3.resource.Bucket(Configuration.AWS_S3_MEDIA_BUCKET_NAME)
        obj_wrapper = ObjectWrapper(bucket.Object(object_key))
        obj_wrapper.delete()

    @staticmethod
    def upload_media(file_path: str,
                     object_key: str,
                     metadata: dict = {}) -> None:
        bucket = s3.resource.Bucket(Configuration.AWS_S3_MEDIA_BUCKET_NAME)

        with open(file_path, mode="rb") as file:
            obj_wrapper = ObjectWrapper(bucket.Object(object_key))

            if not obj_wrapper.exists(s3.client):
                obj_wrapper.put(file, metadata=metadata)
            else:
                print(f"S3 object with key '{object_key}' already exists in bucket '{bucket.name}'.")
