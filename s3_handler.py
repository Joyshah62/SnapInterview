import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# Load environment variables
load_dotenv()

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


class S3Handler:
    """
    Handles file uploads to AWS S3 with username-based folder structure
    """
    
    def __init__(self):
        """Initialize S3 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
            self.bucket_name = S3_BUCKET_NAME
            print(f"✅ S3 Handler initialized for bucket: {self.bucket_name}")
        except Exception as e:
            print(f"❌ Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def upload_file(self, local_file_path: str, username: str, 
                    custom_filename: str = None, folder: str = "recordings") -> dict:
        """
        Upload a file to S3 with username-based organization
        
        Args:
            local_file_path: Path to the local file to upload
            username: Username for organizing files
            custom_filename: Optional custom filename (uses original if None)
            folder: Subfolder type (e.g., 'recordings', 'transcripts', 'documents')
        
        Returns:
            dict with 'success', 'url', 'key', and 'message'
        """
        if not self.s3_client:
            return {
                'success': False,
                'message': 'S3 client not initialized',
                'url': None,
                'key': None
            }
        
        if not os.path.exists(local_file_path):
            return {
                'success': False,
                'message': f'File not found: {local_file_path}',
                'url': None,
                'key': None
            }
        
        try:
            # Generate filename
            if custom_filename:
                filename = custom_filename
            else:
                filename = os.path.basename(local_file_path)
            
            # Create S3 key with username/folder/filename structure
            s3_key = f"{username}/{folder}/{filename}"
            
            # Determine content type
            content_type = self._get_content_type(local_file_path)
            
            # Upload file
            self.s3_client.upload_file(
                local_file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': content_type}
            )
            
            # Generate URL
            file_url = f"https://{self.bucket_name}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
            
            print(f"✅ Uploaded: {filename} -> {s3_key}")
            
            return {
                'success': True,
                'message': 'Upload successful',
                'url': file_url,
                'key': s3_key,
                'filename': filename
            }
        
        except FileNotFoundError:
            return {
                'success': False,
                'message': 'File not found',
                'url': None,
                'key': None
            }
        except NoCredentialsError:
            return {
                'success': False,
                'message': 'AWS credentials not found',
                'url': None,
                'key': None
            }
        except ClientError as e:
            return {
                'success': False,
                'message': f'AWS error: {str(e)}',
                'url': None,
                'key': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Upload failed: {str(e)}',
                'url': None,
                'key': None
            }
    
    def upload_audio_recording(self, local_file_path: str, username: str) -> dict:
        """
        Convenience method for uploading audio recordings
        
        Args:
            local_file_path: Path to the audio file
            username: Username for organizing files
        
        Returns:
            dict with upload result
        """
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = Path(local_file_path).suffix
        custom_filename = f"interview_{timestamp}{extension}"
        
        return self.upload_file(
            local_file_path=local_file_path,
            username=username,
            custom_filename=custom_filename,
            folder="recordings"
        )
    
    def list_user_files(self, username: str, folder: str = None) -> list:
        """
        List all files for a specific user
        
        Args:
            username: Username to search for
            folder: Optional folder filter (e.g., 'recordings')
        
        Returns:
            List of file objects with metadata
        """
        if not self.s3_client:
            print("❌ S3 client not initialized")
            return []
        
        try:
            prefix = f"{username}/"
            if folder:
                prefix = f"{username}/{folder}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            files = []
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'url': f"https://{self.bucket_name}.s3.{AWS_REGION}.amazonaws.com/{obj['Key']}"
                })
            
            return files
        
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            s3_key: The S3 key of the file to delete
        
        Returns:
            True if successful, False otherwise
        """
        if not self.s3_client:
            print("❌ S3 client not initialized")
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            print(f"✅ Deleted: {s3_key}")
            return True
        
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False
    
    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to a file
        
        Args:
            s3_key: The S3 key of the file
            expiration: URL expiration time in seconds (default 1 hour)
        
        Returns:
            Presigned URL string or None if failed
        """
        if not self.s3_client:
            print("❌ S3 client not initialized")
            return None
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        
        except Exception as e:
            print(f"❌ Error generating presigned URL: {e}")
            return None
    
    @staticmethod
    def _get_content_type(file_path: str) -> str:
        """
        Determine content type based on file extension
        
        Args:
            file_path: Path to the file
        
        Returns:
            MIME type string
        """
        extension = Path(file_path).suffix.lower()
        
        content_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        
        return content_types.get(extension, 'application/octet-stream')


# Example usage and testing
if __name__ == "__main__":
    print("Testing S3 Handler...")
    
    s3 = S3Handler()
    
    # Test upload (uncomment and modify path to test)
    # result = s3.upload_audio_recording(
    #     local_file_path="recordings/interview_1234567890.wav",
    #     username="test_user"
    # )
    # print(result)
    
    # Test listing files
    # files = s3.list_user_files("test_user", folder="recordings")
    # for file in files:
    #     print(f"- {file['key']} ({file['size']} bytes)")
    
    print("S3 Handler ready!")