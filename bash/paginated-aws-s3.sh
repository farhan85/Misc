#!/usr/bin/env bash

S3_BUCKET='...'
KEY_PREFIX='...'


function get-s3-keys() {
    local starting_token="$1"
    cmd=(aws s3api list-objects-v2
            --bucket $S3_BUCKET
            --max-items 500
            --prefix $KEY_PREFIX
            --query '{NextToken: NextToken, Keys: Contents[].Key}')
    if [[ -n "$starting_token" ]]; then
        cmd+=( --starting-token $starting_token )
    fi
    echo >&2 "Starting token: $starting_token"
    "${cmd[@]}"
}


output=$(get-s3-keys)
while true ; do
    next_token=$(echo "$output" | jq --raw-output '. | .NextToken')
    all_keys=( $(echo "$output" | jq --raw-output '. | .Keys[]') )
    for key in "${all_keys[@]}"; do
        echo $key
    done

    if [[ "$next_token" == "null" ]]; then
        break
    fi
    output=$(get-s3-keys $next_token)
done
