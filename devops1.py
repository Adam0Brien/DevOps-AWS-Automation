# Dev Ops 1 Assignment - Adam O'Brien - 20093460

import logging
import random as rand
import subprocess
import webbrowser
import time
from datetime import datetime, timedelta
import boto3
import requests

# EC2 Instance Variables
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')

# S3 Bucket variables
s3 = boto3.resource('s3')
s3_client = boto3.client("s3")
s3Url = ""

# Create CloudWatch client/resource
cloudwatch = boto3.resource('cloudwatch')
cloudwatch_client = boto3.client('cloudwatch')

# SNS client for text notifications
sns_client = boto3.client("sns")

keyName = "newKey"
# Bucket name is blank by default
bucket_name = ""
# this string will hold 3 random chars and 3 random ints
randString = ""

# Instance Ip List
instance_ids = []
instance_list = []
instances = []

# Setting up log file

logging.basicConfig(filename='data.log',format='%(asctime)s %(levelname)-8s %(message)s',level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')

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

# TUI was made for my own convinence for managing instances

def mainMenu():
    try:
        print("AWS Automation")
        print("1) Launch instance")
        print("2) Launch bucket")
        print("3) Launch bucket and instance")
        print("4) List Instances")
        print("5) Terminate all instances and buckets")
        print("6) Exit")
       
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
            list_instances()
        if option == 5:
            terminate_instances()
            logging.info("All Instances have been terminated")
            delete_buckets()
            logging.info("All buckets have been deleted")
        if option == 6:
            exit()
        if option > 7:
            print("Please enter a valid option")
            mainMenu()
    except Exception as e:
        print(e)


# ============= EC2 Instance Methods ============= #


# Function that creates the instance using the security group and key
def create_instances():
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
            # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html
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
            KeyName="newKey"

        )
        print("Waiting for instance...")

        instances[0].wait_until_running()
        print("Done waiting")
        time.sleep(10)
        instances[0].reload()

        print("Instance is now running:" + str((instances[0].public_ip_address))
        logging.info("Instance " + instances[0].public_ip_address + "  has been created and is now running")


    except Exception as e:
        print("Instance Failed")
        print(e)
        logging.error("Instance has failed to be created")


# Function to list all instances
def list_instances():
    try:
        global instance_list
        instance_list.clear()
        for inst in ec2.instances.all():
            instance_list.append(inst)
            instance_ids.append(instance_list[-1].id)
            print(inst.id, inst.state, inst.public_ip_address)

    except Exception as e:
        print(e)
        print("Instances cannot be listed - No instances exist")


# ============= S3 Bucket Methods ============= #


def manage_buckets():
    try:
        for bucket in s3.buckets.all():
            print(bucket.id, bucket.state, bucket.public_ip_address)
    except Exception as e:
        print(e)


def randomBucketName():
    try:
        generateRandomString()
        global bucket_name
        bucket_name = "aobrien" + randString
        print(bucket_name)
    except Exception as e:
        print(e)


# Creates the s3 bucket, and waits until it is running
def create_bucket():
    global bucket_name
    global s3Url
    try:
        randomBucketName()
        downloadIMG()
        
        # Ensure no two buckets have the same name
        if not s3.Bucket(bucket_name) in s3.buckets.all():
            response = s3.create_bucket(Bucket=bucket_name, ACL='public-read')
            response.wait_until_exists()
            logging.info(bucket_name + " Bucket has been created")
            print("Bucket has been created")

            upload_object_to_bucket('index.html')
            upload_object_to_bucket('logo.jpg')
            launch_website()

            # Send a text message (Costs extra AWS credit)
            # sns_client.publish(PhoneNumber="", Message="Your S3 Bucket Website is now running view it here " + s3Url)
            # print("Text message Sent")
        else:
            create_bucket() # Call the function again if the bucket name exists
    except Exception as e:
        print(e)


# Upload files into bucket by object_name e.g.index.html
def upload_object_to_bucket(object_name):
    global bucket_name
    global s3Url
    try:
        s3.Object(bucket_name, object_name).put(Body=open(object_name, 'rb'), ACL='public-read',
                                                ContentType="text/html")
        logging.info("The " + str(object_name) + " file has been added to the s3 bucket")
        s3Url = "http://" + bucket_name + ".s3-website-us-east-1.amazonaws.com/"
        print(object_name + " has been added to your s3 bucket")
    except Exception as e:
        print(e)
        print("Exception")


# Launches the s3 bucket as a website
def launch_website():
    global bucket_name
    try:
        website_configuration = {
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'},
        }
        bucket_website = s3.BucketWebsite(bucket_name)

        response = bucket_website.put(WebsiteConfiguration=website_configuration)
        
        logging.info("Website has been Launched")
        webbrowser.open_new_tab(response)
        print("S3 Website has been launched")
    except Exception as e:
        print(e)



# Delete all buckets Ref:(https://stackoverflow.com/questions/48649523/using-boto-to-delete-all-buckets)
def delete_buckets():
    try:
        bucketsList = s3_client.list_buckets()
        for bucket in bucketsList['Buckets']:
            s3_bucket = s3.Bucket(bucket['Name'])
            s3_bucket.objects.all().delete()
            s3_bucket.delete()
    except Exception as e:
        print(e)

# Terminate all instances
def terminate_instances():
    try:
        list_instances()
        for instance_id in instance_ids:
            instance = ec2.Instance(instance_id)
            response = instance.terminate()
            print(response)
    except Exception as e:
        print(e)


def runMonitorScript():
    try:
        
        global instances
        
        print(instances[0].public_ip_address)
        time.sleep(10)
        subprocess.run("chmod 400 newKey.pem", shell=True)
        subprocess.run("scp -i newKey.pem monitor.sh ec2-user@" + str(instances[0].public_ip_address) + ":.",
                       shell=True)
        print("scp check")
        subprocess.run("ssh -i newKey.pem ec2-user@" + str(instances[0].public_ip_address) + " 'chmod 700 monitor.sh'",
                       shell=True)
        print("ssh check")
        subprocess.run("ssh -i newKey.pem  ec2-user@" + str(instances[0].public_ip_address) + " ' ./monitor.sh'",
                       shell=True)
    except Exception as e:
        print(e)


def cloudWatch():
    try:
        instid = instances[0].id
        
        # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-using-alarms.html
        # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/cw-example-creating-alarms.html
        # https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_PutMetricAlarm.html


        # check cloudwatch on aws
        cloudwatch_client.put_metric_alarm(
            AlarmName='Web Server CPU_Utilization, 70% Cap',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Period=60,
            Statistic='Average',
            Threshold=70.0,
            ActionsEnabled=True,
            AlarmActions=[
                'arn:aws:automate:us-east-1:ec2:reboot'
                # When instance CPU Utilization exceeds 70% the ec2 instance will reboot itself
            ],
            AlarmDescription='Alarm when server CPU exceeds 70%',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instid
                },
            ],
            Unit='Seconds'
        )

        # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/viewing_metrics_with_cloudwatch.html

        instance = ec2.Instance(instid)
        instance.monitor()  # Enables detailed monitoring on instance (1-minute intervals)
        time.sleep(180)  # Wait 3 minutes to ensure we have some data (can remove if not a new instance)

        CPU_metric_iterator = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                                        MetricName='CPUUtilization',
                                                        Dimensions=[{'Name': 'InstanceId', 'Value': instid}])

        DISK_metric_iterator = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                                         MetricName='DiskReadBytes',
                                                         Dimensions=[{'Name': 'InstanceId', 'Value': instid}])

        NETWORKIN_metric_iterator = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                                              MetricName='NetworkIn',
                                                              Dimensions=[{'Name': 'InstanceId', 'Value': instid}])

        CPU_Metric = list(CPU_metric_iterator)[0]  # extract first (only) element

        DISK_Metric = list(DISK_metric_iterator)[0]  # extract first (only) element

        NETWORKIN_Metric = list(NETWORKIN_metric_iterator)[0]

        CPU_response = CPU_Metric.get_statistics(StartTime=datetime.utcnow() - timedelta(minutes=5),  # 5 minutes ago
                                                 EndTime=datetime.utcnow(),  # now
                                                 Period=300,  # 5 min intervals
                                                 Statistics=['Average'])

        DISK_response = DISK_Metric.get_statistics(StartTime=datetime.utcnow() - timedelta(minutes=5),  # 5 minutes ago
                                                   EndTime=datetime.utcnow(),  # now
                                                   Period=300,  # 5 min intervals
                                                   Statistics=['Sum'])

        NETWORKIN_response = NETWORKIN_Metric.get_statistics(StartTime=datetime.utcnow() - timedelta(minutes=5),
                                                             # 5 minutes ago
                                                             EndTime=datetime.utcnow(),  # now
                                                             Period=300,  # 5 min intervals
                                                             Statistics=['Sum'])

        cpuUtils = "Average CPU utilisation:", CPU_response['Datapoints'][0]['Average'],CPU_response['Datapoints'][0]['Unit']

        diskReadBytes = "Bytes read from all instance store volumes available to the instance:",DISK_response['Datapoints'][0]['Sum']

        network_in = "The number of bytes received by the instance on all network interfaces",NETWORKIN_response['Datapoints'][0]['Sum'], NETWORKIN_response['Datapoints'][0]['Unit']


        logging.info(cpuUtils)
        logging.info(diskReadBytes)
        logging.info(network_in)
        print(cpuUtils)
        print(diskReadBytes)
        print(network_in)

    except Exception as e:
        print(e)


#mainMenu()
automation_demo()


def automation_demo():
    create_instances()
    create_bucket()
    f = open("aobrienurls.txt", "a")
    f.write("http://" + instances[0].public_ip_address)
    f.write("\n")
    f.write(s3Url)
    f.close()
    time.sleep(10)
    runMonitorScript()
    print("\n\n")
    print("Running Cloudwatch")
    cloudWatch()

# ============= End of Program ============= #






