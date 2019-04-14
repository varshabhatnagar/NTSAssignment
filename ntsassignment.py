# Python script to perform the following AWS tasks:
# 1. Read resource configuration data frm a JSON file ResourceConfig.json
# 2. Create a new Key Pair
# 3. Create an Application Load Balancer alongwith Target Group and a listener receiving HTTP traffic at port 80
# 4. Create LAunch Configuration using Amazon Linux 2 AMI and userdata file to bootstrap docker installation and run apache container on port 8080 at instance launch
# 5. Create AutoScaling Group with desired capacity as 2 ec2 instances
# 6. Register the AutoScaled EC2 instances as Targets under the newly created TargetGroup
# 7. Upon script execution, Apache webpage can be accessed using the LoadBalancer DNS name

import boto3
import pyboto3
import time
import json

############################################################################
# Reading resource related configuration from JSON file
############################################################################
resourceData = {}
with open('D:\\Varsha\\NTS\\ResourceConfig.json') as json_file:  
    resourceData = json.load(json_file)

subnets = resourceData['subnet']
VpcId = resourceData['VpcId']

KeypairData = resourceData['KeyPair']
KeyPair_Name = KeypairData.get('Name')

LoadBalancerData = resourceData['LoadBalancer']
LoadBalancer_Name =  LoadBalancerData.get('Name')
LoadBalancer_Type =  LoadBalancerData.get('Type')
LoadBalancer_TargetGroupData = LoadBalancerData.get('TargerGroup')
LoadBalancer_TargetGroup_Name = LoadBalancer_TargetGroupData.get('Name')
LoadBalancer_TargetGroup_Port = LoadBalancer_TargetGroupData.get('Port')
LoadBalancer_TargetGroup_Protocol = LoadBalancer_TargetGroupData.get('Protocol')
LoadBalancer_TargetGroup_HealthCheckProtocol = LoadBalancer_TargetGroupData.get('HealthCheckProtocol')
LoadBalancer_TargetGroup_HealthCheckPath = LoadBalancer_TargetGroupData.get('HealthCheckPath')
LoadBalancer_TargetGroup_HealthCheckIntervalSeconds = LoadBalancer_TargetGroupData.get('HealthCheckIntervalSeconds')
LoadBalancer_TargetGroup_HealthCheckTimeoutSeconds = LoadBalancer_TargetGroupData.get('HealthCheckTimeoutSeconds')
LoadBalancer_TargetGroup_HealthyThresholdCount = LoadBalancer_TargetGroupData.get('HealthyThresholdCount')
LoadBalancer_TargetGroup_UnhealthyThresholdCount = LoadBalancer_TargetGroupData.get('UnhealthyThresholdCount')
LoadBalancer_ListenerData = LoadBalancerData.get('Listener')
LoadBalancer_Listener_Protocol = LoadBalancer_ListenerData.get('Protocol')
LoadBalancer_Listener_Port = LoadBalancer_ListenerData.get('Port')

AutoScalingData = resourceData['AutoScaling']
AutoScaling_Name =  AutoScalingData.get('Name')
AutoScaling_MinSize =  AutoScalingData.get('MinSize')
AutoScaling_MaxSize =  AutoScalingData.get('MaxSize')
AutoScaling_DesiredCapacity =  AutoScalingData.get('DesiredCapacity')
AutoScaling_HealthCheckGracePeriod =  AutoScalingData.get('HealthCheckGracePeriod')
AutoScaling_HealthCheckType =  AutoScalingData.get('HealthCheckType')
AutoScaling_LaunchConfigurationData =  AutoScalingData.get('LaunchConfiguration')
AutoScaling_LaunchConfiguration_Name =  AutoScaling_LaunchConfigurationData.get('Name')
AutoScaling_LaunchConfiguration_ImageId =  AutoScaling_LaunchConfigurationData.get('ImageId')
AutoScaling_LaunchConfiguration_InstanceType =  AutoScaling_LaunchConfigurationData.get('InstanceType')

############################################################################################################## Client configuration and creation of a new Key Pair
#############################################################################################################
ec2_client = boto3.client('ec2')
ec2 = boto3.resource('ec2')
elb = boto3.client('elbv2')
autoscaling = boto3.client('autoscaling')

print("Please wait...")
print("Resource creation in progress...")
ec2keypair_response = ec2_client.create_key_pair(
    KeyName = KeyPair_Name,
    )
with open('D:\\Automation\\OCI\\KeyPair_Name', 'w') as f:
	print(ec2keypair_response, file=f)

############################################################################################################## Creation of Load Balancer alongwith Target Group and Listener
#############################################################################################################

subnet = subnets

