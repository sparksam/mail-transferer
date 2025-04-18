import smtplib
import imaplib
import email
import os
import logging
import sys
import time
import traceback
from datetime import datetime
import re

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))


def initialize_imap_client():
    logging.info("Initializing the IMAP client")
    imap_host = os.getenv("IMAP_HOST", "imap.gmail.com")
    imap_port = int(os.getenv("IMAP_PORT", 993))
    imap_folder = os.getenv("IMAP_FOLDER", "INBOX")
    imap_use_ssl = bool(os.getenv("IMAP_USE_SSL", True))
    logging.debug(f"IMAP host: {imap_host}")
    logging.debug(f"IMAP folder: {imap_folder}")
    try:
        logging.debug("Creating the IMAP client")
        imap_class = imaplib.IMAP4_SSL if imap_use_ssl else imaplib.IMAP4
        client = imap_class(imap_host, imap_port)
        logging.debug("Authenticating the IMAP client")
        client.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
        logging.debug("Selecting the IMAP folder")
        client.select(imap_folder, readonly=False)
        return client
    except Exception as e:
        logger.error(e)
        sys.exit(1)


def initialize_smtp_client():
    logging.info("Initializing the SMTP client")
    smtp_host = os.getenv("SMTP_HOST", "imap.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_use_tls = bool(os.getenv("SMTP_USE_TLS", True))
    try:
        logging.debug("Creating the SMTP client")
        smtp = smtplib.SMTP(smtp_host, smtp_port)
        if smtp_use_tls:
            smtp.starttls()
        logging.debug("Authenticating the SMTP client")
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
        return smtp
    except Exception as e:
        logger.error(e)
        sys.exit(1)


def search_email(imap_client: imaplib.IMAP4, max_retries) -> list:
    search_criteria = os.getenv("SEARCH_CRITERIA", "ALL")
    logger.info(f"Searching the mailbox with criteria {search_criteria}")
    attempts = 1
    while True:
        if attempts > max_retries:
            sys.exit(1)
        try:
            typ, msgnums = imap_client.search(None, search_criteria)
            if msgnums is None or len(msgnums) == 0:
                return []
            return msgnums[0].split()
        except imaplib.IMAP4.abort as e:
            logger.error(e)
            attempts += 1
            imap_client = initialize_imap_client()


def get_uids(imap_client: imaplib.IMAP4, message_ids: list, max_retries, start_from: int) -> list:
    pattern_uid = re.compile(r'\d+ \(UID (?P<uid>\d+)\)')
    uids = []
    count = 1
    for msgid in message_ids:
        attempts = 1
        if attempts > max_retries:
            sys.exit(1)
        if count < start_from:
            count += 1
            continue
        try:
            logger.debug(
                f"{count}/{len(message_ids)}  Fetching email UID for id {msgid}")
            msg_uid = pattern_uid.match(imap_client.fetch(
                msgid, "(UID)")[1][0].decode("utf-8")).group("uid")
            uids.append(msg_uid)
            count += 1
        except imaplib.IMAP4.abort as e:
            traceback.print_exc()
            attempts += 1
            imap_client = initialize_imap_client()
    return uids


def move_messages(imap_client: imaplib.IMAP4, message_uids: list, dry_run: bool, max_retries: int):
    move_after_process = os.getenv("MOVE_AFTER_PROCESSING", "false")
    destination_folder = os.getenv(
        "DESTINATION_FOLDER", f"TRANSFERED/{datetime.now().strftime("%Y-%m-%d")}")
    logger.debug(f"Move After Processing: {move_after_process}")
    attempts = 1
    count = 1
    if not dry_run and move_after_process:
        try:
            for uid in message_uids:
                if attempts > max_retries:
                    sys.exit(1)
                logger.debug(
                    f"{count}/{len(message_uids)}  Moving email with id  {msgid} to {destination_folder}")
                if "gmail" in imap_client.host:
                    typ, data = imap_client.uid(
                        'STORE', uid, '+X-GM-LABELS', destination_folder)
                else:
                    typ, data = imap_client.uid(
                        'COPY', uid, destination_folder)
                logger.info(f"Message with uid {uid} moved successfully")
                count += 1
        except imaplib.IMAP4.abort as e:
            traceback.print_exc()
            attempts += 1
            imap_client = initialize_imap_client()


def delete_messages(imap_client: imaplib.IMAP4, message_uids: list, dry_run: bool, expunge: bool, max_retries: int):
    delete_after_process = os.getenv(
        "DELETE_AFTER_PROCESSING", "false") == "true"
    logger.debug(f"Delete After Processing: {delete_after_process}")
    attempts = 1
    count = 1
    if not dry_run and delete_after_process:
        try:
            for uid in message_uids:
                if attempts > max_retries:
                    sys.exit(1)
                logger.debug(
                    f"{count}/{len(message_uids)}  Deleting email {msgid}")
                mov, data = imap_client.uid(
                    'STORE', uid, '+FLAGS', '(\\Deleted)')
                logger.info(f"Message with uid {uid} deleted successfully")
                count += 1
            if expunge:
                imap_client.expunge()
        except imaplib.IMAP4.abort:
            traceback.print_exc()
            attempts += 1
            imap_client = initialize_imap_client()


def process_messages(imap_client: imaplib.IMAP4, smtp_client: smtplib.SMTP, message_ids: list, dry_run, max_retries, start_from):
    from_addr = os.getenv("FROM_ADDRESS")
    to_addr = os.getenv("TO_ADDRESS")
    attempts = 1
    count = 1
    sleep_time = int(os.getenv("SLEEP_TIME", 0))
    logger.debug(f"Dry run: {dry_run}")
    if len(message_ids) == 0:
        return
    if len(to_addr) == 0:
        logger.info("No TO address found! Exiting...")
        return
    for msgid in message_ids:
        if attempts > max_retries:
            sys.exit(1)
        if count < start_from:
            count += 1
            continue
        try:
            logger.info(f"Processing email {count}/{len(message_ids)}")
            status, data = imap_client.fetch(msgid, "(RFC822)")
            email_data = data[0][1]
            message = email.message_from_bytes(email_data)
            if "From" in message and "To" in message and "Subject" in message:
                logging.debug(
                    f"Email from {message['From']} to {message['To']}: {message['Subject']}")
            if from_addr is not None:
                message.replace_header("From", from_addr)
            else:
                from_addr = message["From"]

            message.replace_header("To", to_addr)
            if not dry_run:
                logger.debug(
                    f"Sending the mail with id {msgid} from {from_addr} to {to_addr}")
                smtp_client.sendmail(from_addr, to_addr, message.as_string())
                logger.debug(f"Successfully sent email {msgid}")
                time.sleep(sleep_time)
            count += 1

        except smtplib.SMTPException as e:
            traceback.print_exc()
            logger.warning(
                f"Unable to send email {msgid} from {from_addr} to {to_addr}.")
            logger.error(e)
        except imaplib.IMAP4.abort:
            traceback.print_exc()
            attempts += 1
            imap_client = initialize_imap_client()
            continue
        except KeyError:
            continue
        except Exception:
            traceback.print_exc()
            sys.exit(1)


def cleanup(imap_client: imaplib.IMAP4, smtp_client: smtplib.SMTP):
    try:
        if imap_client is not None:
            logger.info("Closing the IMAP client")
            imap_client.close()
            imap_client.logout()

        if smtp_client is not None:
            logging.info("Closing the SMTP client")
            smtp_client.quit()
        logger.info
    except Exception as e:
        logger.error(e)
        sys.exit(1)


if __name__ == "__main__":
    try:
        imap_client = initialize_imap_client()
        dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        logger.info(f"Dry Run: {dry_run}")
        max_retries = os.getenv("MAX_ATTEMPTS", 3)
        start_from = int(os.getenv("START_FROM", 0))
        expunge = os.getenv("EXPUNGE", "false") == "true"
        emails_to_transfer = search_email(imap_client, max_retries)
        smtp_client = initialize_smtp_client()
        if len(emails_to_transfer) == 0:
            logger.info("No email to transfer")
        else:
            logger.info(f"Found {len(emails_to_transfer)} mails.")
            process_messages(imap_client, smtp_client,
                             emails_to_transfer, dry_run, max_retries, start_from)
            uids = get_uids(imap_client, emails_to_transfer,
                            max_retries, start_from)
            move_messages(imap_client, uids, dry_run, max_retries)
            delete_messages(imap_client, uids, dry_run, expunge, max_retries)
        cleanup(imap_client, smtp_client)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
