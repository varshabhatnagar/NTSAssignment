# NTSAssignment

Python script to perform the following AWS tasks:
1. Read resource configuration data frm a JSON file ResourceConfig.json
2. Create a new Key Pair
3. Create an Application Load Balancer alongwith Target Group and a listener receiving HTTP traffic at port 80
4. Create Launch Configuration using Amazon Linux 2 AMI and userdata file to bootstrap docker installation and run apache container on port 8080 at instance launch
5. Create AutoScaling Group with desired capacity as 2 ec2 instances
6. Register the AutoScaled EC2 instances as Targets under the newly created TargetGroup
7. Upon script execution, Apache webpage can be accessed using the LoadBalancer DNS name