elb_response = elb.create_load_balancer(
    Name=LoadBalancer_Name,
    Subnets=subnet,
    Type=LoadBalancer_Type,
    IpAddressType='ipv4')

alb_list = elb_response['LoadBalancers']
lbarn = ''
lbdns = ''
for alb in alb_list:
    lbarn = alb.get("LoadBalancerArn")
    lbdns = alb.get("DNSName")


targetgroup_response = elb.create_target_group(
    Name=LoadBalancer_TargetGroup_Name,
    Port=LoadBalancer_TargetGroup_Port,
    Protocol=LoadBalancer_TargetGroup_Protocol,
    VpcId=VpcId,
    HealthCheckProtocol=LoadBalancer_TargetGroup_HealthCheckProtocol,
    HealthCheckEnabled=True,
    HealthCheckPath=LoadBalancer_TargetGroup_HealthCheckPath,
    HealthCheckIntervalSeconds=LoadBalancer_TargetGroup_HealthCheckIntervalSeconds,
    HealthCheckTimeoutSeconds=LoadBalancer_TargetGroup_HealthCheckTimeoutSeconds,
    HealthyThresholdCount=LoadBalancer_TargetGroup_HealthyThresholdCount,
    UnhealthyThresholdCount=LoadBalancer_TargetGroup_UnhealthyThresholdCount,
    TargetType='instance'
)


tg_list = targetgroup_response['TargetGroups']
for tg in tg_list:
    tgarn = tg.get("TargetGroupArn")


listener_response = elb.create_listener(
    LoadBalancerArn=lbarn,
    Protocol=LoadBalancer_Listener_Protocol,
    Port=LoadBalancer_Listener_Port,
    DefaultActions=[
        {
            'Type': 'forward',
            'TargetGroupArn': tgarn,
       }
    ]
)    

############################################################################################################## Creation of Launch Configuratiom and AutoScaling Group. LaunchConfiguration makes use of userdata file to install Docker and place Apache containers on EC2 instances that server webcontent on the specified port
#############################################################################################################

launchconfig_response = autoscaling.create_launch_configuration(
    LaunchConfigurationName=AutoScaling_LaunchConfiguration_Name,
    ImageId=AutoScaling_LaunchConfiguration_ImageId,
    KeyName=KeyPair_Name,
    UserData=open("D:\\Automation\\OCI\\userdata.txt").read(),
    InstanceType=AutoScaling_LaunchConfiguration_InstanceType,
    AssociatePublicIpAddress=True)

ASGSubnets = subnet[0]+ ',' +subnet[1]
autoscalinggrp_response = autoscaling.create_auto_scaling_group(
    AutoScalingGroupName=AutoScaling_Name,
    LaunchConfigurationName=AutoScaling_LaunchConfiguration_Name,
    MinSize=AutoScaling_MinSize,
    MaxSize=AutoScaling_MaxSize,
    DesiredCapacity=AutoScaling_DesiredCapacity,
    DefaultCooldown=120,
    HealthCheckGracePeriod=AutoScaling_HealthCheckGracePeriod,
    TargetGroupARNs=[
        tgarn,
    ],
    VPCZoneIdentifier=ASGSubnets,
    HealthCheckType=AutoScaling_HealthCheckType,
    )


############################################################################################################## Capturing Instance ID in AutoScaling Group to register them as Targets inside the Target Group for the Load Balancer
#############################################################################################################
time.sleep(10)
instance_list = []
autosclg_capture= autoscaling.describe_auto_scaling_groups(
    AutoScalingGroupNames=[
        AutoScaling_Name,
    ]
)

for a in autosclg_capture['AutoScalingGroups']:
    inst = a.get("Instances")
    for ins in inst:
        instance_list.append(ins.get("InstanceId"))


wt = ec2_client.get_waiter('instance_running')
wt.wait(InstanceIds=instance_list)

############################################################################################################## Registering Autoscaled EC2 instances as Targets
#############################################################################################################
registertarget_response = elb.register_targets(
    TargetGroupArn=tgarn,
    Targets=[
        {
            'Id': instance_list[0],
            'Port': LoadBalancer_TargetGroup_Port,
        },
        {
            'Id': instance_list[1],
            'Port': LoadBalancer_TargetGroup_Port,
        },
    ]
)   

print("Starting resource check...")
wt = ec2_client.get_waiter('instance_status_ok')
wt.wait(InstanceIds=instance_list)
print("Resource check complete! Status OK")

############################################################################################################## Web content accessible using the Load Balancer DNS name
#############################################################################################################
print("Execution completed successfully!")
print("Access the webpage at Load Balancer DNS name: %s" % (lbdns))


