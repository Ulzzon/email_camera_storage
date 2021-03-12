import json
import email
import os
import boto3
import datetime
import imaplib
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


database = boto3.resource('dynamodb')
s3 = boto3.resource('s3')
SERVER = 'imap.gmail.com'


def handler(event, context):
    region = os.environ['AWS_REGION']
    email_address = os.environ['EMAIL_ADDRESS']
    email_password = os.environ['EMAIL_PASSWORD']
    search_days = int(os.environ['DAYS_TO_SEARCH'])
    email_receivers = os.environ['EMAIL_RECEIVERS']

    print('Region: {0}, email{1}'.format(region, email_address))
    email_handler = EmailHandler(email_address=email_address, password=email_password)
    new_emails_received = email_handler.fetch_emails()
    email_handler.send_emails(email_receivers, new_emails_received)
    table = database.Table(os.environ['LOG_TABLE_NAME'])

    print('Table name: {0}'.format(table.name))

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
    }




class EmailHandler():

    def __init__(self, email_address, password):
        self.email = email_address
        self.password = password
        self.mail = None
        self.activity_log = []
        self.table = database.Table(os.environ['LOG_TABLE_NAME'])
        self.s3_storage = s3.Bucket(os.environ['S3_BUCKET_NAME'])

    def save_attachment(self, msg, download_folder="/tmp"):
            """
            Given a message, save its attachments to the specified
            download folder (default is /tmp)
            return: file path to attachment
            """
            att_path = "No attachment found."
            new_file = False
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename().split('.')[0]
                file_date = self._convert_to_file_date(msg['date'])

                att_path = os.path.join(download_folder, f'{filename}_{file_date}.JPG')
                print(f'Attachment downloaded: {att_path}')
                
                image_data = part.get_payload(decode=True)
                new_file = True
                self.s3_storage.put_object(Key=att_path, Body=image_data)
            return new_file, image_data

    def get_all_emails(self, search_days=7):
        # connect to the server and go to its inbox
        self.mail = imaplib.IMAP4_SSL(SERVER)
        try:
            self.mail.login(self.email, self.password)
        except Exception as e:
            print(e)
            exit()

        # we choose the inbox but you can select others
        self.mail.select('inbox')
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=search_days)
        string_week = week_ago.strftime('"%d-%b-%Y"')
        print('week' + string_week)
        # we'll search using the ALL criteria to retrieve
        # every message inside the inbox
        # it will return with its status and a list of ids
        status, data = self.mail.search(None, 'FROM', '"Kamera"', 'SINCE', string_week)
        # the list returned is a list of bytes separated
        # by white spaces on this format: [b'1 2 3', b'4 5 6']
        # so, to separate it first we create an empty list
        mail_ids = []
        # then we go through the list splitting its blocks
        # of bytes and appending to the mail_ids list
        for block in data:
            # the split function called without parameter
            # transforms the text or bytes into a list using
            # as separator the white spaces:
            # b'1 2 3'.split() => [b'1', b'2', b'3']
            mail_ids += block.split()
        return mail_ids

    def fetch_emails(self):
        mail_ids = self.get_all_emails()
        email_date_received = None
        email_attachment = None
        new_emails_received = []

        for mail_id in mail_ids:
            # the fetch function fetch the email given its id
            # and format that you want the message to be
            mail_id = mail_id.decode('utf-8')
            if self._check_if_new_mail(f'{mail_id}'):
                print(f'New email received with id:{mail_id}')
                status, data = self.mail.fetch(mail_id, '(RFC822)')
                timestamp, attachment = self.parse_email(data)
                new_emails_received.append((mail_id, timestamp, attachment))
        if new_emails_received:
            self.store_email_log(new_emails_received)
        return new_emails_received
    
    def parse_email(self, email_data):
        mail_content = ''
        email_attachment = None
        # the content data at the '(RFC822)' format comes on
        # a list with a tuple with header, content, and the closing
        # byte b')'
        for response_part in email_data:
            # so if its a tuple...
            if isinstance(response_part, tuple):
                # we go for the content at its second element
                # skipping the header at the first and the closing
                # at the third
                message = email.message_from_bytes(response_part[1])
                mail_subject = message['subject']
                mail_date = message['date']
                new_file, email_attachment = self.save_attachment(message)
        return mail_date, email_attachment


    def send_emails(self, receivers, attachments=[]):
        sender_email = self.email
        password = self.password
        html_activity = ''
        number_of_pictures = len(attachments)

        message = MIMEMultipart("alternative")
        message["Subject"] = "Summering från åtelkameran"
        message["From"] = f'Tobias <{sender_email}>'
        message["To"] = f'{receivers}'
        for activity in self.activity_log:
            html_activity += f'<li>{activity}</li>'
        # Create the plain-text and HTML version of your message
        text = f"""\
        Godmorgon,
        
        Här kommer senaste mailet från kameran
        Antal bilder: {number_of_pictures}
        """
        
        html = f"""\
        <html>
        <body>
            <p>Godmorgon,<br>
            Här kommer summering av senaste dygnets rapporter från kameran<br>
            Antal bilder: {number_of_pictures}<br>

            Aktiviter:
            <ol>
            {html_activity}
            </ol>
            </p>
        </body>
        </html>
        """

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)
        for attachment in attachments[:15]:
            image_name = '{}.JPG'.format(attachment[1])
            message.attach(self._add_image_as_attachment(attachment[2], image_name))

        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receivers.split(','), message.as_string()
            )

    def _add_image_as_attachment(self, image_data, image_name):
        part = MIMEImage(image_data, _subtype='jpeg')
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {image_name}',
        )
        return part

    def store_email_log(self, list_to_log):
        with self.table.batch_writer() as batch:
            for (mail_id, timestamp, attachment) in list_to_log:
                batch.put_item(
                    Item={
                        'mail_id': mail_id,
                        'timestamp': timestamp,
                        'number_of_pictures': 0,
                        'image_array': attachment
                    }
                )

                self.activity_log.append(f'{timestamp}')


    def _check_if_new_mail(self, mail_id):
        response = self.table.get_item(
            Key ={
                'mail_id': mail_id,
        })
        print(f'Database response: {response}')
        if response.get('Item', None) is None:
            return True
        else:
            return False


    def _convert_to_file_date(self, mail_date):
        date_time_obj = datetime.datetime.strptime(mail_date, '%a, %d %b %Y %H:%M:%S %z')
        date_time_obj = date_time_obj.astimezone()
        return date_time_obj.strftime('%Y_%m_%d_T%H-%M')


class EmailObject():
    
    @property
    def received(self):
        return self._received

    @property
    def attachment(self):
        return self._attachment
    
    def __init__(self, time_received, attachment):
        super().__init__()
        self._received = time_received
        self._attachment = attachment