# Loads AWS credentials from the founder's key CSV into THIS shell only. Never echoes them.
# Usage: source tools/aws/aws_env.sh   (then aws ... ; credentials vanish when the shell exits)
_KEYCSV="${AWS_KEY_CSV:-/Users/aditya/CODING/AWS/linux/rootkey.csv}"
export AWS_ACCESS_KEY_ID="$(awk -F, 'NR==2{gsub(/\r/,"");print $1}' "$_KEYCSV")"
export AWS_SECRET_ACCESS_KEY="$(awk -F, 'NR==2{gsub(/\r/,"");print $2}' "$_KEYCSV")"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-ap-south-1}"
export AWS_PAGER=""
export AWS_CONFIG_FILE="/Volumes/Aditya ssd/Salt-Battery-Lab/tools/aws/config"
export AWS_SHARED_CREDENTIALS_FILE="/Volumes/Aditya ssd/Salt-Battery-Lab/tools/aws/credentials_unused"
unset _KEYCSV
