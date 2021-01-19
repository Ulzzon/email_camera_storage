import email
import os
import imaplib
import datetime

SERVER = 'imap.gmail.com'
DAYS = 7

class EmailHandler():

    def __init__(self, email_address, password):
        self.email = email_address
        self.password = password
        self.mail = None
        
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
                mail_date = msg['date']
                date_time_obj = datetime.datetime.strptime(mail_date, '%a, %d %b %Y %H:%M:%S %z')
                file_date = date_time_obj.strftime('%Y_%m_%d')

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

        # now for every id we'll fetch the email
        # to extract its content
        for i in mail_ids:
            # the fetch function fetch the email given its id
            # and format that you want the message to be
            status, data = self.mail.fetch(i, '(RFC822)')

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
                        mail_content = ''
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

                    print(f'Subject: {mail_subject}')
                    print(f'Content: {mail_content}')
                    print(f'Sent on: {mail_date}')
                    if new_file:
                        print(f'New file at: {file_path}')

    def send_emails(self):
        pass