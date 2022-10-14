import logging
import random as rand
import subprocess
import sys
import webbrowser

import boto3
import requests

# EC2 Instance Variables
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

# S3 Bucket variables
s3 = boto3.resource('s3')
s3_client = boto3.client("s3")
s3Url = ""

# SNS Variables
sns_client = boto3.client("sns")

# Key name
keyName = "Adamskey"
# Bucket name is blank by default
bucket_name = ""

# Instance Ip List
instance_ips = []
instance_ids = []
instance_list = []
bucket_list = []


# Setting up log file

logging.basicConfig(
    filename='data.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'),
logging.info("Program Started!")


# ============= Utilities ============= #

def validateInput(choice, min, max):
    if choice in range(min, max):
        return True
    else:
        return False


def generateRandomString():
    global randString  # 97 in ASSCI is a + 26 letters in the alphabet
    randString = str(rand.randint(0, 9)) + str(chr(rand.randrange(97, 97 + 26))) + \
                 str(rand.randint(0, 9)) + str(chr(rand.randrange(97, 97 + 26))) + \
                 str(rand.randint(0, 9)) + str(chr(rand.randrange(97, 97 + 26)))


def downloadIMG():
    link = "http://devops.witdemo.net/logo.jpg"
    response = requests.get(link)

    file = open("logo.jpg", "wb")
    file.write(response.content)
    file.close()

    logging.info("Image has been downloaded from " + link)


# ============= Startup ============= #

# This UI is disabled on submission because
# the goal is for it to be an automated process
# it was made only for MY convince

def mainMenu():
    print("Amazon Automation")
    print("1) Launch instance")
    print("2) Launch bucket")
    print("3) Launch bucket and instance")
    print("4) Terminate all instances and buckets")
    print("5) Exit")

    option = int(input("---->"))

    while not validateInput(option, 1, 10):
        option = int(input("---->"))
    if option == 1:
        create_instances()
    if option == 2:
        create_bucket()
    if option == 3:
        create_instances()
        f = open("aobrienurls.txt", "a")
        f.write("\n")
        f.close()
        create_bucket()
        f = open("aobrienurls.txt", "a")
        f.write(s3Url)
        f.close()
    if option == 4:
        terminate_instances()
        logging.info("All Instances have been terminated")
        manage_buckets()
        logging.info("All data from buckets has been erased")
        delete_buckets()
        logging.info("All buckets have been deleted")
        mainMenu()
    if option == 5:
        exit()
    if option > 4:
        print("Please enter a valid option")
        mainMenu()


# ============= EC2 Instance Methods ============= #


# print the instances

def listInstances():
    print(instance_list)


# Function that creates the instance using the security group and key
def create_instances():
    manage_instances()
    try:
        instances = ec2.create_instances(

            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'adamsec2Instance1.2'
                        },
                    ]
                },
            ],

            ImageId='ami-026b57f3c383c2eec',
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.nano',
            UserData="""#!/bin/bash
                 sudo yum install httpd -y
                 systemctl enable httpd
                 systemctl start httpd
                 
                 echo "<?php echo '<p>Hello World</p>'; ?>" >> test.php
                 
                 echo '<html>' > index.html
                 
                 echo 'Private IP address: ' >> index.html
                 curl http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html 
                 
                 echo '<br>' >> index.html
                 
                 echo " Public IP address" >> index.html
                 curl http://169.254.169.254/latest/meta-data/public-ipv4 >> index.html 
                 
                 cp index.html /var/www/html/index.html

            """,
            SecurityGroupIds=['sg-0f0b4ae866f08b674'],
            KeyName="Adamskey"

        )
        print("Waiting for instance...")

        instances[0].wait_until_running()
        instances[0].reload()

        print("Instance is now running")

        logging.info("Instance Created")
        logging.info("Instance " + instance_list[-1].public_ip_address + " is now running")
        sns_client.publish(PhoneNumber="+353858275412",
                           Message="AWS Instance " + instance_list[-1].public_ip_address + " is now Running")

        instance_ip = instances[-1].public_ip_address
        f = open("aobrienurls.txt", "a")
        f.write("http://"+instance_ip)
        f.close()

    except:
        print("Except")

    else:
        if instance_list[-1].state != 'running':
            print("Instance Failed")
            logging.error("Instance has failed to be created")


# Function to list all instances
def manage_instances():
    try:
        global instance_list
        instance_list.clear()
        for inst in ec2.instances.all():
            instance_list.append(inst)
            instance_ids.append(instance_list[-1].id)
            print(inst.id, inst.state, inst.public_ip_address)
    except:
        print("Instances cannot be listed - No instances exist")


# ============= S3 Bucket Methods ============= #


def manage_buckets():
    global bucket_list

    bucket_list.clear()
    for bucket in s3.buckets.all():
        bucket_list.append(bucket)


        # print(bucket.id, bucket.state, bucket.public_ip_address)


# print the buckets
def listBuckets():
    print(bucket_list)


randString = ""


def randomBucketName():
    generateRandomString()
    global bucket_name
    bucket_name = "aobrien" + randString
    print(bucket_name)





# Creates the s3 bucket, and waits until it is running
def create_bucket():
    global bucket_name
    global s3Url
    randomBucketName()
    downloadIMG()
    try:
        response = s3.create_bucket(Bucket=bucket_name, ACL='public-read')
        # ,CreateBucketConfiguration={'LocationConstraint': 'us-east-1'})
        response.wait_until_exists()
        print(response)
        logging.info(bucket_name + " Bucket has been created")
        print("bucket has been created")

        # TODO
        put_bucket('index.html')
        put_bucket('logo.jpg')
        launchWebsite()

        sns_client.publish(PhoneNumber="+353858275412",
                           Message="Your S3 Bucket Website is now running view it here " + s3Url)
        print("Text message Sent")


    except Exception as error:
        print(error)


# put files into bucket e.g. index.html

# TODO source of double text message
def put_bucket(object_name):
    global bucket_name
    global s3Url

    s3 = boto3.resource("s3")


    try:
        response = s3.Object(bucket_name,
                             object_name).put(Body=open(object_name, 'rb'), ACL='public-read', ContentType="text/html")
        print(response)
        logging.info("The " + str(object_name) + " file has been added to the s3 bucket")
        s3Url = "http://" + bucket_name + ".s3-website-us-east-1.amazonaws.com/"
    except Exception as error:
        print(error)


# Launches the s3 bucket as a website
def launchWebsite():
    global bucket_name
    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }
    bucket_website = s3.BucketWebsite(bucket_name)

    response = bucket_website.put(WebsiteConfiguration=website_configuration)
    print("Response\n")
    print(response)
    logging.info("Website has been Launched")
    webbrowser.open_new_tab(response)

# https://stackoverflow.com/questions/48649523/using-boto-to-delete-all-buckets
def delete_buckets():
    bucketsList = s3_client.list_buckets()

    for bucket in bucketsList['Buckets']:
        s3_bucket = s3.Bucket(bucket['Name'])
        s3_bucket.objects.all().delete()
        s3_bucket.delete()


def terminate_instances():
    manage_instances()
    for instance_id in instance_ids:
        instance = ec2.Instance(instance_id)
        response = instance.terminate()
        print(response)


mainMenu()

subprocess.run('ls')
subprocess.run('./monitor.sh')

# ============= End of Program ============= #
