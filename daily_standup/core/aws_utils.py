# daily_standup/core/aws_utils.py
import logging
import requests
from botocore.exceptions import NoCredentialsError
from .config import config

logger = logging.getLogger(__name__)

class AWSUtils:
    def __init__(self, s3_client=None):
        """Optional S3 client if we want to use boto3 for signed URLs"""
        self.s3 = s3_client
        self.bucket_name = config.AWS_SUMMARY_BUCKET

    def fetch_summary_doc_from_url(self, url: str) -> str:
        """
        Fetch a summary document from S3 via pre-signed or public URL.
        Supports .txt and .md docs.
        """
        try:
            logger.info(f"🌐 Fetching summary doc from URL: {url}")
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                raise ValueError(f"Failed to fetch doc, status: {response.status_code}")

            content = response.text.strip()
            if not content:
                raise ValueError("Summary document is empty!")

            logger.info("✅ Summary document fetched successfully")
            return content

        except NoCredentialsError:
            logger.error("❌ AWS credentials not found (if using signed URLs)")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching summary doc: {e}")
            raise
