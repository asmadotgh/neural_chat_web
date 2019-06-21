# Neural Chat Web

## Preparation - Key Concepts

This is the Django server portion of the Neural Chat project and is accompanied by another [**repository including our open-sourced dialog models**](https://github.com/natashamjaques/neural_chat). The system is engineered such that the two repositories can be maintained separately.
You can interact with our models here: **http://neural.chat**. 

The project is written in Django and contains setup and deployment scripts to configure Nginx, uWSGI, MySQL on a Unix environment.

The project has a bunch of convenience functions that work with [Autoenv](https://github.com/kennethreitz/autoenv), and it is highly recommended that you install it when working with this project.

These instructions assume you have a server on Google Cloud running Debian 9 or later. It is not required to use Google Cloud, but for the chatbots you will want a server with a GPU.

## Code Configuration

First of all, all passwords have been stripped out of all the code and must be replaced. You can do a search for the string EDITME to find all locations, but a full list is presented here:

* deploy/fabric/deploy.py `MYSQL_ROOT_PASSWORD` and `GITHUB_SSH_URL`
* deploy/nginx-default-conf change `server_name` to your server's hostname
* settings.py `SECRET_KEY` and `DATABASES`
* .env `SERVER_HOSTNAME`
* Make sure you update the Informed Consent text in templates/index.html in the `informedconsent` section!


## Local Installation (Mac OSX Instructions)

* Install MySQL, and good luck. My recommendation is to install [homebrew](https://docs.brew.sh/Installation) run `brew install mysql-connector-c; brew unlink mysql-connector-c; brew install mysql`.
* Check if you have Python 3.6 (`which python3.6`). If you don't have it, [download it](https://www.python.org/downloads/release/python-367/).
* Create the logging directory the Django project will use. `sudo mkdir /var/log/django/`. Then make sure you can read/write in it `sudo chmod 777 /var/log/django/`.
* Check out the project from Github.
* `cd` into project the directory, and create a virtual environment. `virtualenv -p python3.6 env`
* If you haven't already, install [Autoenv](https://github.com/kennethreitz/autoenv#install).
* In a new terminal, `cd` into the directory again to make sure autoenv picks up the virtual environment. It'll ask if you want to run the .env script. Say Yes.
* Run `pip install -r requirements.txt`
* Run `fab -f deploy/fabric/deploy.py configure_local_db` to set up your database locally.
* Run `python manage.py migrate` to set up all the Django model tables.

## Running the server locally

* If you have autoenv, just `cd` into the project's directory and run `runserver` then access the server at http://localhost:8000/. If you don't, you must make sure you're in the proper python environment (`source env/bin/activate`) and use the command `python manage.py runserver 0.0.0.0:8000` which is the equivalent.

## Setting Up Automated Deployment Scripts for Google Cloud

We provide deployment and server configuration scripts to make your lives much easier, but they assume you are running Debian 9. They involve connecting to your server via command line, which is a little tricky in Google Cloud. Here's how to configure your local machine to be able to do that.

* Download the [Google Cloud SDK](https://cloud.google.com/sdk/docs/).
* Unzip the file somewhere permanent, like /opt/. `cd` to the directory, then run `./google-cloud-sdk/install.sh`
* Close your terminal tab and open a new one, to load the changes.
* In the new tab run `gcloud auth login` and authorize it with the correct account.
* Set the project with `gcloud config set project [[ PROJECT NAME ]]`
* Run `gcloud compute config-ssh --ssh-key-file=~/.ssh/google`
* Now convert the keyfile to RSA so Fabric can use it. `ssh-keygen -p -m PEM -f ~/.ssh/google`
* Again, close the terminal and open a new one to read the changes.
* Now you can SSH into the Virtual Instance with the command `ssh [[ SERVER HOSTNAME ]]`!

## Setting Up Production Server

First, make sure you have the code checked in to your own Github project. The deploy scripts need a reference to that project so the server can download the code and install it. It will always download the code from the master branch, so make sure whatever's checked into master is ready to be sent to your server!

Also, make sure you have a server running somewhere that you have SSH access for and have sudo privileges. You can't deploy code to a server without a server running!

And finally.... Don't skip any of these steps!

#### Deploying a Chatbots project

As mentioned above, this project is intended to import code from a separate, pre-existing Chatbots project.
Use our [**Neural Chat**](https://github.com/natashamjaques/neural_chat) open-source project for a range of neural dialog models. 

If you would like to create your own chatbot models, now is the time to make one. Here's how to create one yourself:

* Create a new Github project. Copy dialog/chatbots.py to that project, and rename it web_chatbots.py. Edit it to remove all references to Django and settings. You can make any number of chatbots, so long as they implement the `Chatbot` class and use the `@registerbot()` decorator. They will all automatically be picked up by the Django project!
* Create a virtual environment with Python 3.6. We recommend placing it in /opt/virtualenvironment/. Basically, run this command: `cd /opt/; virtualenv -p python3.6 virtualenvironment`
* We recommend adding a copy of dialog/chatbottest.py to your Chatbots project to test and run your chatbots on the command line.
* SSH into your server and check out your chatbots project. Activate your virtual environment, install all requirements, and run chatbottest.py to make sure it's working.

#### Configuring the Django project to talk to the Chatbots project

Now that you have your chatbots running on your server, it's time to update the code in this project to be able to locate that project and its virtual environment on your server.

* Make sure `VIRTUAL_ENVIRONMENT` in deploy/fabric/deploy.py points to the virtual environment set up for your chatbots.
* Make sure `virtualenv` in deploy/fabric/vassals/django.ini points to the same directory
* Make sure `ExecStart` in deploy/fabric/uwsgi-systemd points to the same directory
* Make sure the second `pythonpath` in deploy/fabric/vassals/django.ini points to the directory your chatbots project is in.
* Be sure to check in and push all your configuration changes!

#### Generating Github Deploy Keys

You will need to make sure the scripts can access your Github project. So we must generate keys. These keys will be automatically ignored by git, so they must be manually sent between team members once generated.

* In the project directory, run `fab deploy/fabric/deploy.py create_ssh_key`. You should see two new files in the deploy/fabric/keys directory.
* Go to your Github project's page, and go to Settings -> Deploy Keys -> Add New. Paste the contents of the public key file (deploy/fabric/keys/github.pub) into the box, and give the key a name (it doesn't matter what you call it).
* Now your server will be able to check out your code from Github!

#### Running the server setup scripts

* In the main directory of your project, run `fab -f deploy/fabric/deploy.py -H [[SERVER HOSTNAME]] setup_server`. During this process, you will be prompted by [Certbot](https://certbot.eff.org/) on configuration options. Generally, just choose the default options, or look up terms on the Certbot page. If everything was configured correctly, your server should now be running!
* Run `fab -f deploy/fabric/deploy.py -H [[SERVER HOSTNAME]] create_superuser` to create an account in your Django Admin Console. You can now access your admin console by going to https://[[SERVER HOSTNAME]]/admin/ and logging in with the account you just created.

## Deploying Code Changes to the Server

After the server has been successfully set up, it's simple to update it with any subsequent code changes.

* Make sure you have all changes and files checked into your project's master branch!
* With autoenv, simply `cd` into the project's base directory and run `deploy`. The server will check out the code from the master branch of your github project, run any necessary database migrations, and restart the server for you.

## Editing LESS Files

We highly recommend using [PyCharm](https://www.jetbrains.com/pycharm/) for this project (especially the free educational edition). Located in the /static/ directory is a file, style.css. It is automatically generated from style.less by PyCharm every time style.less is edited. So we highly recommend using an IDE where you can continue editing the .less file and never manually editing the .css file.


## Setting up Studies and Exporting Your Data

When you register a chatbot with the `@registerchatbot()` decorator, it will automatically be included on the index page of the site. But you can also set up specific studies to run with a subset of your bots with specific configurations!

To set up a study, log in to your Django Admin Console (located at https://[[ SERVER HOSTNAME ]]/admin/). Then create a new Study object. When you create a new Study, you can give it a couple options. Basically, give it a human readable name and select which bots you want included. Additionally, you can choose to flag the study as being random. If you do, the participants will be shown one random and anonymized bot. Otherwise, the participants will get to choose which bot they want to chat with out of a list. You can also flag the study as being a Mechanical Turk study, in which case the participant will be asked for their Mechanical Turk ID and will be given a code at the end of their chat session they can paste into their Turk page, to help match which Turk Worker had which conversations.

Once you've configured and saved up your studies, you can see a link to each one right there in the Admin Console. Just click the link to see what your participants will see!

After people have used your chatbots, you can download their conversations and ratings by going to /admin/dialog/chatrating/ and /admin/dialog/chatrecord/ and clicking the "DOWNLOAD ALL AS CSV" link in the upper right corner.

You can also download the data for a specific study by navigating to that study in the admin and clicking the "DOWNLOAD AS CSV" buttons in the upper right of the screen.

## Licence

The MIT License

Copyright (c) 2019 Craig Ferguson, Natasha Jaques, Asma Ghandeharioun, Judy Shen, Noah Jones, Agata Lapedriza, Rosalind Picard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

## Reference
If you use this code, please reference the following paper:

```
@article{ghandeharioun2019approximating,
  title={Approximating Interactive Human Evaluation with Self-Play for Open-Domain Dialog Systems},
  author={Ghandeharioun, Asma and Shen, Judy and Jaques, Natasha and Ferguson, Craig and Jones, Noah, and Lapedriza, Agata and Picard, Rosalind},
  journal={arXiv preprint arXiv:},
  year={2019}
}
```