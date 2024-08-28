# project core
from app.core.utils import connection_retry, since_timestamp, logger
from app.core.processors.exceptions import APIServerConnectionError

# project extension
from app.ext.kpm_audi.kpm_client import KPMClient
from app.ext.kpm_audi.exceptions import KPMApiError

# project service
from .config import (
    USE_KPM_SERVER,
    KPM_SERVER,
    KPM_USER_ID,
    KPM_CERT_FILE_PATH,
    KPM_INBOX,
    POST_BACK_TO_KPM,
)


@connection_retry(times=5)
def kpm_client(
    server: str = KPM_SERVER,
    user_id: str = KPM_USER_ID,
    cert_file_path: str = KPM_CERT_FILE_PATH,
    inbox: str = KPM_INBOX,
    post_back_to_kpm: bool = POST_BACK_TO_KPM,
) -> KPMClient:
    """Interact with the KPM server.

    !!! ATTENTION !!!
    Both PROD and DEV envs use the same KPM server, user & tls certificate.
    Only the INBOX is different.
    """
    try:
        kpm: KPMClient = KPMClient(
            server_url=server,
            user_id=user_id,
            cert_path=cert_file_path,
            inbox=inbox,
            post_back_to_kpm=post_back_to_kpm,
        ).connect()
        logger.debug("Testing connection to KPM server with a simple query ... ")
        kpm.query(since_timestamp(1))
        logger.info(f"👍👍👍 KPM server {USE_KPM_SERVER} connection successful 👍👍👍 ")
        return kpm
    except (KPMApiError, Exception) as ex:
        logger.error(
            f"Failed to connect to KPM server {KPM_USER_ID}@{KPM_SERVER}: {ex}"
        )
        raise APIServerConnectionError
