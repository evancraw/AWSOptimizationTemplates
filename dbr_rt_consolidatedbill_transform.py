#!/usr/bin/python
import sys
import re
from datetime import date, datetime
from csv import reader	

# list of all EC2 instance types
instance_types = ['t2.large','m4.large','m4.10xlarge','m4.xlarge','m4.2xlarge','m4.4xlarge','ds2.xlarge','ds2.8xlarge','dw1.xlarge','dw1.8xlarge','dw2.large','dw2.8xlarge','m1.small', 't1.micro', 't2.micro','t2.small','t2.medium','m1.small','m1.medium', 'm1.large','m1.xlarge','m1.2xlarge','c1.medium', 'm3.medium','m3.large', 'm2.xlarge', 'm3.xlarge', 'm3.2xlarge','m3.4xlarge','m2.2xlarge', 'c1.xlarge', 'm2.4xlarge', 'cc1.4xlarge', 'cg1.4xlarge', 'hi1.4xlarge', 'hs1.8xlarge', 'cc2.8xlarge', 'cr1.8xlarge','c3.large','c3.xlarge','c3.2xlarge','c3.4xlarge','c3.8xlarge','c4.large','c4.xlarge','c4.2xlarge','c4.4xlarge','c4.8xlarge','r3.large','r3.xlarge','r3.2xlarge','r3.4xlarge','r3.8xlarge','g2.2xlarge','g2.8xlarge','i2.8xlarge','i2.4xlarge','i2.2xlarge','data transfer','provisioned storage','provisioned iops','IOPS-month','hours purchased','Sign up charge for subscription:','dynamodb.read','dynamodb.write', 'snapshot data']
# list all EC2 and RDS Operating Systems
OS_types = ['Linux', 'MySQL', 'RHEL','SUSE','Windows', 'Oracle SE1 - LI', 'Oracle SE1 - BYOL','PostgreSQL','SQL Server SE - LI','SQL Server SE - BYOL','SQL Server EX - LI','SQL Server EX - BYOL','SQL Server Web - LI','SQL Server Web - BYOL','SQL Std','SQL Web','EMR','Cache','Redshift','DynamoDB']
#we need to flag multi-az instances for correct RDS pricing. we also need to flag dedicated Ec2 instances
MultiDedicated_types = ['Multi-AZ','Dedicated']
#we need to define regions as we price by region not AZ
Region_types = ['us-east-1','us-west-2','eu-west-1','eu-central-1','us-west-1','ap-northeast-1','ap-southeast-1','ap-southeast-2','sa-east-1']


start_date = date(2013,1,1)

# Returns instance type from the ItemDescription or usagetype field
def get_instance_type(description):
	for instance_type in instance_types:
		if description.find(instance_type) >= 0:
			return instance_type
	return None

#Returns operating system from ItemDescription field
def get_OS_type(description):
	for OS_type in OS_types:
		if description.find(OS_type) >= 0:
			return OS_type
	return None

#Returns Multi-AZ from ItemDescription or usagetype field
def get_MultiDedicated_type(description):
	for MultiDedicated_type in MultiDedicated_types:
		if description.find(MultiDedicated_type) >= 0:
			return MultiDedicated_type
	return None

#Get a Region from the AZ field as pricing is Region based, not AZ based

def get_Region_type(description):
	for Region_type in Region_types:
		if description.find(Region_type) >= 0:
			return Region_type
	return None

