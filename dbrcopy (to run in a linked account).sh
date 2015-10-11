#rename to dbrcopy.sh to match datapipeline template
#apply all updates
sudo yum update aws-cli -y
sudo mkdir /media/ephemeral0/DBR/
sudo chmod 777 /media/ephemeral0/DBR/
 cd /media/ephemeral0/DBR/
#Retrieve access keys from AWS 
sudo aws sts assume-role --role-arn arn:aws:iam::example --role-session-name DBRdownload >temp-creds.txt
#retrieve the keys from the temp-creds file
sudo awk '/SecretAccessKey/ {gsub(/",/,"",$2);gsub(/"/,"",$2); print $2}' temp-creds.txt >secretaccesskey.txt
sudo awk '/AccessKeyId/ {gsub(/",/,"",$2);gsub(/"/,"",$2); print $2}' temp-creds.txt >accesskeyid.txt
sudo awk '/SessionToken/ {gsub(/",/,"",$2);gsub(/"/,"",$2); print $2}' temp-creds.txt >sessiontoken.txt
# insert keys into a new profile called temp-creds
aws configure set aws_access_key_id file://accesskeyid.txt --profile temp-creds
aws configure set aws_secret_access_key file://secretaccesskey.txt --profile temp-creds
aws configure set aws_session_token file://sessiontoken.txt --profile temp-creds
#copy DBRs
aws s3 cp s3://billingbucket/ . --exclude "*" --include "*resources-and-tags-2015-09*" --recursive --region ap-southeast-2 --profile temp-creds
zcat *resources* | split -l 1000000 -  dbr.gz.part
rm –f *tags*
gzip dbr.gz.part*
#remove the old files
aws s3 rm s3://storagebucket/Datapipeline/DBR/ --recursive --region ap-southeast-2
aws s3 rm s3://storagebucket/Datapipeline/DBRafterEMR/ --recursive --region ap-southeast-2
#upload the files to the s3 staging bucket
aws s3 cp . s3://storagebucket/Datapipeline/DBR/ --exclude "*" --include "*dbr*" --recursive --region ap-southeast-2
