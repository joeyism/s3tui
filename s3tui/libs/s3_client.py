"""AWS S3 client wrapper"""

from typing import List, Tuple
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class S3Client:
    """Wrapper for AWS S3 operations"""

    def __init__(self):
        self.s3 = boto3.client('s3')
        self.resource = boto3.resource('s3')

    def list_buckets(self) -> List[str]:
        """List all S3 buckets"""
        try:
            response = self.s3.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]
        except (ClientError, NoCredentialsError) as e:
            raise Exception(f"Error listing buckets: {str(e)}")

    def list_objects(self, bucket: str, prefix: str = '') -> Tuple[List[str], List[str]]:
        """
        List objects in a bucket with a given prefix
        Returns: (folders, files)
        """
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/')

            folders = []
            files = []

            for page in pages:
                # Get "folders" (common prefixes)
                for prefix_obj in page.get('CommonPrefixes', []):
                    folder_path = prefix_obj['Prefix']
                    # Extract just the folder name
                    folder_name = folder_path.rstrip('/').split('/')[-1]
                    folders.append(folder_name)

                # Get files
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    # Skip if it's just the prefix itself
                    if key == prefix:
                        continue
                    # Extract just the file name (not full path)
                    file_name = key[len(prefix):].split('/')[0]
                    if file_name and file_name not in folders:
                        files.append(file_name)

            return sorted(folders), sorted(files)
        except ClientError as e:
            return [], []

    def download_file(self, bucket: str, key: str, local_path: str) -> None:
        """Download a file from S3"""
        self.s3.download_file(bucket, key, local_path)
