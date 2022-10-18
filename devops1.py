# Dev Ops 1 Assignment - Adam O'Brien - 20093460

import logging
import random as rand
import subprocess
import webbrowser
import time

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
# this string will hold 3 random chars and 3 random ints
randString = ""

# Instance Ip List
instance_ips = []
instance_ids = []  # dont touch
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
    try:
        print("Amazon Automation")
        print("1) Launch instance")
        print("2) Launch bucket")
        print("3) Launch bucket and instance")
        print("4) Terminate all instances and buckets")
        print("5) Exit")
        print("6) List Instances")

        option = int(input("---->"))

        while not validateInput(option, 1, 10):
            option = int(input("---->"))
        if option == 1:
            create_instances()
            mainMenu()
        if option == 2:
            create_bucket()
            mainMenu()
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
        if option == 6:
            manage_instances()
        if option > 7:
            print("Please enter a valid option")
            mainMenu()
    except Exception as e:
        print(e)


# ============= EC2 Instance Methods ============= #


# print the instances

def listInstances():
    print(instance_list)


instances = []


# Function that creates the instance using the security group and key
def create_instances():
    global instance_ips
    global instances
    global instance_list
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
            #https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html
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
                 
                 echo '<br>' >> index.html
                  
                 echo " Instance Type " >> index.html
                 curl http://169.254.169.254/latest/meta-data/instance-type >> index.html
                
                 echo '<br>' >> index.html
                 
                 echo " Availability Zone " >> index.html
                 curl http://169.254.169.254/latest/meta-data/placement/availability-zone >> index.html
                 
                 echo '<br>' >> index.html
                  
                 echo " Instance AMI " >> index.html
                 curl http://169.254.169.254/latest/meta-data/ami-id >> index.html
                 
                 echo '<br>' >> index.html
                 
                 echo " Security Group " >> index.html
                 curl http://169.254.169.254/latest/meta-data/security-groups >> index.html    

                 cp index.html /var/www/html/index.html

            """,
            SecurityGroupIds=['sg-0f0b4ae866f08b674'],
            KeyName="Adamskey"

        )
        print("Waiting for instance...")

        instances[0].wait_until_running()
        print("Done waiting")
        time.sleep(10)
        instances[0].reload()

        print("Instance is now running")

        logging.info("Instance Created")
        logging.info("Instance " + instances[0].public_ip_address + " is now running")
        # sns_client.publish(PhoneNumber="+353858275412",
        #                 Message="AWS Instance " + instance_list[
        #                     0].public_ip_address + " is now Running" + " http://" + instance_list[
        #                            0].public_ip_address)

        print(instances[0].public_ip_address)
        f = open("aobrienurls.txt", "a")
        f.write("http://" + instances[0].public_ip_address)
        f.close()
        # print(instances[0].public_ip_address)
        #manage_instances()
        



    except Exception as e:

        print("Instance Failed")
        print(e)
        logging.error("Instance has failed to be created")


# Function to list all instances
def manage_instances():
    try:
        global instance_list
        instance_list.clear()
        for inst in ec2.instances.all():
            instance_list.append(inst)
            instance_ids.append(instance_list[-1].id)
            instance_ips.append(instance_list[-1].public_ip_address)
            print(inst.id, inst.state, inst.public_ip_address)

    except Exception as e:
        print(e)
        print("Instances cannot be listed - No instances exist")


# ============= S3 Bucket Methods ============= #


def manage_buckets():
    try:
        global bucket_list

        bucket_list.clear()
        for bucket in s3.buckets.all():
            bucket_list.append(bucket)
            print(bucket.id, bucket.state, bucket.public_ip_address)
    except Exception as e:
        print(e)


# print the buckets
def listBuckets():
    print(bucket_list)


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
    if not s3.Bucket(bucket_name) in s3.buckets.all():  # Makes sure that two buckets cant have the same name
        try:
            response = s3.create_bucket(Bucket=bucket_name, ACL='public-read')
            response.wait_until_exists()
            #print(response)
            logging.info(bucket_name + " Bucket has been created")
            print("bucket has been created")

            # I made the lab code into a function with one perameter so,
            # I can call whatever i need to upload to the bucket in this function
            put_bucket('index.html')
            put_bucket('logo.jpg')
            launchWebsite()

            # sns_client.publish(PhoneNumber="+353858275412",
            #                    Message="Your S3 Bucket Website is now running view it here " + s3Url)
            print("Text message Sent")

        except Exception as e:
            print(e)
    else:
        create_bucket()
        # if the first generated bucket name has the same name as a
        # pre-existing bucket then it will call the method until an
        # original bucket name is found


# put files into bucket e.g. index.html


def put_bucket(object_name):
    global bucket_name
    global s3Url
    try:
        response = s3.Object(bucket_name,
                             object_name).put(Body=open(object_name, 'rb'), ACL='public-read', ContentType="text/html")
        #print(response) #metadata
        logging.info("The " + str(object_name) + " file has been added to the s3 bucket")
        s3Url = "http://" + bucket_name + ".s3-website-us-east-1.amazonaws.com/"
        print(object_name + " has been added to your s3 bucket")
    except Exception as e:
        print(e)
        print("Exception")


# Launches the s3 bucket as a website
def launchWebsite():
    global bucket_name
    try:
        website_configuration = {
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'},
        }
        bucket_website = s3.BucketWebsite(bucket_name)

        response = bucket_website.put(WebsiteConfiguration=website_configuration)
        #print("Response\n")
        #print(response)

        logging.info("Website has been Launched")
        webbrowser.open_new_tab(response)  # works in website.py but does not work in wsl
        print("S3 Website has been launched")
    except Exception as e:
        print(e)


# https://stackoverflow.com/questions/48649523/using-boto-to-delete-all-buckets
def delete_buckets():
    try:
        bucketsList = s3_client.list_buckets()

        for bucket in bucketsList['Buckets']:
            s3_bucket = s3.Bucket(bucket['Name'])
            s3_bucket.objects.all().delete()
            s3_bucket.delete()
    except Exception as e:
        print(e)


def terminate_instances():
    try:
        manage_instances()
        for instance_id in instance_ids:
            instance = ec2.Instance(instance_id)

            response = instance.terminate()
            print(response)
    except Exception as e:
        print(e)


mainMenu()


#
# subprocess.run('ls')
# subprocess.run('./monitor.sh')

# OPTION 3 FROM UI
# UNCOMMENT FOR AUTOMATION
#
# create_instances()
# f = open("aobrienurls.txt", "a")
# f.write("\n")
# f.close()
# create_bucket()
# f = open("aobrienurls.txt", "a")
# f.write(s3Url)
# f.close()
#
# time.sleep(10)


def runMonitorScript():
    global instances
    print(instances[0].public_ip_address)
    scp_command = "scp -i Adamskey.pem monitor.sh ec2-user@" + str(instances[0].public_ip_address) + ":."
    ssh_command = "ssh -i Adamskey.pem ec2-user@" + str(instances[0].public_ip_address) + " 'chmod 700 monitor.sh' "

    subprocess.run(scp_command, shell=True)
    print("scp check")
    subprocess.run(ssh_command, shell=True)
    print("ssh check")
    subprocess.run("ssh -i Adamskey.pem  ec2-user@" + str(instances[0].public_ip_address) + " ' ./monitor.sh'",
                   shell=True)


runMonitorScript()
# ============= End of Program ============= #


import boto3
from datetime import datetime, timedelta
import time


def cloudWatch():
    cloudwatch = boto3.resource('cloudwatch')
    ec2 = boto3.resource('ec2')

    instid = instances[0].id  # Prompt the user to enter an Instance ID
    instance = ec2.Instance(instid)
    instance.monitor()  # Enables detailed monitoring on instance (1-minute intervals)
    time.sleep(360)  # Wait 6 minutes to ensure we have some data (can remove if not a new instance)

    metric_iterator = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                                MetricName='CPUUtilization',
                                                Dimensions=[{'Name': 'InstanceId', 'Value': instid}])

    metric = list(metric_iterator)[0]  # extract first (only) element

    response = metric.get_statistics(StartTime=datetime.utcnow() - timedelta(minutes=5),  # 5 minutes ago
                                     EndTime=datetime.utcnow(),  # now
                                     Period=300,  # 5 min intervals
                                     Statistics=['Average'])

    print("Average CPU utilisation:", response['Datapoints'][0]['Average'], response['Datapoints'][0]['Unit'])
    # print (response)   # for debugging only


cloudWatch()

