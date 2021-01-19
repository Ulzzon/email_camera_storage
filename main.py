import sys
from emails import EmailHandler


if __name__ == "__main__":
    print(f"Arguments count: {len(sys.argv)}")
    email = sys.argv[1]
    password = sys.argv[2]
    print(f'email: {email}, password: {password}')
    email_handler = EmailHandler(email_address=email, password=password)
    email_handler.fetch_emails()

    
