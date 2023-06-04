: 'The Outline management URL is by default stored in management_api.url.
   The Outline management URL has the form https://IPv4:port/Base64_string. You
   can find it on the Settings tab of your server in Outline Manager software.
   Outline readme can be viewed in the following link. It shows the commands
   used here.
   https://github.com/Jigsaw-Code/outline-server/blob/master/src/shadowbox/README.md'
read -r API_URL < management_api.url
id=0
first=1
created_keys=0
# By default, the contacts are stored in contacts.csv.
# fname, lname, and email are First Name, Last Name, and E-mail, respectively.
# TODO: An argument could be used to denote the number contacts to be created instead of using an input file.
contacts_file="contacts.csv"
access_keys="access_keys.json"
output_file="outline_keys.csv"
echo "Output file: $output_file"

# Parse and validate arguments
while getopts "u:c" OPT; do
    case $OPT in
    u)
        API_URL="$OPTARG"
        ;;
    c)
        contacts_file="$OPTARG"
        ;;
# TODO: The -o option does not work. Fix it.
#    o)
#        output_file="$OPTARG"
#        ;;
#    a)
#        ACCUMULATE="y"
#        ;;
#    H)
#        HEADER="y"
#        ;;
# TODO: Implement the usage function.
    h)
        usage
        exit 0
        ;;
    *)
        usage
        exit 1
        ;;
    esac
done
echo "Output file: $output_file, $API_URL"

# TODO: Delete this key that is not going to be used.
curl --insecure -X POST $API_URL/access-keys
while IFS=, read -r fname lname email the_rest
do
	# Skipping the first row of the contacts because it is the titles.
	if [ $first == 0 ]; then	
		# Getting the ID of the last access key created.
		if [ $id == 0 ]; then	
			curl --insecure $API_URL/access-keys/ > $access_keys
			id=`jq '.accessKeys | .[-1].id' $access_keys`
			# TODO: If all the keys have been deleted, this part will return ul instead of a number. Therefore the key names will not correspond to the key email. One way to get around this issue is to create a key and then delete it at the end.
			# This issue happens when the last key has been removed, too. Creating a key and removing it at the end solves this issue, as well.
			id=${id:1:-1}
			echo $id
			#if [ $id is not number ]; then
			#	curl --insecure -X POST $API_URL/access-keys
			#	id=0
			#	continue
			#fi
			first_id=$id
			echo "first_id=$first_id"
		fi
		echo "ID: $id"
		# Creating an access key
		access_key_name="$fname $lname"
		if [ "$access_key_name" = " " ]; then	
			access_key_name="$email"
		fi
		echo "Acces Key Name: $access_key_name"
		# TODO: Set port number to 443
		curl --insecure -X POST $API_URL/access-keys
		id=$(($id+1))
		# Renaming the access key
		curl --insecure -X PUT -F "name=$access_key_name" $API_URL/access-keys/$id/name
		#exit
		created_keys=$(($created_keys+1))
	fi
	first=0
done < $contacts_file
# TODO: Set a data limit on the access keys.
# Outline readme suggests using the following command, but it does not work.
curl -v --insecure -X PUT -H "Content-Type: application/json" -d '{"limit": {"bytes": 100000000}}' $API_URL/experimental/access-key-data-limit
curl --insecure $API_URL/access-keys/ > $access_keys
echo "KeyName,AccessKey" > all_keys.csv
jq -r '.accessKeys[] | [.name,.accessUrl] | @csv' access_keys.json >> all_keys.csv
echo "id: $id, first_id: $first_id, created_keys: $created_keys"
lines=$(wc -l all_keys.csv | awk '{print $1}')
echo "$lines"
range="2,$((lines-id+first_id))d"
echo "$range"
sed $range all_keys.csv > access_keys.csv
echo "A total of $((id-first_id)) access keys created and stored in $access_keys."
paste -d ',' access_keys.csv contacts.csv > $output_file
echo "You can now see the generated access keys on the Outline Manager software in addition to the file $output_file."
