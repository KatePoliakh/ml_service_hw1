from app.logger import logger

def upload_to_s3(local_path, remote_path):
    logger.info("upload_to_s3 stub: %s -> %s", local_path, remote_path)
    return True

def download_from_s3(remote_path, local_path):
    logger.info("download_from_s3 stub: %s -> %s", remote_path, local_path)
    return True