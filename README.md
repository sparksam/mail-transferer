# Mail Transferer
This application is an that can be used to transfer emails from a mailbox to another. This utility uses the IMAP protocol to access a mailbox, fecth the messages based on a search criteria, All messages will be fetched by default. 
The messages will then be sent using the SMTP protocol and then the messages are labelled and deleted if these options are specified. 

## Requirements

This project was tested with `Python 3` and Docker so in order to run the project, please install [Python](https://docs.python.org/3/using/index.html) or [Docker](https://www.docker.com/get-started/).
  
## Instructions

Before running the project please copy the [.env example file](.env.example) to `.env` and configure using to the [configuration](#configuration) section. 

### Windows/Mac/Linux
To run on your computer, please install python and run the following commands.
```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python -u src/app.py
```

### Docker
This repository has an image available [here](https://hub.docker.com/repositories/samuelklutse). In can be run using [this docker compose file](./docker-compose.yml).

```bash
    docker compose -f docker-compose.yml up
```

## Configuration

This repository relies on few environment variables. 
| Variable | Default| Description 
|---------|---------|---------|
| `IMAP_HOST`  | `imap.gmail.com`| *The IMAP Host*
| `IMAP_PORT`  | `993`| *The IMAP Port*
| `IMAP_FOLDER`  | `INBOX`| the folder to be selected from the mailbox
| `SMTP_HOST`  | `smtp.gmail.com`| The SMTP Host
| `SMTP_PORT`  | `587`| The SMTP Port
| `SMTP_USE_TLS`  | `true`| Use TLS when creating the SMTP client
| `EMAIL_USER`  | | The username to use to create the imap client. Usually this user is the email address of the account
| `EMAIL_PASSWORD`  | | The password of the email account used
| `TO_ADDRESS`  | | The account to transfer the emails to
| `FROM_ADDRESS`  | | The account from which the emails are sent from
| `LOG_LEVEL`  | `INFO`| The log level of the application
| `SEARCH_CRITERIA`  | `ALL`| The Search criteria used when search emails in the mailbox
| `DRY_RUN`  | `True`| Run the app with only fetching the emails without sending them to the destination account or moving them
| `DESTINATION_FOLDER`  | `False`| Destination folder to move the email to
| `MOVE_AFTER_PROCESSING`  | `False`| Move the emails to a different folder
| `DELETE_AFTER_PROCESSING`  | `False`| Delete the emails after processing them


## Limitations
- Some email providers limit the amount of emails So increasing the sleep time and refining the search criteria can help as a work around when hitting the limit.

## Author
- [Samuel Klutse](https://github.com/sparksam)