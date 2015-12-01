import random
import string
# Required to send confirmation emails
import smtplib
from email.mime.text import MIMEText

def generate_digit_code(N):
    ''' Returns a random string of digits of length N '''
    return(''.join(random.SystemRandom().choice(string.digits)     \
                   for _ in range(N)))    
    
def generate_validation_key(N):
    ''' Returns a random string of letters and digits of length N '''
    return(''.join(random.SystemRandom().choice(string.uppercase + \
                                                string.lowercase + \
                                                string.digits)     \
                   for _ in range(N)))

def send_email(message, recipient_address):
    me = 'bigalgaeopenexperiment@gmail.com'
    password = get_email_password()
    
    message['From'] = me
    message['To'] = recipient_address
    
    email_server = smtplib.SMTP('smtp.gmail.com:587')
    email_server.ehlo()
    email_server.starttls()
    email_server.login(me, password)
    email_server.sendmail(me, recipient_address, message.as_string())
    email_server.quit()
        
    return(True)
    
def get_email_password():
    with open('/var/www/html/baoe-app/.google_password') as f:
        return(f.readline().strip())

def process_advanced_measurements_string(input_string):
    return_list = []
    for value in input_string.split(','):
        if not value == '':
            return_list.append(float(value))
    return(return_list)