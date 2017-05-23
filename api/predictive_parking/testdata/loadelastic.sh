# load database into elastic search.

set -e
set -u


dc() {
   docker-compose $*;
}

dc up -d elasticsearch

while ! nc -z elasticsearch 9200
do
 	echo "Waiting for elastic..."
 	sleep 1.5
done

curl -s -v -f -XPUT http://elasticsearch:9200/_template/scan -d '
{
  "template": "scans-*",
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "scan": {
      "properties": {
        "geo": {
          "type": "geo_point"
        }
      }
    }
  }
}'

dc run -e "DB=test_predictiveparking" -e "TABLE=metingen_scan" --rm logstash logstash -f readdb.conf
