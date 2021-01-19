import sys
from emails import EmailHandler
import configparser


if __name__ == "__main__":
    if len(sys.argv) < 1:
        email = sys.argv[1]
        password = sys.argv[2]
        receivers = sys.argv[3]
    else:
        config = configparser.ConfigParser()
        config.read('config.ini')
        email = config['EMAIL']['SenderEmail']
        password = config['EMAIL']['PASSWORD']
        receivers = config['EMAIL']['ReceiverEmails']
    print(f'email: {email}, password: {password}')
    email_handler = EmailHandler(email_address=email, password=password)
    new_files = email_handler.fetch_emails()
    email_handler.send_emails(receivers=config['EMAIL']['ReceiverEmails'], attachments=new_files)

