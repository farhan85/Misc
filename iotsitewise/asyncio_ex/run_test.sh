#!/usr/bin/env bash

DB=
MODEL_NAME=
ASSET_NAME=
ASSET_COUNT=

while getopts ':d:n:p:h' OPT; do
    case "$OPT" in
        d) DB="$OPTARG" ;;
        n) ASSET_COUNT="$OPTARG" ;;
        p) MODEL_NAME="$OPTARG"
           ASSET_NAME="${MODEL_NAME}-asset" ;;
        h) echo "Usage: $(basename $0) -p <resource name prefix> -n <num Assets> -d <db filename> [-h]"
           exit 0 ;;
        ?) echo "Invalid option: -$OPTARG" ; exit 2 ;;
    esac
done
shift $((OPTIND - 1))

if [[ -z "$DB" || -z "$MODEL_NAME" || -z "$ASSET_NAME" || -z "$ASSET_COUNT" ]]; then
    echo "Missing args"
    exit 1
fi

set -e

echo '{}' > $DB

echo "Creating AssetModel"
./1_create_asset_model.py --asset-model-name "$MODEL_NAME" --db-filename "$DB"

echo "Creating Assets"
./2_create_assets.py --asset-name-prefix "$ASSET_NAME" --num-assets $ASSET_COUNT --db-filename "$DB"

echo "Created all Assets. Wait 10s before deleting them"
sleep 10

echo "Deleting Assets"
./3_delete_assets.py --db-filename "$DB"

echo "Deleting AssetModel"
./4_delete_asset_model.py --db-filename "$DB"
