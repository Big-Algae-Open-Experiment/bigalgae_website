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
    password = 'algaearegreat'
    
    message['From'] = me
    message['To'] = recipient_address
    
    email_server = smtplib.SMTP('smtp.gmail.com:587')
    email_server.ehlo()
    email_server.starttls()
    email_server.login(me, password)
    email_server.sendmail(me, recipient_address, message.as_string())
    email_server.quit()
        
    return(True)