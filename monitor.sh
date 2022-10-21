#!/usr/bin/bash
#
# Some basic monitoring functionality; Tested on Amazon Linux 2
#
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
AVAILABILITY_ZONE=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
AMI_ID=$(curl -s http://169.254.169.254/latest/meta-data/ami-id)
SECURITY_GROUP=$(curl -s http://169.254.169.254/latest/meta-data/security-groups)
IPV4=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
MEMORYUSAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
PROCESSES=$(expr $(ps -A | grep -c .) - 1)
HTTPD_PROCESSES=$(ps -A | grep -c httpd)

echo "Instance ID: $INSTANCE_ID"
echo "Memory utilisation: $MEMORYUSAGE"
echo "No of processes: $PROCESSES"
echo "IPV4 Address: $IPV4"
echo "Instance Type: $INSTANCE_TYPE"
echo "AMI id: $AMI_ID"
echo "Availability Zone: $AVAILABILITY_ZONE"
echo "Security group: $SECURITY_GROUP"
if [ $HTTPD_PROCESSES -ge 1 ]
then
    echo "Web server is running"
else
    echo "Web server is NOT running"
fi



