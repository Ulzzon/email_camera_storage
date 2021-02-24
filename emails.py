import email
import os
import imaplib
import datetime
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

SERVER = 'imap.gmail.com'
DAYS = 7

class EmailHandler():

    def __init__(self, email_address, password):
        self.email = email_address
        self.password = password
        self.mail = None
        self.activity_log = []

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
                dirname = os.path.dirname(__file__)
                file_date = self._convert_to_file_date(msg['date'])

                att_path = os.path.join(dirname, f'temp/{filename}_{file_date}.JPG')
                print(f'Attachment downloaded: {att_path}')

                if not os.path.isfile(att_path):
                    fp = open(att_path, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
                    new_file = True
            return new_file, att_path

    def get_all_emails(self):
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=DAYS)

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
        week_ago = today - datetime.timedelta(days=7)
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
        new_file = False
        new_files = []
        pictures = 0

        for mail_id in mail_ids:
            # the fetch function fetch the email given its id
            # and format that you want the message to be
            if self._check_if_new_mail(f'{mail_id}'):
                continue
            status, data = self.mail.fetch(mail_id, '(RFC822)')
            mail_content = ''
            # the content data at the '(RFC822)' format comes on
            # a list with a tuple with header, content, and the closing
            # byte b')'
            for response_part in data:
                # so if its a tuple...
                if isinstance(response_part, tuple):
                    # we go for the content at its second element
                    # skipping the header at the first and the closing
                    # at the third
                    message = email.message_from_bytes(response_part[1])
                    mail_subject = message['subject']
                    mail_date = message['date']

                    # then for the text we have a little more work to do
                    # because it can be in plain text or multipart
                    # if its not plain text we need to separate the message
                    # from its annexes to get the text
                    if message.is_multipart():
                        
                        new_file, file_path = self.save_attachment(message)
                        # on multipart we have the text message and
                        # another things like annex, and html version
                        # of the message, in that case we loop through
                        # the email payload
                        for part in message.get_payload():
                            # if the content type is text/plain
                            # we extract it
                            if part.get_content_type() == 'text/plain':
                                mail_content += part.get_payload()
                    else:
                        # if the message isn't multipart, just extract it
                        mail_content = message.get_payload()

                    print(f'Content: {mail_content}')

                    if new_file:
                        print(f'New file at: {file_path}')
                        new_files.append(file_path)
                        try:
                            numbers = [int(s) for s in mail_content.split() if s.isdigit()]
                            pictures += numbers[0]
                        except Exception as e:
                            pictures += 1
                            numbers.append(1)
                        self.store_email_log(mail_id, self._convert_to_file_date(mail_date), numbers[0], file_path)

        return new_files, pictures

    def send_emails(self, receivers, number_of_pictures=0, attachments=[]):
        sender_email = self.email
        password = self.password
        html_activity = ''

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
            message.attach(self._add_attachments(attachment))

        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receivers.split(','), message.as_string()
            )

    def _add_attachments(self, file_path):
        # Open PDF file in binary mode
        with open(file_path, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email    
        encoders.encode_base64(part)
        filename = file_path.split('/')[-1]

        # Add header as key/value pair to attachment part
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}',
        )

        return part

    def store_email_log(self, mail_id, timestamp, number_of_pictures, attachment='None'):
        dirname = os.path.dirname(__file__)
        logfile = os.path.join(dirname, 'output', 'logfile.txt')
        self.activity_log.append(f'{timestamp} images: {number_of_pictures}')
        with open(logfile,'a+') as log:
            log.write(f'{mail_id},{timestamp},{number_of_pictures},{attachment} \n')

    def _check_if_new_mail(self, mail_id):
        exists = False
        dirname = os.path.dirname(__file__)
        logfile = os.path.join(dirname, 'output', 'logfile.txt')
        if os.path.isfile(logfile):
            with open(logfile,'rt') as log:
                exists = [True for line in log.readlines() if line.startswith(mail_id)]
        return exists


    def _convert_to_file_date(self, mail_date):
        date_time_obj = datetime.datetime.strptime(mail_date, '%a, %d %b %Y %H:%M:%S %z')
        date_time_obj = date_time_obj.astimezone()
        return date_time_obj.strftime('%Y_%m_%d_T%H-%M')