# Transforms the row according to the needed format for RedShift loading
def transform_row(values):
	# strip out quotation marks and commas from values and change some of the item descriptions so we can pick up instance types / os etc
	result = []
	i = 0
	for value in values:
		# strip out commas
		value = re.sub(',', '', value)
		# change 'Redis' to Redis Cache so it picks up as an elasticache OS
		value = re.sub('Redis', 'Redis Cache',value)
		# Cater for Windows BYOL
		value = re.sub('Windows BYOL', 'Win BYOL ba Linux',value)
		# Pick up the region for Spot instances
		value = re.sub('Sydney', 'ap-southeast-2',value)
		value = re.sub('Singapore', 'ap-southeast-1',value)
		value = re.sub('Frankfurt', 'eu-central-1',value)
		value = re.sub('Dublin', 'eu-west-1',value)
		value = re.sub('Virginia', 'us-east-1',value)
		value = re.sub('Oregon', 'us-west-2',value)
		value = re.sub('California', 'us-west-1',value)
		value = re.sub('Sao Paulo', 'sa-east-1',value)
		value = re.sub('Beijing', 'cn-north-1',value)
		value = re.sub('GovCloud', 'us-gov-west-1',value)
		# change 'Red Hat Enterprise Linux' to RHEL so it isn't confused with Amazon Linux
		value = re.sub('Red Hat Enterprise Linux', 'RHEL',value)
		# change '(License Included)' to -LI so RDS SQL licensing is picked up consistently
		value = re.sub("\(License Included\)", '- LI',value)
		# change EC2 SQL item descriptions to be consistent. Note RDS has SQL Server Standard - LI, EC2 has SQL Server Standard (Amazon VPC) / Windows with SQL Std
		value = re.sub('Windows with SQL Server Standard', 'SQL Std',value)
		value = re.sub('Windows with SQL Server Standard', 'SQL Std',value)
		value = re.sub('SQL Serve Web - License Included', 'SQL Server Web - LI',value)
		value = re.sub('SQL Server Express', 'SQL Server EX',value)
		value = re.sub('SQL Serve EX', 'SQL Server EX',value)
		value = re.sub('Windows with SQL Server Web', 'SQL Web',value)
		value = re.sub('Windows with SQL Web', 'SQL Web',value)
		value = re.sub('Windows with SQL Std', 'SQL Std',value)
		#change Dynamo read / write to instance type format
		value = re.sub('units of read capacity', 'dynamodb.read',value)
		value = re.sub('units of write capacity', 'dynamodb.write',value)
		value = re.sub('Reserved Read Capacity', 'dynamodb.read',value)
		value = re.sub('Reserved Write Capacity', 'dynamodb.write',value)
		# change Redshift item descriptions to be consistent.
		value = re.sub('dw\.hs1\.xlarge','dw1.xlarge',value)
		value = re.sub('dw\.hs1\.8xlarge','dw1.8xlarge',value)
		value = re.sub('dc1\.xlarge','dw2.xlarge',value) #Redshift changed naming conventions in Jun '15
		value = re.sub('dc1\.8xlarge','dw2.8xlarge',value) #Redshift changed naming conventions in Jun '15
		value = re.sub('ds1\.xlarge','dw1.xlarge',value) #Redshift changed naming conventions in Jun '15
		value = re.sub('ds1\.8xlarge','dw1.8xlarge',value) #Redshift changed naming conventions in Jun '15
		value = re.sub("\(DW1.XL\)",'dw1.xlarge',value) 
		value = re.sub("\(DW1.8XL\)",'dw1.8xlarge',value) #not sure if this exists, just in case
		#change dates to Redshift friendly format
		if i == 14 or i == 15:
			value = re.sub('/','-',value)
		# add new values
		result.append(value)
		i += 1
	values = result
	
	#if this is a single account (not consolidated billing) it won't have blended / unblended rates, we'll add in two columns to standardize format
	
	#values.insert(19,values[17])
	#values.insert(20,values[18])
	
	
	# populate a new instance type field
	instance_type = get_instance_type(values[9])
	if instance_type != None:	
		values.insert(16,instance_type)
	else:
		instance_type = get_instance_type(values[13])
		if instance_type != None:
			values.insert(16,instance_type)
		else:
			values.insert(16,'')
		
	# populate a new OS field
	OS_type = get_OS_type(values[13])
	if OS_type != None:
		values.insert(17,OS_type)
	else: 
		OS_type = get_OS_type(values[5]) #For Redshift and Dynamo we get the OS from the Productname field
		if OS_type != None:
			values.insert(17,OS_type)
		else:
			values.insert(17,'')
	
	# Change 'EMR' os to Linux 
	result = []
	i = 0
	for value in values:
		# strip out commas
		value = re.sub(',', '', value)
		if i == 17:
			value = re.sub('EMR','Linux',value)
		# add new values
		result.append(value)
		i += 1
	values = result
	
	# populate a new field that indicated dedicated EC2 instances or Multi-AZ RDS instances
	MultiDedicated_type = get_MultiDedicated_type(values[9])
	if MultiDedicated_type != None:
		values.insert(18,MultiDedicated_type)
	else: 
		MultiDedicated_type = get_MultiDedicated_type(values[13])
		
		if MultiDedicated_type != None:
			values.insert(18,MultiDedicated_type)
		else:	
			values.insert(18,'Shared')
	
	# populate a new field that indicates the Region (not AZ)
	
	Region_type = get_Region_type(values[11])
	if Region_type != None:
		values.insert(19,Region_type)
	else: 
		Region_type = get_Region_type(values[13])
		
		if Region_type != None:
			values.insert(19,Region_type)
	
		else: 
			values.insert(19,'')

	
	# check reserved instances field
	if values[12] == 'Y':
		values[12] = '1'
	else:
		values[12] = '0'
	
	# if recordid is blank, input a placeholder
	if values[4] is None:
		values[4] = '1234567890'
		
	# remove the line item field
	values.pop(3)

	return values

def main(argv):
	for line in reader(sys.stdin):
		try:
			if line[3] == 'LineItem':
				# transform row to correct format
				line = transform_row(line)
				# output values in csv format
				print(','.join(line).rstrip())
		except ValueError as e:
			sys.stderr.write("%s\n" % (e))

if __name__ == "__main__":
	main(sys.argv)

  
