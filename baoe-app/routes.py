from flask import Flask, url_for, request, render_template, redirect
from app import app
from werkzeug import secure_filename
import os
from pymongo import MongoClient, errors
# Contains the functions required to process uploaded images
import bigalgae
# Required to create emails
from email.mime.text import MIMEText

client = MongoClient()

DB_NAME = 'bigalgae'

#COLLECTION_NAME = 'bioreactors'

#COUNTER = 'counter'

BIOREACTOR_COLLECTION = 'bioreactors'

GLOBAL_VARIABLE_COLLECTION = 'counter'

algal_species = ['Chlamydomonas reinhardtii', 'Chlorella vulgaris']

def returnNewID(global_variable_collection):
    new = global_variable_collection.find_and_modify({'_id': 'counter'}, \
                                                     {'$inc': {'seq': 1}}, \
                                                     new=True)
    return(str(new['seq']).zfill(4))

UPLOAD_FOLDER = 'uploaded_images/'
ALLOWED_EXTENSIONS = set(['jpeg', 'svg', 'jpg', 'txt'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def landing():
    return(render_template('Landing.html'))

@app.route('/about')
def about():
    return(render_template('About.html'))

@app.route('/thanks')
def thanks():
    return(render_template('ThanksReactor.html'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return(render_template('RegisterBioreactor.html'));
    elif request.method == 'POST':
        db = client[DB_NAME]
        reactors = db[BIOREACTOR_COLLECTION]
        
        global_var_collection = db[GLOBAL_VARIABLE_COLLECTION]
        
        user_data = request.get_json()
        upload_code = bigalgae.generate_digit_code(4)
        experiment_validation_code = bigalgae.generate_digit_code(6)
        validation_key = bigalgae.generate_validation_key(32)
        success = False

        while not success:
            try:
                id_str = returnNewID(global_var_collection)
                
                reactors.insert({'_id': id_str, \
                                'name': user_data['name'], \
                                'email': user_data['email'], \
                                'latitude': user_data['latitude'], \
                                'longitude': user_data['longitude'], \
                                'upload_code': upload_code, \
                                'experiment_validation_code': experiment_validation_code, \
                                'validation_key': validation_key, \
                                'validated': False, \
                                'experiments': []})
                success = True
                
                validation_link = url_for('validate', reactor_id=id_str, _external=True) + '?key=' + validation_key
                confirmation_email = MIMEText(render_template('ConfirmationEmail', \
                                                              validation_link = validation_link, \
                                                              reactor_id = id_str))
                confirmation_email['Subject'] = 'Big Algae Open Experiment Validation'

                recipient = user_data['email']
                
                bigalgae.send_email(confirmation_email, recipient)

            except errors.DuplicateKeyError:
                success = False
                
        return(url_for('thanks'))

@app.route('/reactor/<reactor_id>')
def reactor(reactor_id):
    db = client[DB_NAME]
    reactors = db[BIOREACTOR_COLLECTION]
    id_search = [res for res in reactors.find({'_id': reactor_id})]
    if len(id_search) == 0:
        return(render_template('SorryReactor.html', search_id=reactor_id))
    else:
        if id_search[0]['validated']:
            return(render_template('ReactorPage.html', reactor=id_search[0]))
        else:
            return(render_template('UnvalidatedReactor.html', reactor=reactor_id))

@app.route('/reactor/<reactor_id>/register', methods=['GET', 'POST'])
def register_experiment(reactor_id):
    db = client[DB_NAME]
    reactors = db[BIOREACTOR_COLLECTION]
    id_search = [res for res in reactors.find({'_id': reactor_id})]
    if request.method == 'GET':
        if len(id_search) == 0:
            return(render_template('SorryReactor.html', search_id=reactor_id))
        else:
            return(render_template('RegisterExperiment.html', algal_species=algal_species, incorrect_password=False))
    elif request.method == 'POST':
        if len(id_search) == 0:
            return(render_template('SorryReactor.html', search_id=reactor_id))
        else:
            species = request.form['algae_dropdown']
            user_code = request.form['experiment_validation']
            experiment_validation_code = id_search[0]['experiment_validation_code']
            if experiment_validation_code == user_code:
                experiment_id = str(len(id_search[0]['experiments']) + 1)
                
                reactors.find_and_modify({'_id': reactor_id}, \
                                        {'$push': {'experiments': \
                                            {'id': experiment_id, \
                                            'species': species, \
                                            'measurements': []}
                                        }})

                return(redirect(url_for('experiment', reactor_id=reactor_id, experiment_id=experiment_id)))
            else:
                return(render_template('RegisterExperiment.html', algal_species=algal_species, incorrect_password=True))

@app.route('/reactor/<reactor_id>/validate')
def validate(reactor_id):
    db = client[DB_NAME]
    reactors = db[BIOREACTOR_COLLECTION]
    id_search = [res for res in reactors.find({'_id': reactor_id})]
    if len(id_search) == 0:
        return(render_template('SorryReactor.html', search_id=reactor_id))
    else:
        # if the bioreactor has already been validated, just direct to its page
        if id_search[0]['validated']:
            return(redirect(url_for('reactor', reactor_id=reactor_id)))
        key = request.args.get('key')
        # if the key is incorrect
        if key != id_search[0]['validation_key']:
            return(render_template('WrongKeyReactor.html', search_id=reactor_id))
        else:
            reactors.find_and_modify({'_id': reactor_id}, \
                                     {'$set': {'validated': True}})
            
            info_email = MIMEText(render_template('FurtherInformationEmail', \
                                                  experiment_validation_code = id_search[0]['experiment_validation_code'], \
                                                  upload_code = id_search[0]['upload_code'], \
                                                  reactor_id = reactor_id))
            info_email['Subject'] = 'Big Algae Open Experiment Important Information'

            recipient = id_search[0]['email']
            
            bigalgae.send_email(info_email, recipient)
                                 
            return(render_template('SuccessfulValidation.html', reactor_id = reactor_id))

@app.route('/reactor/<reactor_id>/experiment/<experiment_id>')
def experiment(reactor_id, experiment_id):
    db = client[DB_NAME]
    reactors = db[BIOREACTOR_COLLECTION]
    exp_search = [res for res in reactors.find({'_id': reactor_id, 'experiments': {'$elemMatch': {'id': experiment_id}}})]
    if len(exp_search) == 0:
        return(render_template('SorryExperiment.html', \
                               reactor_id=reactor_id,  \
                               experiment_id=experiment_id))
    else:
        experiment_dict = exp_search[0]['experiments'][int(experiment_id)-1]
        return(render_template('ExperimentPage.html', \
                               reactor_id=reactor_id, \
                               experiment_id=experiment_id, \
                               species=experiment_dict['species']))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return(render_template('Upload.html'))
    if request.method == 'POST':
        file = request.files['upload_picture']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('about'))
